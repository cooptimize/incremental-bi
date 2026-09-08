#!/usr/bin/env python3
"""Validate the incremental-bi knowledge vault.

Checks (stdlib only, no pip installs):
1. Frontmatter lint: every *.md under the vault layer folders has YAML
   frontmatter with title:, layer: (from an allowed set), and status:
   (draft | working | stable).
2. Related links: every path under `related:` resolves to an existing file
   (%20 decoded to space).
3. Pattern Index: every pattern file appears by filename in "Pattern Index.md",
   and every markdown link target in "Pattern Index.md" exists.
4. teamai.yaml sanity: team:, repo:, provider: keys present.

Exits 0 on PASS, 1 on FAIL.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LAYER_DIRS = [
    "Bronze",
    "Silver",
    "Gold",
    "Cross-Cutting",
    "Decisions",
    "Semantic Model",
    "Snapshots",
]

ALLOWED_LAYERS = {
    "bronze",
    "silver",
    "gold",
    "cross-cutting",
    "snapshots",
    "semantic-model",
    "decisions",
}

ALLOWED_STATUS = {"draft", "working", "stable"}

errors = []


def err(msg):
    errors.append(msg)


def parse_frontmatter(path):
    """Return (frontmatter_text, None) or (None, reason)."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, "no opening '---' frontmatter fence"
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[1:i]), None
    return None, "no closing '---' frontmatter fence"


def pattern_files():
    for d in LAYER_DIRS:
        base = ROOT / d
        if not base.is_dir():
            err(f"layer directory missing: {d}/")
            continue
        yield from sorted(base.rglob("*.md"))


def check_frontmatter_and_related():
    files = list(pattern_files())
    for f in files:
        rel = f.relative_to(ROOT)
        fm, problem = parse_frontmatter(f)
        if fm is None:
            err(f"{rel}: {problem}")
            continue

        m = re.search(r"^title:\s*(.+)$", fm, re.M)
        if not m or not m.group(1).strip():
            err(f"{rel}: missing or empty 'title:' in frontmatter")

        m = re.search(r"^layer:\s*(\S+)\s*$", fm, re.M)
        if not m:
            err(f"{rel}: missing 'layer:' in frontmatter")
        elif m.group(1) not in ALLOWED_LAYERS:
            err(f"{rel}: layer '{m.group(1)}' not in {sorted(ALLOWED_LAYERS)}")

        m = re.search(r"^status:\s*(\S+)\s*$", fm, re.M)
        if not m:
            err(f"{rel}: missing 'status:' in frontmatter")
        elif m.group(1) not in ALLOWED_STATUS:
            err(f"{rel}: status '{m.group(1)}' not in {sorted(ALLOWED_STATUS)}")

        # related: block — list items indented under the key
        m = re.search(r"^related:\s*\n((?:[ \t]+-[ \t]*\S.*\n?)+)", fm, re.M)
        if m:
            for item in re.finditer(r"^[ \t]+-[ \t]*(.+?)\s*$", m.group(1), re.M):
                target = item.group(1).strip().strip('"').strip("'")
                target = target.replace("%20", " ")
                if not (ROOT / target).is_file():
                    err(f"{rel}: related target does not exist: {target}")
    return files


def check_pattern_index(files):
    index = ROOT / "Pattern Index.md"
    if not index.is_file():
        err("Pattern Index.md not found at repo root")
        return
    text = index.read_text(encoding="utf-8")

    for f in files:
        rel = f.relative_to(ROOT)
        # The index lists patterns by repo-relative path in the File column.
        # Require the relative path so a rename can't hide behind a
        # same-named file in another layer (e.g. three "Full Load.md" files).
        if str(rel) not in text:
            err(f"{rel}: not listed in Pattern Index.md")

    # Every markdown link target and every backticked layer-folder path in
    # the index must resolve. (Historical notes about pre-rename lowercase
    # paths are intentionally not matched by the layer-dir anchor.)
    targets = [m.group(1) for m in re.finditer(r"\]\(([^)]+\.md)\)", text)]
    for d in LAYER_DIRS:
        targets += re.findall(rf"`({re.escape(d)}/[^`]+\.md)`", text)
    for target in targets:
        target = target.replace("%20", " ")
        if not (ROOT / target).is_file():
            err(f"Pattern Index.md: referenced path does not exist: {target}")


def check_teamai_yaml():
    cfg = ROOT / "teamai.yaml"
    if not cfg.is_file():
        err("teamai.yaml not found at repo root")
        return
    text = cfg.read_text(encoding="utf-8")
    for key in ("team:", "repo:", "provider:"):
        if not re.search(rf"^\s*{re.escape(key)}", text, re.M):
            err(f"teamai.yaml: missing key '{key}'")


def main():
    files = check_frontmatter_and_related()
    check_pattern_index(files)
    check_teamai_yaml()

    if errors:
        print(f"FAIL: {len(errors)} problem(s) found")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"PASS: {len(files)} pattern files validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
