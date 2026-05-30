from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass


class DeployError(RuntimeError):
    """Raised when the Render deploy workflow cannot continue safely."""


@dataclass(frozen=True)
class ServiceTarget:
    name: str
    service_id: str
    url: str


DEFAULT_API_NAME = "loom-api-free"
DEFAULT_WEB_NAME = "loom-web"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deploy the Loom Render API and web services.")
    parser.add_argument("--commit", help="Commit SHA to deploy. Defaults to HEAD.")
    parser.add_argument("--api-service", default=DEFAULT_API_NAME)
    parser.add_argument("--web-service", default=DEFAULT_WEB_NAME)
    parser.add_argument("--web-only", action="store_true")
    parser.add_argument("--api-only", action="store_true")
    parser.add_argument("--skip-validate", action="store_true")
    parser.add_argument("--skip-verify", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--skip-remote-check", action="store_true")
    return parser.parse_args(argv)


def run(cmd: list[str], *, capture: bool = False) -> str:
    print("+", " ".join(cmd), flush=True)
    completed = subprocess.run(cmd, check=True, text=True, capture_output=capture)
    return completed.stdout if capture else ""


def git_output(*args: str) -> str:
    return run(["git", *args], capture=True).strip()


def ensure_clean_worktree(allow_dirty: bool) -> None:
    if allow_dirty:
        return
    status = git_output("status", "--short")
    if status:
        raise DeployError("Working tree is not clean. Commit or stash changes before deploying.")


def resolve_commit(explicit_commit: str | None) -> tuple[str, str]:
    branch = git_output("branch", "--show-current")
    if not branch:
        raise DeployError("Could not determine the current git branch.")
    commit = explicit_commit or git_output("rev-parse", "HEAD")
    return branch, commit


def ensure_remote_commit(branch: str, commit: str, skip_remote_check: bool) -> None:
    if skip_remote_check:
        return
    remote_commit = git_output("rev-parse", f"origin/{branch}")
    if remote_commit != commit:
        raise DeployError(
            f"Commit {commit} is not the current origin/{branch} tip. Push first or pass --skip-remote-check."
        )


def read_services() -> list[dict]:
    output = run(["render", "services", "-o", "json", "--confirm"], capture=True)
    data = json.loads(output)
    if not isinstance(data, list):
        raise DeployError("Unexpected Render services payload.")
    return data


def find_service(services: list[dict], name: str) -> ServiceTarget:
    for item in services:
        service = item.get("service")
        if not isinstance(service, dict) or service.get("name") != name:
            continue
        details = service.get("serviceDetails", {})
        url = details.get("url", "")
        if not service.get("id") or not url:
            raise DeployError(f"Render service {name} is missing an id or url.")
        return ServiceTarget(name=name, service_id=service["id"], url=url)
    raise DeployError(f"Could not find Render service named {name}.")


def deploy_service(target: ServiceTarget, commit: str) -> dict:
    output = run(
        [
            "render",
            "deploys",
            "create",
            target.service_id,
            "--commit",
            commit,
            "--wait",
            "--confirm",
            "-o",
            "json",
        ],
        capture=True,
    )
    data = json.loads(output)
    if data.get("status") != "live":
        raise DeployError(f"Deploy for {target.name} finished with status {data.get('status')}.")
    return data


def verify_api(url: str) -> None:
    output = run(["curl", "-fsS", f"{url}/health"], capture=True).strip()
    data = json.loads(output)
    if data.get("ok") is not True:
        raise DeployError(f"Unexpected API health response: {output}")


def verify_web(url: str) -> None:
    run(["curl", "-I", url])


def selected_targets(args: argparse.Namespace, services: list[dict]) -> list[ServiceTarget]:
    if args.web_only and args.api_only:
        raise DeployError("Use only one of --web-only or --api-only.")
    targets: list[ServiceTarget] = []
    if not args.web_only:
        targets.append(find_service(services, args.api_service))
    if not args.api_only:
        targets.append(find_service(services, args.web_service))
    return targets


def maybe_validate(skip_validate: bool) -> None:
    if not skip_validate:
        run(["render", "blueprints", "validate"])


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        ensure_clean_worktree(args.allow_dirty)
        branch, commit = resolve_commit(args.commit)
        ensure_remote_commit(branch, commit, args.skip_remote_check)
        maybe_validate(args.skip_validate)
        services = read_services()
        targets = selected_targets(args, services)
        for target in targets:
            deploy_service(target, commit)
        if not args.skip_verify:
            for target in targets:
                if target.name == args.api_service:
                    verify_api(target.url)
                else:
                    verify_web(target.url)
        print(f"Deployed commit {commit} from branch {branch}.", flush=True)
        for target in targets:
            print(f"- {target.name}: {target.url}", flush=True)
    except (DeployError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"Deploy failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
