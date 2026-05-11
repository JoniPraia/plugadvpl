#!/usr/bin/env python3
"""Sync plugin.json and marketplace.json version from hatch-vcs derived version."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def get_version() -> str:
    """Either accept arg or derive from hatch version."""
    if len(sys.argv) > 1:
        v = sys.argv[1]
        if v.startswith("v"):
            v = v[1:]
        return v
    result = subprocess.run(
        ["hatch", "version"],
        cwd=ROOT / "cli",
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def main() -> None:
    version = get_version()
    print(f"Bumping to version: {version}")

    plugin_json_path = ROOT / ".claude-plugin" / "plugin.json"
    plugin_data = json.loads(plugin_json_path.read_text(encoding="utf-8"))
    plugin_data["version"] = version
    plugin_json_path.write_text(
        json.dumps(plugin_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] {plugin_json_path}")

    marketplace_json_path = ROOT / ".claude-plugin" / "marketplace.json"
    marketplace_data = json.loads(marketplace_json_path.read_text(encoding="utf-8"))
    for p in marketplace_data.get("plugins", []):
        if p.get("name") == "plugadvpl":
            p["version"] = version
    marketplace_json_path.write_text(
        json.dumps(marketplace_data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] {marketplace_json_path}")


if __name__ == "__main__":
    main()
