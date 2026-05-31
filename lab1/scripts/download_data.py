#!/usr/bin/env python3
"""Download public data for the Germany grid bottleneck model."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_data"

NETWORK_FILES = {
    "highvoltage_vertices.csv": (
        "https://raw.githubusercontent.com/ComplexNetTSP/Power_grids/master/"
        "Countries/Germany/Nodes/highvoltage_vertices.csv"
    ),
    "highvoltage_links.csv": (
        "https://raw.githubusercontent.com/ComplexNetTSP/Power_grids/master/"
        "Countries/Germany/Edges/highvoltage_links.csv"
    ),
}

ENERGY_CHARTS = {
    "openapi.json": "https://api.energy-charts.info/openapi.json",
    "public_power_de_latest.json": "https://api.energy-charts.info/public_power?country=de",
    "total_power_de_latest.json": "https://api.energy-charts.info/total_power?country=de",
    "installed_power_de.json": "https://api.energy-charts.info/installed_power?country=de",
    "public_power_forecast_de_latest.json": (
        "https://api.energy-charts.info/public_power_forecast?country=de"
    ),
}

SMARD_FILTERS = {
    "1223": "lignite",
    "1225": "wind_offshore",
    "4067": "wind_onshore",
    "4068": "solar",
    "4069": "hard_coal",
    "4071": "gas",
    "410": "load",
    "4359": "residual_load",
}

SMARD_REGIONS = ["DE", "50Hertz", "Amprion", "TenneT", "TransnetBW"]


def fetch(url: str) -> bytes:
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content


def save_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def download_network(sources: list[dict]) -> None:
    for filename, url in NETWORK_FILES.items():
        target = RAW / "network" / filename
        save_bytes(target, fetch(url))
        sources.append(
            {
                "dataset": "Germany high-voltage grid topology",
                "file": str(target.relative_to(ROOT)),
                "source": url,
                "provider": "ComplexNetTSP Power_grids / OSM-derived SciGRID-style data",
                "notes": "OpenStreetMap-derived approximation, not an official TSO grid model.",
            }
        )


def download_energy_charts(sources: list[dict]) -> None:
    for filename, url in ENERGY_CHARTS.items():
        target = RAW / "energy_charts" / filename
        try:
            data = fetch(url)
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 429 and target.exists():
                data = target.read_bytes()
            elif filename.startswith("public_power_forecast"):
                continue
            else:
                raise
        save_bytes(target, data)
        sources.append(
            {
                "dataset": "Energy-Charts Germany electricity data",
                "file": str(target.relative_to(ROOT)),
                "source": url,
                "provider": "Fraunhofer ISE Energy-Charts API",
                "notes": "Latest public generation/load snapshots and installed capacity.",
            }
        )


def latest_smard_timestamp(filter_id: str, region: str) -> int | None:
    region_q = quote(region, safe="")
    url = f"https://www.smard.de/app/chart_data/{filter_id}/{region_q}/index_hour.json"
    response = requests.get(url, timeout=12)
    if response.status_code != 200 or "json" not in response.headers.get("content-type", ""):
        return None
    try:
        timestamps = response.json().get("timestamps", [])
    except ValueError:
        return None
    return timestamps[-1] if timestamps else None


def download_smard(sources: list[dict]) -> None:
    for region in SMARD_REGIONS:
        for filter_id, name in SMARD_FILTERS.items():
            stamp = latest_smard_timestamp(filter_id, region)
            if stamp is None:
                continue
            region_q = quote(region, safe="")
            url = (
                f"https://www.smard.de/app/chart_data/{filter_id}/{region_q}/"
                f"{filter_id}_{region_q}_hour_{stamp}.json"
            )
            target = RAW / "smard" / f"{region}_{name}_{filter_id}_{stamp}.json"
            try:
                data = target.read_bytes() if target.exists() else fetch(url)
                save_bytes(target, data)
            except requests.RequestException:
                continue
            sources.append(
                {
                    "dataset": f"SMARD hourly {name} for {region}",
                    "file": str(target.relative_to(ROOT)),
                    "source": url,
                    "provider": "Bundesnetzagentur | SMARD.de",
                    "notes": "Latest available weekly hourly file at download time.",
                }
            )


def catalog_existing_smard(sources: list[dict]) -> None:
    known = {item["file"] for item in sources}
    for target in sorted((RAW / "smard").glob("*.json")):
        rel = str(target.relative_to(ROOT))
        if rel in known:
            continue
        parts = target.stem.split("_")
        if len(parts) < 4:
            continue
        region = parts[0]
        filter_id = parts[-2]
        name = "_".join(parts[1:-2])
        region_q = quote(region, safe="")
        stamp = target.stem.rsplit("_", 1)[-1]
        sources.append(
            {
                "dataset": f"SMARD hourly {name} for {region}",
                "file": rel,
                "source": (
                    f"https://www.smard.de/app/chart_data/{filter_id}/{region_q}/"
                    f"{filter_id}_{region_q}_hour_{stamp}.json"
                ),
                "provider": "Bundesnetzagentur | SMARD.de",
                "notes": "Previously downloaded latest weekly hourly file.",
            }
        )


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    sources: list[dict] = []
    download_network(sources)
    download_energy_charts(sources)
    download_smard(sources)
    catalog_existing_smard(sources)
    catalog = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": sources,
    }
    (RAW / "source_catalog.json").write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Downloaded {len(sources)} files into {RAW}")


if __name__ == "__main__":
    main()
