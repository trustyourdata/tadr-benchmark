from pathlib import Path

from tadr_benchmark.cli import main
from tadr_benchmark.safety import repository_issues
from tadr_benchmark.validation import planned_runs, validate_repository


def test_bootstrap_manifest_is_planned_and_not_executable():
    import pytest
    root = Path(__file__).parents[1]
    manifests = validate_repository(root)
    alpha = next(item for item in manifests if item.campaign_id == "ALPHA_BENCHMARK_V1")
    assert alpha.status == "planned"
    assert alpha.scenario_ids == []
    assert len(alpha.planned_scope.check_ids) == 11
    with pytest.raises(ValueError, match="not executable"):
        planned_runs(alpha, [])


def test_repository_candidates_are_public_safe():
    assert repository_issues(Path(__file__).parents[1], include_untracked=True) == []


def test_results_index_is_current_and_measurement_free():
    root = Path(__file__).parents[1]
    assert main(["--root", str(root), "results-index", "--check"]) == 0
    assert "PLANNED / NOT YET RUN" in (root / "RESULTS.md").read_text(encoding="utf-8")
