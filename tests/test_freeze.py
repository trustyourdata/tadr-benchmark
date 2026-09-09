import json

import pytest

from tadr_benchmark.campaigns import freeze as publication
from tadr_benchmark.models import RunResult
from tadr_benchmark.serialization import sha256
from tadr_benchmark.execution.attempts import make_attempt


@pytest.fixture
def freeze_fixture(tmp_path, monkeypatch, campaign, scenario, completed, environment):
    # Isolate filesystem publication tests from the developer's real Git state.
    monkeypatch.setattr(publication, "require_clean_revision", lambda *args: "b" * 40)
    monkeypatch.setattr(publication, "repository_issues", lambda *args, **kwargs: [])
    runs, reports = completed
    return dict(root=tmp_path, manifest=campaign, scenarios=[scenario], runs=runs,
                environments={environment.environment_id: environment}, reports=reports,
                frozen_date="2026-01-01", public_reviewed=True, attempts=[make_attempt(r) for r in runs])


def test_freeze_round_trip_and_no_overwrite(freeze_fixture):
    destination = publication.freeze(**freeze_fixture)
    manifest, summary = publication.verify_frozen(destination)
    assert manifest.status == "frozen"
    assert manifest.target_source_distribution == "proprietary"
    assert manifest.target_repository_url_or_null is None
    assert summary.groups[0].measured_runs == 2
    assert summary.total_attempts == 3 and summary.infrastructure_retries == 0
    checksums = (destination / "checksums.sha256").read_text()
    assert "attempts.jsonl" in checksums and "protocol.md" in checksums
    assert len(list((destination / "tables").glob("*.csv"))) == 16
    with pytest.raises(ValueError, match="already exists"):
        publication.freeze(**freeze_fixture)


def test_freeze_still_rejects_missing_target_fingerprint(freeze_fixture):
    # Bypass construction to confirm the publication boundary revalidates it.
    freeze_fixture["manifest"] = freeze_fixture["manifest"].model_copy(
        update={"target_installation_artifact_sha256": None})
    with pytest.raises(ValueError, match="artifact fingerprint"):
        publication.freeze(**freeze_fixture)
    assert not (freeze_fixture["root"] / "results/campaigns/fixture_v1").exists()


def test_fixture_artifact_fingerprint_is_bound_to_frozen_outcomes(freeze_fixture):
    from tadr_benchmark.models import CampaignManifest
    fingerprint = sha256(b"synthetic installation artifact fixture")
    manifest = CampaignManifest.model_validate({**freeze_fixture["manifest"].model_dump(),
        "target_installation_artifact_sha256": fingerprint})
    freeze_fixture["manifest"] = manifest
    with pytest.raises(ValueError, match="run provenance differs"):
        publication.freeze(**freeze_fixture)  # Runs must carry the same reviewed fingerprint.
    runs = [RunResult.model_validate({**r.model_dump(), "target_installation_artifact_sha256": fingerprint})
            for r in freeze_fixture["runs"]]
    freeze_fixture.update(runs=runs, attempts=[make_attempt(r) for r in runs])
    destination = publication.freeze(**freeze_fixture)
    frozen, _ = publication.verify_frozen(destination)
    assert frozen.target_installation_artifact_sha256 == fingerprint
    assert frozen.target_repository_url_or_null is None
    assert fingerprint in (destination / "REPORT.md").read_text()
    assert all(json.loads(line)["outcome"]["target_installation_artifact_sha256"] == fingerprint
               for line in (destination / "attempts.jsonl").read_text().splitlines())


def test_rechecksummed_stale_derived_table_is_rejected(freeze_fixture):
    destination = publication.freeze(**freeze_fixture)
    table = destination / "tables" / "identity.csv"
    table.write_bytes(table.read_bytes()+b"stale\n")
    inventory = sorted(p.relative_to(destination).as_posix() for p in destination.rglob("*")
                       if p.is_file() and p.name != "checksums.sha256")
    (destination / "checksums.sha256").write_text("".join(
        sha256((destination / name).read_bytes())+"  "+name+"\n" for name in inventory), encoding="utf-8")
    with pytest.raises(ValueError, match="derived table is stale"):
        publication.verify_frozen(destination)


@pytest.mark.parametrize("failure", ["unreviewed", "missing_run", "missing_truth", "wrong_report", "unsafe_report", "wrong_environment"])
def test_freeze_rejects_invalid_artifacts(freeze_fixture, failure):
    args = freeze_fixture
    if failure == "unreviewed":
        args["public_reviewed"] = False
    elif failure == "missing_run":
        args["runs"] = args["runs"][:-1]
    elif failure == "missing_truth":
        args["scenarios"] = []
    elif failure == "wrong_report":
        args["reports"][args["runs"][0].run_id] = b"{}"
    elif failure == "wrong_environment":
        args["environments"] = {}
    else:
        run = args["runs"][0]
        data = json.loads(args["reports"][run.run_id])
        data["unsafe"] = "C:" + "/" + "Users/example/source"
        original = json.dumps(data).encode()
        args["reports"][run.run_id] = original
        args["runs"][0] = RunResult.model_validate({**run.model_dump(), "canonical_report_sha256": sha256(original)})
    with pytest.raises(ValueError):
        publication.freeze(**args)
    assert not (args["root"] / "results/campaigns/fixture_v1").exists()


def test_checksum_detects_tampering(freeze_fixture):
    destination = publication.freeze(**freeze_fixture)
    (destination / "summary.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        publication.verify_frozen(destination)


def test_unchecksummed_file_is_rejected(freeze_fixture):
    destination = publication.freeze(**freeze_fixture)
    (destination / "unexpected.txt").write_text("extra", encoding="utf-8")
    with pytest.raises(ValueError, match="unchecksummed"):
        publication.verify_frozen(destination)


def test_dirty_benchmark_cannot_freeze(monkeypatch, tmp_path):
    from types import SimpleNamespace
    monkeypatch.setattr(publication.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=" M README.md"))
    with pytest.raises(ValueError, match="clean"):
        publication.require_clean_revision(tmp_path, "b" * 40)


def test_wrong_benchmark_revision_cannot_freeze(monkeypatch, tmp_path):
    from types import SimpleNamespace
    responses = iter(["", "a" * 40])
    monkeypatch.setattr(publication.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=next(responses)))
    with pytest.raises(ValueError, match="revision"):
        publication.require_clean_revision(tmp_path, "b" * 40)


def test_history_rejects_rechecksummed_rewrite(monkeypatch, tmp_path):
    from types import SimpleNamespace
    def git(args, **kwargs):
        if args[1] == "ls-tree":
            return SimpleNamespace(stdout="results/campaigns/fixture_v1/manifest.json\n")
        if args[1] == "show":
            return SimpleNamespace(stdout=b'{"status":"frozen"}')
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(publication.subprocess, "run", git)
    with pytest.raises(ValueError, match="historical frozen"):
        publication.verify_history(tmp_path, "b" * 40)


def test_changed_observation_cannot_hide_behind_valid_report_hash(freeze_fixture):
    run = freeze_fixture["runs"][0]
    freeze_fixture["runs"][0] = RunResult.model_validate({**run.model_dump(), "readiness_score": 90})
    with pytest.raises(ValueError, match="target report"):
        publication.freeze(**freeze_fixture)


def test_historical_scenario_identity_is_immutable(freeze_fixture, scenario):
    from tadr_benchmark.models import ScenarioSpec
    from tadr_benchmark.validation import validate_historical_scenarios
    publication.freeze(**freeze_fixture)
    validate_historical_scenarios(freeze_fixture["root"], [scenario])
    changed = ScenarioSpec.model_validate({**scenario.model_dump(), "description": "Changed experiment"})
    with pytest.raises(ValueError, match="historical scenario"):
        validate_historical_scenarios(freeze_fixture["root"], [changed])
