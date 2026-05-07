# Cohesive units reduce incidental complexity.
"""Guard test for consistency probe token availability."""

from pathlib import Path

from _consistency_probe_core import run_probe


def test_should_return_zero_when_probe_token_is_present():
    """Ensure probe token remains available in tracked targets."""
    repo_root = Path(__file__).resolve().parents[2]

    result = run_probe(repo_root=repo_root, token="SEBASTIANGUTIERREZBETANCOURT")

    assert result == 0
