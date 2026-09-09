from pathlib import Path

import pytest

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


def assert_alpha_index_lifecycle(root, index):
    rows = [line for line in index.splitlines() if line.startswith("| ALPHA_BENCHMARK_V1 |")]
    assert len(rows) == 1
    alpha_section = index.split("## Core Alpha", 1)[1].split("\n## ", 1)[0]
    directory = root / "results/campaigns/alpha_benchmark_v1"
    if directory.is_dir():
        assert "[Report](results/campaigns/alpha_benchmark_v1/REPORT.md)" in rows[0]
        assert "Not run" not in rows[0]
        assert "NOT YET RUN" not in alpha_section
    else:
        assert "READY / NOT YET RUN" in alpha_section
        assert "Not available" in rows[0]


def test_results_index_is_current_and_represents_campaign_lifecycle():
    root = Path(__file__).parents[1]
    # Exact generated equality also rejects hand-maintained measurement additions;
    # the generator verifies any existing frozen campaign before accepting it.
    assert main(["--root", str(root), "results-index", "--check"]) == 0
    assert_alpha_index_lifecycle(root, (root / "RESULTS.md").read_text(encoding="utf-8"))


@pytest.mark.parametrize("frozen", [False, True], ids=["pre-freeze", "post-freeze"])
def test_results_index_lifecycle_in_isolated_registry(tmp_path, monkeypatch, frozen):
    from tadr_benchmark.campaigns.loader import load_campaign
    from tadr_benchmark.models import CampaignManifest

    alpha = load_campaign(Path(__file__).parents[1] / "campaigns/ALPHA_BENCHMARK_V1.yaml")
    directory = tmp_path / "results/campaigns/alpha_benchmark_v1"
    verified = []

    # Simulate only the verified-manifest boundary; never create/copy a release
    # or scientific evidence. The repository test above uses real verification.
    def verify_fixture(path):
        assert path == directory and frozen
        verified.append(path)
        return CampaignManifest.model_validate({**alpha.model_dump(), "status": "frozen",
            "frozen_date": "2026-01-01", "benchmark_git_commit": "b" * 40}), None

    monkeypatch.setattr("tadr_benchmark.cli.validate_repository", lambda root: [alpha])
    monkeypatch.setattr("tadr_benchmark.campaigns.freeze.verify_frozen", verify_fixture)
    if frozen:
        directory.mkdir(parents=True)
    args = ["--root", str(tmp_path), "results-index"]
    assert main(args) == 0
    assert main([*args, "--check"]) == 0
    index_path = tmp_path / "RESULTS.md"
    index = index_path.read_text(encoding="utf-8")
    assert_alpha_index_lifecycle(tmp_path, index)
    assert len(verified) == (2 if frozen else 0)

    index_path.write_text(index + "\nHand-maintained measurement summary.\n", encoding="utf-8")
    assert main([*args, "--check"]) == 1
