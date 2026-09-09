"""Synthetic release fixtures only; no target imports or scientific invocations."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tadr_benchmark.campaigns import adjudication, freeze, publication
from tadr_benchmark.campaigns.processing import ProcessingProvenance
from tadr_benchmark.execution.attempts import make_attempt
from tadr_benchmark.reporting import publication as report_generator
from tadr_benchmark.reporting.markdown import campaign_report
from tadr_benchmark.reporting.plots import build_figures, plotting_tables
from tadr_benchmark.reporting.protocol import protocol_bytes
from tadr_benchmark.reporting.queries import ReportInputs, TABLE_COLUMNS, table_rows
from tadr_benchmark.reporting.aggregate import aggregate
from tadr_benchmark.serialization import canonical_bytes, sha256


@pytest.fixture
def publication_fixture(tmp_path, monkeypatch, campaign, scenario, completed, environment):
    # Use the portable generic harness to construct original evidence. The
    # adjudication/report mocks isolate publication mechanics, not metric tests.
    monkeypatch.setattr(freeze, "require_clean_revision", lambda *args: "b" * 40)
    monkeypatch.setattr(freeze, "repository_issues", lambda *args, **kwargs: [])
    runs, reports = completed
    attempts = [make_attempt(run) for run in runs]
    legacy = freeze.freeze(tmp_path / "seed", campaign, [scenario], runs,
                           {environment.environment_id: environment}, reports, "2026-01-01",
                           public_reviewed=True, attempts=attempts)
    original = publication.read_artifacts(legacy)
    inputs = ReportInputs(campaign, [scenario], runs, [], reports, attempts)
    tables = table_rows(inputs)
    figures = build_figures(tables, attempts=attempts)
    original["manifest.json"] = canonical_bytes(campaign)
    original["protocol.md"] = protocol_bytes(campaign)
    original["REPORT.md"] = ("CANDIDATE FOR REVIEW — NOT FROZEN\n\n" + campaign_report(
        campaign, aggregate(campaign.campaign_id, runs, [], attempts), tables=tables, figures=figures)).encode()
    original["execution_provenance.json"] = canonical_bytes({
        "manifest": campaign.model_dump(mode="json"), "environment": environment.model_dump(mode="json")})
    original["processing_provenance.json"] = canonical_bytes(ProcessingProvenance(
        execution_git_commit="b" * 40, processing_git_commit="c" * 40,
        execution_binding_sha256=sha256(original["execution_provenance.json"]),
        attempts_sha256=sha256(original["attempts.jsonl"]), processing_environment=environment))
    original["checksums.sha256"] = publication.checksum_bytes(original)
    sources = publication.PublicationSources(tmp_path / ".work/original", tmp_path / ".work/overlay",
                                              tmp_path / ".work/scientific_review.md")
    publication._write_stage(sources.candidate, original)
    overlay = {name: b"{}\n" for name in adjudication.BUNDLE_FILES}
    overlay["checksums.sha256"] = publication.checksum_bytes(overlay)
    publication._write_stage(sources.adjudication, overlay)
    sources.scientific_review.write_text("Synthetic fixture review only.\n")

    def check_fixture_overlay(evidence, bundle, review):
        publication.verify_checksums(bundle)
        publication.require(set(bundle) == adjudication.BUNDLE_FILES, "complete adjudication bundle is required")
        return {"fixture": True}

    monkeypatch.setattr(adjudication, "verify_adjudication", check_fixture_overlay)
    monkeypatch.setattr(report_generator, "publication_report", lambda evidence, overlay, provenance, manifest:
                        "Synthetic publication only.\n" + canonical_bytes(provenance).decode())
    monkeypatch.setattr(report_generator, "adjudication_reproduction", lambda bundle: "Synthetic reconstruction.\n")
    monkeypatch.setattr(publication, "capture_environment", lambda: environment)
    monkeypatch.setattr(publication, "repository_issues", lambda *args, **kwargs: [])
    monkeypatch.setattr(publication, "require_publication_code", lambda root: None)
    monkeypatch.setattr(freeze, "require_clean_revision", lambda *args: "d" * 40)
    return SimpleNamespace(root=tmp_path, sources=sources, original=original, overlay=overlay)


def test_complete_release_is_validated_before_atomic_creation(publication_fixture, monkeypatch):
    fixture = publication_fixture
    actual_verify = publication.verify_publication
    events = []

    def check_stage(stage, **kwargs):
        assert not (fixture.root / "results/campaigns/fixture_v1").exists()
        artifacts = publication.read_artifacts(stage)
        assert {"adjudication_v1/" + name for name in fixture.overlay} <= set(artifacts)
        for name, raw in fixture.original.items():
            assert artifacts[publication.HISTORY.get(name, name)] == raw
        result = actual_verify(stage, **kwargs)
        events.append("complete stage verified")
        return result

    monkeypatch.setattr(publication, "verify_publication", check_stage)
    destination = publication.freeze_publication(fixture.root, fixture.sources, "2026-01-02", public_reviewed=True)
    assert events == ["complete stage verified"]
    manifest, _ = actual_verify(destination)
    provenance = json.loads((destination / "publication_provenance.json").read_bytes())
    assert provenance["scientific_execution_revision"] == manifest.benchmark_git_commit == "b" * 40
    assert provenance["historical_processing_revision"] == "c" * 40
    assert provenance["publication_assembly_revision"] == "d" * 40
    assert {json.loads(line)["benchmark_git_commit"] for line in
            (destination / "runs.jsonl").read_bytes().splitlines()} == {"b" * 40}
    for name in ("runs.jsonl", "attempts.jsonl", "processing_provenance.json", "execution_provenance.json"):
        assert (destination / name).read_bytes() == fixture.original[name]
    assert {**manifest.model_dump(), "status": "ready", "frozen_date": None} == json.loads(fixture.original["manifest.json"])
    with pytest.raises(ValueError, match="already exists"):
        publication.freeze_publication(fixture.root, fixture.sources, "2026-01-02", public_reviewed=True)


def test_failed_verification_never_creates_immutable_directory(publication_fixture, monkeypatch):
    fixture = publication_fixture
    def reject(*args, **kwargs):
        raise ValueError("fixture verification failure")
    monkeypatch.setattr(publication, "verify_publication", reject)
    with pytest.raises(ValueError, match="fixture verification failure"):
        publication.freeze_publication(fixture.root, fixture.sources, "2026-01-02", public_reviewed=True)
    assert not (fixture.root / "results/campaigns/fixture_v1").exists()


def test_stage_does_not_invent_publication_revision_or_freeze(publication_fixture):
    fixture = publication_fixture
    stage = publication.stage_publication(fixture.root, fixture.sources, fixture.root / ".work/stage")
    provenance = publication.PublicationProvenance.model_validate_json((stage / "publication_provenance.json").read_bytes())
    assert provenance.publication_assembly_revision is None and provenance.state == "staged"
    assert json.loads((stage / "manifest.json").read_bytes())["frozen_date"] is None
    with pytest.raises(ValueError, match="unresolved"):
        freeze.verify_frozen(stage, check_directory_name=False)
    assert freeze.verify_frozen(stage, check_directory_name=False, allow_staged=True)[0].status == "ready"
    assert not (fixture.root / "results/campaigns/fixture_v1").exists()
    with pytest.raises(ValueError, match="ignored .work"):
        publication.stage_publication(fixture.root, fixture.sources, fixture.root / "public-stage")


@pytest.mark.parametrize("tamper", ["missing_overlay", "altered_overlay", "inner_checksums", "history",
                                    "mapping", "report", "execution_role", "manifest_revision", "unsafe"])
def test_rechecksummed_publication_tampering_is_rejected(publication_fixture, tamper):
    fixture = publication_fixture
    artifacts = publication._assemble(fixture.root, fixture.sources, frozen_date=None, publication_revision=None)
    if tamper == "missing_overlay":
        del artifacts["adjudication_v1/practical_event_key.json"]
    elif tamper == "altered_overlay":
        artifacts["adjudication_v1/practical_event_key.json"] = b"[{}]\n"
    elif tamper == "inner_checksums":
        artifacts["adjudication_v1/checksums.sha256"] = b""
    elif tamper == "history":
        artifacts["history/candidate_REPORT.md"] += b"changed\n"
    elif tamper == "mapping":
        value = json.loads(artifacts["publication_inventory.json"])
        value["original_candidate_mapping"]["REPORT.md"] = "REPORT.md"
        artifacts["publication_inventory.json"] = canonical_bytes(value)
    elif tamper == "report":
        artifacts["REPORT.md"] = b"Only favorable results.\n"
    elif tamper == "execution_role":
        value = json.loads(artifacts["publication_provenance.json"])
        value["scientific_execution_revision"] = "d" * 40
        artifacts["publication_provenance.json"] = canonical_bytes(value)
    elif tamper == "manifest_revision":
        value = json.loads(artifacts["manifest.json"])
        value["benchmark_git_commit"] = "d" * 40
        artifacts["manifest.json"] = canonical_bytes(value)
    else:
        artifacts["REPORT.md"] = ("C:" + "/" + "Users/example/private\n").encode()
    artifacts["checksums.sha256"] = publication.checksum_bytes(artifacts)
    stage = fixture.root / ".work/tampered"
    publication._write_stage(stage, artifacts)
    with pytest.raises(ValueError):
        freeze.verify_frozen(stage, check_directory_name=False, allow_staged=True)


def test_publication_code_must_match_clean_checkout(tmp_path, monkeypatch):
    monkeypatch.setattr(publication.subprocess, "run", lambda *args, **kwargs: SimpleNamespace(stdout=""))
    with pytest.raises(ValueError, match="assembly code differs"):
        publication.require_publication_code(tmp_path)


def test_tied_x_values_follow_selected_attempt_bindings_without_changing_tables(completed):
    runs, _ = completed
    attempts = sorted([make_attempt(run) for run in runs], key=lambda a: a.attempt_id)
    tables = {name: [] for name in TABLE_COLUMNS}
    points = [dict(run_id=a.run_id, family="class", case="support", format="csv", count=5,
                   readiness_score=score) for a, score in zip(attempts, (100, 92, 90))]
    tables["score_sweeps.csv"] = list(reversed(points))
    ordered = plotting_tables(tables, list(reversed(attempts)))
    assert ordered["score_sweeps.csv"] == points
    assert tables["score_sweeps.csv"] == list(reversed(points))
    first = build_figures(tables, attempts=attempts)
    tables["score_sweeps.csv"] = points
    assert first == build_figures(tables, attempts=list(reversed(attempts)))
    assert first != build_figures({**tables, "score_sweeps.csv": list(reversed(points))})
    with pytest.raises(ValueError, match="unique selected"):
        plotting_tables(tables, attempts + attempts[:1])
    with pytest.raises(ValueError, match="no selected attempt"):
        plotting_tables(tables, attempts[:1])

    with pytest.raises(ValueError, match="unique selected"):
        plotting_tables(tables, [attempts[0], attempts[1].model_copy(update={"attempt_id": attempts[0].attempt_id})])
    with pytest.raises(ValueError, match="one score row"):
        plotting_tables({**tables, "score_sweeps.csv": points + points[:1]}, attempts)
