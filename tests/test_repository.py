from pathlib import Path

from tadr_benchmark.cli import main
from tadr_benchmark.safety import repository_issues
from tadr_benchmark.validation import planned_runs, validate_repository


def test_ready_manifest_has_a_finite_plan_and_unresolved_benchmark_revision():
    import pytest
    from tadr_benchmark.scenarios.families import load_family_scenarios
    root = Path(__file__).parents[1]
    manifests = validate_repository(root)
    alpha = next(item for item in manifests if item.campaign_id == "ALPHA_BENCHMARK_V1")
    assert alpha.status == "ready"
    assert len(alpha.scenario_ids) == 370
    assert alpha.benchmark_git_commit is None
    assert len(alpha.planned_scope.check_ids) == 11
    assert len(planned_runs(alpha, load_family_scenarios(root))) == 578
    with pytest.raises(ValueError, match="not executable"):
        planned_runs(alpha.model_copy(update={"status": "planned"}), [])


def test_repository_candidates_are_public_safe():
    assert repository_issues(Path(__file__).parents[1], include_untracked=True) == []


def test_results_index_is_current_and_measurement_free():
    root = Path(__file__).parents[1]
    assert main(["--root", str(root), "results-index", "--check"]) == 0
    assert "READY / NOT YET RUN" in (root / "RESULTS.md").read_text(encoding="utf-8")
