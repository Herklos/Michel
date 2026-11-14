"""Check the Markdown docs for broken relative links and known stale names.

Run from the repository root:  python scripts/check_docs.py
Exit code 1 if any problem is found. No network access is needed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC_GLOBS = ["README.md", "docs/**/*.md"]
LINK = re.compile(r"\]\(([^)\s]+)\)")
# Names retired by a rename or a re-check. Add a line here when a name is retired.
STALE = {
    "grokbot": "project was renamed to michel",
    "docs/research/temporal-deepagents/": "research files are docs/research/0N-*.md",
}


def markdown_files() -> list[Path]:
    files: list[Path] = []
    for pattern in DOC_GLOBS:
        files.extend(ROOT.glob(pattern))
    return sorted({f for f in files if f.is_file()})


def check() -> list[str]:
    problems: list[str] = []
    for path in markdown_files():
        rel = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        for needle, why in STALE.items():
            if needle in text:
                problems.append(f"{rel}: stale name '{needle}' ({why})")
        for match in LINK.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            file_part = target.split("#", 1)[0]
            if not file_part:
                continue
            resolved = (path.parent / file_part).resolve()
            if not resolved.exists():
                problems.append(f"{rel}: broken link '{target}'")
    return problems


if __name__ == "__main__":
    found = check()
    for line in found:
        print(line)
    print(f"{len(markdown_files())} files checked, {len(found)} problem(s)")
    sys.exit(1 if found else 0)
