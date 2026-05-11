#!/usr/bin/env python3
"""Validador de plugadvpl plugin structure."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
EXPECTED_COMMAND_SKILLS = {
    "init",
    "ingest",
    "reindex",
    "status",
    "find",
    "callers",
    "callees",
    "tables",
    "param",
    "arch",
    "lint",
    "doctor",
    "grep",
}
EXPECTED_KNOWLEDGE_SKILLS = {
    "plugadvpl-index-usage",
    "advpl-encoding",
    "advpl-fundamentals",
    "advpl-mvc",
    "advpl-embedded-sql",
    "advpl-matxfis",
    "advpl-pontos-entrada",
    "advpl-webservice",
    "advpl-jobs-rpc",
    "advpl-code-review",
    "advpl-advanced",
    "advpl-tlpp",
    "advpl-web",
    "advpl-dicionario-sx",
    "advpl-mvc-avancado",
}
EXPECTED_AGENTS = {
    "advpl-analyzer",
    "advpl-impact-analyzer",
    "advpl-code-generator",
    "advpl-reviewer-bot",
}


def check_plugin_json() -> list[str]:
    errors = []
    p = ROOT / ".claude-plugin" / "plugin.json"
    if not p.exists():
        return [f"missing: {p}"]
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {p}: {e}"]
    for field in ["name", "version", "description"]:
        if field not in data:
            errors.append(f"plugin.json missing field: {field}")
    if data.get("name") != "plugadvpl":
        errors.append(
            f"plugin.json: name must be 'plugadvpl', got '{data.get('name')}'"
        )
    return errors


def check_marketplace_json() -> list[str]:
    errors = []
    p = ROOT / ".claude-plugin" / "marketplace.json"
    if not p.exists():
        return [f"missing: {p}"]
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {p}: {e}"]
    if "name" not in data or "owner" not in data or "plugins" not in data:
        errors.append(
            "marketplace.json missing required fields (name, owner, plugins)"
        )
    return errors


def check_skills() -> list[str]:
    errors = []
    skills_dir = ROOT / "skills"
    found = {
        p.name
        for p in skills_dir.iterdir()
        if p.is_dir() and (p / "SKILL.md").exists()
    }
    missing_cmd = EXPECTED_COMMAND_SKILLS - found
    missing_kn = EXPECTED_KNOWLEDGE_SKILLS - found
    if missing_cmd:
        errors.append(f"missing command skills: {sorted(missing_cmd)}")
    if missing_kn:
        errors.append(f"missing knowledge skills: {sorted(missing_kn)}")
    # Frontmatter check
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        sf = skill_dir / "SKILL.md"
        if not sf.exists():
            continue
        content = sf.read_text(encoding="utf-8", errors="replace")
        if not content.startswith("---"):
            errors.append(f"{sf}: missing YAML frontmatter")
            continue
        # Check `description:` present
        m = re.search(r"^description:\s*(.+)$", content[:1000], re.MULTILINE)
        if not m:
            errors.append(f"{sf}: missing 'description' in frontmatter")
    return errors


def check_agents() -> list[str]:
    errors = []
    agents_dir = ROOT / "agents"
    found = set()
    for p in agents_dir.iterdir():
        if p.suffix == ".md":
            found.add(p.stem)
    missing = EXPECTED_AGENTS - found
    if missing:
        errors.append(f"missing agents: {sorted(missing)}")
    # Frontmatter check
    for p in agents_dir.glob("*.md"):
        content = p.read_text(encoding="utf-8", errors="replace")
        if not content.startswith("---"):
            errors.append(f"{p}: missing YAML frontmatter")
            continue
        for field in ["name", "description"]:
            if not re.search(rf"^{field}:", content[:500], re.MULTILINE):
                errors.append(f"{p}: missing '{field}' in frontmatter")
    return errors


def check_hook() -> list[str]:
    errors = []
    p = ROOT / "hooks" / "hooks.json"
    if not p.exists():
        return [f"missing: {p}"]
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"invalid JSON: {p}: {e}"]
    if "hooks" not in data:
        errors.append("hooks.json missing 'hooks' key")
    if "SessionStart" not in data.get("hooks", {}):
        errors.append("hooks.json missing SessionStart")
    # Check session-start.mjs exists
    mjs = ROOT / "hooks" / "session-start.mjs"
    if not mjs.exists():
        errors.append(f"missing: {mjs}")
    return errors


def main() -> int:
    print("plugadvpl plugin validation\n")
    all_errors = []
    for name, check in [
        ("plugin.json", check_plugin_json),
        ("marketplace.json", check_marketplace_json),
        ("skills/", check_skills),
        ("agents/", check_agents),
        ("hooks/", check_hook),
    ]:
        errs = check()
        if errs:
            print(f"[FAIL] {name}")
            for e in errs:
                print(f"   - {e}")
            all_errors.extend(errs)
        else:
            print(f"[OK] {name}")

    if all_errors:
        print(f"\n{len(all_errors)} errors found")
        return 1
    print("\nAll checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
