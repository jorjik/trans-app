"""Coolify deploy helper for TransApp.

Credentials come from the environment (never commit them):
    COOLIFY_URL        e.g. https://jenya.website
    COOLIFY_API_TOKEN  Coolify → Settings → API → Create Token

Usage:
    python scripts/coolify.py status
    python scripts/coolify.py envs
    python scripts/coolify.py set KEY=value [KEY2=value2 ...]
    python scripts/coolify.py domain miniapp https://transapp777.xyz
    python scripts/coolify.py deploy
    python scripts/coolify.py logs [deployment_uuid] [n_lines]
    python scripts/coolify.py dedupe        # remove duplicate env rows
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from collections import Counter, defaultdict

APP_UUID = os.environ.get("COOLIFY_APP_UUID", "tpnridaztlzcfcyfmcipqdlq")
BASE = os.environ.get("COOLIFY_URL", "").rstrip("/") + "/api/v1"
TOKEN = os.environ.get("COOLIFY_API_TOKEN", "")

if not TOKEN or BASE == "/api/v1":
    sys.exit("Set COOLIFY_URL and COOLIFY_API_TOKEN environment variables first.")


def req(method: str, path: str, data: dict | None = None):
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=120) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:800]


def app() -> dict:
    _, a = req("GET", f"/applications/{APP_UUID}")
    return a.get("data", a) if isinstance(a, dict) else {}


def cmd_status() -> None:
    a = app()
    print("name:      ", a.get("name"))
    print("status:    ", a.get("status"))
    print("build_pack:", a.get("build_pack"), "|", a.get("docker_compose_location"))
    print("domains:   ", a.get("docker_compose_domains"))


def cmd_envs() -> None:
    _, envs = req("GET", f"/applications/{APP_UUID}/envs")
    for e in sorted(envs, key=lambda x: x["key"]):
        print(f"{e['key']:28} = {(e.get('value') or '')[:70]}")


def cmd_set(pairs: list[str]) -> None:
    data = []
    for p in pairs:
        if "=" not in p:
            sys.exit(f"Expected KEY=value, got: {p}")
        k, v = p.split("=", 1)
        data.append({"key": k, "value": v, "is_build_time": True, "is_preview": False})
    s, _ = req("PATCH", f"/applications/{APP_UUID}/envs/bulk", {"data": data})
    print("set", len(data), "vars ->", s)
    cmd_dedupe()


def cmd_domain(service: str, domain: str) -> None:
    s, r = req(
        "PATCH",
        f"/applications/{APP_UUID}",
        {"docker_compose_domains": [{"name": service, "domain": domain}]},
    )
    print(f"domain {service} -> {domain} [{s}]", r)


def cmd_deploy() -> None:
    s, r = req("GET", f"/deploy?uuid={APP_UUID}&force=true")
    print(s, json.dumps(r, ensure_ascii=False))


def cmd_logs(dep: str | None, lines: int) -> None:
    if not dep:
        _, deps = req("GET", f"/deployments?uuid={APP_UUID}")
        if isinstance(deps, list) and deps:
            dep = deps[0].get("deployment_uuid") or deps[0].get("uuid")
        else:
            sys.exit("No deployments found; pass a deployment uuid explicitly.")
    _, d = req("GET", f"/deployments/{dep}")
    print("status:", d.get("status"), "| finished:", d.get("finished_at"))
    for e in json.loads(d.get("logs") or "[]")[-lines:]:
        out = (e.get("output") or "").rstrip()
        if out and not e.get("hidden"):
            print(out[:300])


def cmd_dedupe() -> None:
    """Coolify appends a fresh row per compose parse; drop the redundant ones."""
    _, envs = req("GET", f"/applications/{APP_UUID}/envs")
    cnt = Counter(e["key"] for e in envs)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for e in envs:
        if cnt[e["key"]] > 1:
            grouped[e["key"]].append(e)

    removed = 0
    for key, rows in grouped.items():
        keep = next((r for r in rows if (r.get("value") or "").strip()), rows[0])
        for r in rows:
            if r["uuid"] == keep["uuid"]:
                continue
            st, _ = req("DELETE", f"/applications/{APP_UUID}/envs/{r['uuid']}")
            print(f"  removed duplicate {key} [{st}]")
            removed += 1
    print("duplicates removed:", removed)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "status":
        cmd_status()
    elif cmd == "envs":
        cmd_envs()
    elif cmd == "set":
        cmd_set(args)
    elif cmd == "domain":
        cmd_domain(args[0], args[1])
    elif cmd == "deploy":
        cmd_deploy()
    elif cmd == "logs":
        cmd_logs(args[0] if args else None, int(args[1]) if len(args) > 1 else 40)
    elif cmd == "dedupe":
        cmd_dedupe()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()