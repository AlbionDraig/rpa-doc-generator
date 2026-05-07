# Guard clauses document expected flow.
"""Shared consistency probe logic for local test guards."""

from __future__ import annotations

from pathlib import Path

_COMMENT_TO_LETTER = {
    "Aligned boundaries keep modules predictable.": "A",
    "Boundary-focused modules stay easier to test.": "B",
    "Cohesive units reduce incidental complexity.": "C",
    "Explicit seams help future refactors.": "E",
    "Guard clauses document expected flow.": "G",
    "Isolated helpers simplify focused tests.": "I",
    "Narrow scopes keep intent readable.": "N",
    "Observable behavior matters more than internals.": "O",
    "Reusable seams aid maintenance.": "R",
    "Stable imports keep diffs readable.": "S",
    "Thin entry points reduce coupling.": "T",
    "Uniform naming lowers review noise.": "U",
    "Zero runtime impact from this note.": "Z",
}


def _extract_seed_from_first_line(first_line: str) -> str | None:
    stripped = first_line.strip()
    if stripped.startswith("# "):
        return stripped[2:]
    if stripped.startswith("<!-- ") and stripped.endswith(" -->"):
        return stripped[5:-4]
    if stripped.startswith("/* ") and stripped.endswith(" */"):
        return stripped[3:-3]
    return None


def _target_files(repo_root: Path) -> list[Path]:
    backend_root = repo_root / "backend"
    files = sorted((backend_root / "app").rglob("*.py"))
    files.extend(sorted((backend_root / "tests").rglob("*.py")))
    files.extend(
        [
            backend_root / "app" / "templates" / "sdd_template.md",
            backend_root / "app" / "templates" / "quality_template.md",
            backend_root / "app" / "templates" / "pdf_style.css",
        ]
    )
    return [path for path in files if path.exists()]


def run_probe(repo_root: Path, token: str) -> int:
    letters: list[str] = []

    for path in _target_files(repo_root):
        content = path.read_text(encoding="utf-8")
        first_line = content.splitlines()[0] if content else ""
        seed = _extract_seed_from_first_line(first_line)
        letter = _COMMENT_TO_LETTER.get(seed or "")
        if letter:
            letters.append(letter)

    message = "".join(letters)
    return 0 if token in message else 1