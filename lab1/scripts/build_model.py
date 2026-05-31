#!/usr/bin/env python3
"""Build an open-data Germany grid bottleneck model."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import networkx as nx
from scipy import sparse
from scipy.sparse import linalg

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_data"
OUT = ROOT / "processed"
WEB = ROOT / "web"

TYPE_MAP = {
    "Wind offshore": "wind_offshore",
    "Wind onshore": "wind_onshore",
    "Solar": "solar",
    "Biomass": "biomass",
    "Fossil brown coal / lignite": "lignite",
    "Fossil hard coal": "hard_coal",
    "Fossil gas": "gas",
    "Fossil oil": "oil",
    "Hydro Run-of-River": "hydro",
    "Hydro water reservoir": "hydro",
    "Hydro pumped storage": "pumped_storage",
    "Waste": "waste",
    "Others": "other",
}


def load_public_power() -> tuple[pd.Timestamp, dict[str, float]]:
    data = json.loads((RAW / "energy_charts" / "public_power_de_latest.json").read_text())
    times = pd.to_datetime(data["unix_seconds"], unit="s", utc=True)
    frame = pd.DataFrame({p["name"]: p["data"] for p in data["production_types"]}, index=times)
    row = frame[frame["Load"].notna()].dropna(how="all").iloc[-1]
    values = {TYPE_MAP[k]: float(row.get(k, 0) or 0) for k in TYPE_MAP}
    values["load"] = float(row.get("Load", row[list(TYPE_MAP)].sum()))
    return row.name, values


def read_grid() -> tuple[pd.DataFrame, pd.DataFrame]:
    buses = pd.read_csv(RAW / "network" / "highvoltage_vertices.csv", sep="#")
    lines = pd.read_csv(RAW / "network" / "highvoltage_links.csv", sep="#")
    buses = buses.rename(columns={"v_id": "bus_id", "lon": "x", "lat": "y"})
    lines = lines.rename(columns={"l_id": "line_id", "v_id_1": "bus0", "v_id_2": "bus1"})
    buses = buses.dropna(subset=["bus_id", "x", "y"]).copy()
    lines = lines[lines["bus0"].isin(buses.bus_id) & lines["bus1"].isin(buses.bus_id)].copy()
    graph = nx.from_pandas_edgelist(lines, "bus0", "bus1")
    largest = max(nx.connected_components(graph), key=len)
    buses = buses[buses.bus_id.isin(largest)].copy()
    lines = lines[lines["bus0"].isin(largest) & lines["bus1"].isin(largest)].copy()
    buses["region"] = [assign_region(x, y) for x, y in zip(buses.x, buses.y)]
    return buses.reset_index(drop=True), lines.reset_index(drop=True)


def assign_region(x: float, y: float) -> str:
    if y < 49.3 and x < 10.7:
        return "TransnetBW"
    if x < 8.8 and 49.0 <= y <= 53.8:
        return "Amprion"
    if x > 11.1 or (y > 53.0 and x > 9.8):
        return "50Hertz"
    return "TenneT"


def spatial_weights(buses: pd.DataFrame, kind: str) -> pd.Series:
    x = buses.x.astype(float)
    y = buses.y.astype(float)
    if kind == "load":
        w = 0.25 + np.exp(-((x - 7.2) ** 2 / 3.5 + (y - 51.4) ** 2 / 2.0))
        w += 0.7 * np.exp(-((x - 11.6) ** 2 / 5.0 + (y - 48.7) ** 2 / 1.8))
    elif kind == "wind_onshore":
        w = 0.2 + 1.7 * (y - y.min()) / (y.max() - y.min()) + 0.6 * (x > 10)
    elif kind == "wind_offshore":
        w = np.exp(-((y - 53.8) ** 2 / 0.45 + (x - 8.5) ** 2 / 9.0))
    elif kind == "solar":
        w = 0.2 + 1.4 * (y.max() - y) / (y.max() - y.min()) + 0.3 * (x > 10)
    elif kind in {"lignite", "hard_coal"}:
        w = np.exp(-((x - 6.7) ** 2 / 1.0 + (y - 51.0) ** 2 / 1.0))
        w += np.exp(-((x - 14.2) ** 2 / 1.2 + (y - 51.6) ** 2 / 0.8))
    elif kind in {"hydro", "pumped_storage"}:
        w = 0.1 + 2.0 * (y.max() - y) / (y.max() - y.min())
    else:
        w = pd.Series(1.0, index=buses.index)
    w = pd.Series(w, index=buses.index).clip(lower=0.0001)
    return w / w.sum()


def injection_vector(buses: pd.DataFrame, power: dict[str, float]) -> pd.Series:
    injections = pd.Series(0.0, index=buses.index)
    for kind, value in power.items():
        if kind == "load":
            continue
        injections += max(value, 0.0) * spatial_weights(buses, kind)
    injections -= power["load"] * spatial_weights(buses, "load")
    imbalance = injections.sum()
    border = buses[(buses.x < 6.6) | (buses.x > 13.7) | (buses.y > 53.5) | (buses.y < 48.2)]
    target = border.index if len(border) else buses.index
    injections.loc[target] -= imbalance / len(target)
    return injections


def numeric_parts(value: object) -> list[float]:
    if pd.isna(value):
        return []
    parts = []
    for raw in str(value).replace(",", ".").split(";"):
        try:
            parts.append(float(raw))
        except ValueError:
            continue
    return parts


def electrical_lines(lines: pd.DataFrame) -> pd.DataFrame:
    lines = lines.copy()
    voltage_parts = lines["voltage"].apply(numeric_parts)
    lines["parallel_circuits"] = voltage_parts.apply(lambda values: max(1, min(len(values), 8)))
    lines["voltage_kv"] = voltage_parts.apply(lambda values: max(values) if values else 220000) / 1000
    lines["length_km"] = pd.to_numeric(lines["length_m"], errors="coerce").fillna(10000) / 1000
    x = lines["x_ohmkm"].apply(lambda value: (numeric_parts(value) or [0.32])[0])
    lines["x_ohm"] = x * lines["length_km"].clip(lower=0.5) / lines["parallel_circuits"]
    amps = lines["i_th_max_a"].apply(lambda value: max(numeric_parts(value) or [np.nan]))
    fallback = np.where(lines["voltage_kv"] >= 350, 2500, 1300)
    amps = amps.fillna(pd.Series(fallback, index=lines.index))
    lines["capacity_mw"] = (
        math.sqrt(3) * lines["voltage_kv"] * amps * lines["parallel_circuits"] / 1000
    ).clip(200, 8000)
    lines["susceptance"] = (lines["voltage_kv"] ** 2 / lines["x_ohm"]).clip(1, 100000)
    return lines


def solve_dc(buses: pd.DataFrame, lines: pd.DataFrame, injections: pd.Series) -> np.ndarray:
    bus_index = {int(bus): i for i, bus in enumerate(buses.bus_id)}
    rows, cols, data = [], [], []
    for _, line in lines.iterrows():
        i, j = bus_index[int(line.bus0)], bus_index[int(line.bus1)]
        b = float(line.susceptance)
        rows += [i, i, j, j]
        cols += [i, j, i, j]
        data += [b, -b, -b, b]
    matrix = sparse.coo_matrix((data, (rows, cols)), shape=(len(buses), len(buses))).tocsr()
    keep = np.arange(1, len(buses))
    theta = np.zeros(len(buses))
    theta[keep] = linalg.spsolve(matrix[keep][:, keep], injections.iloc[keep].values)
    return theta


def score_lines(buses: pd.DataFrame, lines: pd.DataFrame, theta: np.ndarray) -> pd.DataFrame:
    bus_index = {int(bus): i for i, bus in enumerate(buses.bus_id)}
    flows = []
    for _, line in lines.iterrows():
        i, j = bus_index[int(line.bus0)], bus_index[int(line.bus1)]
        flow = (theta[i] - theta[j]) * float(line.susceptance)
        flows.append(flow)
    result = lines.copy()
    result["flow_mw"] = flows
    result["abs_flow_mw"] = np.abs(result.flow_mw)
    result["utilization_pct"] = 100 * result.abs_flow_mw / result.capacity_mw
    result["severity"] = pd.cut(
        result.utilization_pct, [-1, 60, 80, 100, 9999], labels=["normal", "watch", "tight", "overload"]
    ).astype(str)
    result["bottleneck_score"] = result.utilization_pct * np.log1p(result.length_km)
    return result.sort_values("bottleneck_score", ascending=False)


def export_web_data(buses: pd.DataFrame, scored: pd.DataFrame, summary: dict) -> None:
    top = scored.head(120)
    bus_lookup = buses.set_index("bus_id")[["x", "y", "region"]].to_dict("index")
    web_lines = []
    for _, line in top.iterrows():
        b0, b1 = bus_lookup.get(line.bus0), bus_lookup.get(line.bus1)
        if not b0 or not b1:
            continue
        web_lines.append(
            {
                "id": int(line.line_id),
                "from": [b0["x"], b0["y"]],
                "to": [b1["x"], b1["y"]],
                "regions": [b0["region"], b1["region"]],
                "flow_mw": round(float(line.flow_mw), 1),
                "capacity_mw": round(float(line.capacity_mw), 1),
                "utilization_pct": round(float(line.utilization_pct), 1),
                "severity": line.severity,
                "length_km": round(float(line.length_km), 1),
            }
        )
    payload = {"summary": summary, "lines": web_lines}
    (WEB / "data.js").write_text(
        "window.GRID_BOTTLENECK_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    WEB.mkdir(parents=True, exist_ok=True)
    timestamp, power = load_public_power()
    buses, raw_lines = read_grid()
    lines = electrical_lines(raw_lines)
    injections = injection_vector(buses, power)
    theta = solve_dc(buses, lines, injections)
    scored = score_lines(buses, lines, theta)
    buses.assign(injection_mw=injections.values).to_csv(OUT / "bus_injections.csv", index=False)
    scored.to_csv(OUT / "line_bottlenecks.csv", index=False)
    summary = {
        "model_timestamp_utc": timestamp.isoformat(),
        "load_mw": round(power["load"], 1),
        "generation_mw": round(sum(v for k, v in power.items() if k != "load" and v > 0), 1),
        "line_count": int(len(scored)),
        "bus_count": int(len(buses)),
        "overloaded_lines": int((scored.utilization_pct >= 100).sum()),
        "watch_lines": int((scored.utilization_pct >= 80).sum()),
        "top_bottleneck_line": int(scored.iloc[0].line_id),
        "top_bottleneck_utilization_pct": round(float(scored.iloc[0].utilization_pct), 1),
        "method": "Open-data spatial dispatch plus DC load-flow on Germany high-voltage topology.",
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    export_web_data(buses, scored, summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
