"""Optional retained-evidence regression; portable synthetic tests run separately.

Before publication these inputs remain in ignored operator storage. Public CI
skips this module when they are unavailable; it never constructs or runs Alpha.
"""

import builtins
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tadr_benchmark.campaigns import adjudication, freeze, publication
from tadr_benchmark.reporting.plots import build_figures
from tadr_benchmark.serialization import sha256


@pytest.fixture(scope="module")
def alpha_publication(tmp_path_factory):
    root = Path(__file__).parents[1]
    sources = publication.PublicationSources(
        root / ".work/reviews/alpha_execution/candidate",
        root / ".work/reviews/alpha_execution/adjudication_v1",
        root / ".work/reviews/ALPHA_BENCHMARK_V1_SCIENTIFIC_RESULT_REVIEW.md")
    if not all(path.exists() for path in (sources.candidate, sources.adjudication, sources.scientific_review)):
        pytest.skip("Optional retained Alpha evidence is unavailable; portable publication fixtures run separately")
    importer = builtins.__import__
    def forbid_target(name, *args, **kwargs):
        if name == "tadr" or name.startswith("tadr.") or name.startswith("alpha_v1_"):
            raise AssertionError("Publication must not import target or embedded operator code")
        return importer(name, *args, **kwargs)
    with patch("builtins.__import__", forbid_target):
        original = publication.read_artifacts(sources.candidate)
        bundle = publication.read_artifacts(sources.adjudication)
        evidence = publication.original_evidence(original)
        artifacts = publication._assemble(root, sources, frozen_date=None, publication_revision=None)
        stage = tmp_path_factory.mktemp("publication-check") / "staged"
        publication._write_stage(stage, artifacts)
        yield SimpleNamespace(sources=sources, original=original, bundle=bundle,
                              evidence=evidence, artifacts=artifacts, stage=stage)
        assert publication.read_artifacts(sources.candidate) == original
        assert publication.read_artifacts(sources.adjudication) == bundle


def test_complete_retained_publication_verifies_without_target(alpha_publication):
    data = alpha_publication
    manifest, summary = freeze.verify_frozen(data.stage, check_directory_name=False, allow_staged=True)
    assert manifest.status == "ready" and manifest.frozen_date is None
    assert manifest.benchmark_git_commit == "a76bb9458b181500c7bfb9efefcfecfbb019b5a9"
    assert summary.total_attempts == 578
    assert len(data.artifacts) == 1086 and len(data.original) == 1062 and len(data.bundle) == 17
    assert len(data.evidence.inputs.runs) == 578 and len(data.evidence.inputs.diagnostics) == 72
    assert data.evidence.processing.processing_git_commit == "4887bd579d394de523bab0ccb227840d66447fd9"
    assert sha256(data.original["checksums.sha256"]) == publication.ALPHA_CANDIDATE_CHECKSUM
    for name, raw in data.original.items():
        assert data.artifacts[publication.HISTORY.get(name, name)] == raw
    for name, raw in data.bundle.items():
        assert data.artifacts["adjudication_v1/" + name] == raw
    with pytest.raises(ValueError, match="unresolved"):
        freeze.verify_frozen(data.stage, check_directory_name=False)


def test_all_eleven_original_svgs_reproduce_from_persisted_attempt_order(alpha_publication):
    data = alpha_publication
    figures = build_figures({name: list(reversed(rows)) for name, rows in data.evidence.tables.items()},
                            attempts=list(reversed(data.evidence.inputs.attempts)))
    assert len(figures) == 11
    for name, raw in figures.items():
        assert raw == data.original["figures/" + name]
    assert sha256(figures["score_class_imbalance.svg"]) == "7962868e46e957fa58360430009e85aceee8cf7ecb2fe638d21c178f33cfdb52"


def test_public_report_preserves_both_layers_and_adverse_observations(alpha_publication):
    report = alpha_publication.artifacts["REPORT.md"].decode()
    required = (
        "ORIGINAL PREREGISTERED-LABEL RESULT: whole-cell normative conformance 234/320 (73.1250%)",
        "ADJUDICATED PINNED-CONTRACT RESULT: whole-cell normative conformance 320/320 (100.0000%)",
        "Physical detection: 246/314 (78.3439%); 68 physical misses remain",
        "68 representation cells / 34 logical pairs", "identifiers triggered HIGH",
        "practically adverse specificity", "28/36 reference/bounded Finding sets agree exactly; 8 disagree",
        "sampling.leakage.head", "60 → 100", "CRITICAL leakage Finding disappears; hard gate disappears",
        "42 mismatches — 37 CSV/pqstr and 5 native projections", "Decision fields remained equal",
        "parser/scoring non-monotonicity", "collapsed class", "not calibrated damage or safety measures",
        "WSL2-specific", "prepared/uncontrolled", "Sampled RSS", "0.105340397", "5M case", "n=2 weak descriptive evidence",
        "578/578", "72/72", "320/320", "8/8", "159/159", "Singleton groups are **not repeat-tested**",
        "Original physical/design ground truth and preregistered normative labels preceded execution",
        "adjudication occurred after execution", "No target execution changed",
        "physical truth and scientific inputs did not change",
        "canonical reports, attempts, instrumentation and diagnostics were unchanged",
        "implementation is proprietary", "distributes neither Core source nor private wheel bytes",
        "generated source CSV/Parquet files are excluded", "authorized artifact access",
        "adjudication_v1/practical_event_key.json", "history/candidate_REPORT.md",
    )
    for phrase in required:
        assert phrase in report, phrase
    assert not report.startswith("CANDIDATE FOR REVIEW")
    assert alpha_publication.artifacts["history/candidate_REPORT.md"].startswith(b"CANDIDATE FOR REVIEW")
    note = alpha_publication.artifacts["ADJUDICATION_REPRODUCTION.md"].decode()
    assert "not assigned a fictitious Git commit" in note
    assert "actual historical Windows environment" in note
    assert "function takes no report" in note
    for name, digest in json.loads(alpha_publication.bundle["adjudication_provenance.json"])["processor_artifacts"].items():
        assert name in note and digest in note


@pytest.mark.parametrize("mode", ["missing", "altered", "rechecksummed"])
def test_approved_overlay_cannot_be_changed(alpha_publication, mode):
    data = alpha_publication
    bundle = dict(data.bundle)
    if mode == "missing":
        del bundle["practical_event_key.json"]
    else:
        bundle["practical_event_key.json"] = b"[]\n"
        if mode == "rechecksummed":
            bundle["checksums.sha256"] = publication.checksum_bytes(bundle)
    with pytest.raises(ValueError, match="checksum|bundle changed"):
        adjudication.verify_adjudication(data.evidence, bundle, data.sources.scientific_review.read_bytes())
