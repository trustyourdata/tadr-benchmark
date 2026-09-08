"""Public proprietary-target provenance; no live target or research execution."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from tadr_benchmark.campaigns.loader import load_campaign
from tadr_benchmark.models import CampaignManifest, TargetMetadata
from tadr_benchmark.reporting.aggregate import aggregate
from tadr_benchmark.reporting.markdown import campaign_report, results_index
from tadr_benchmark.safety import scan_files


@pytest.fixture
def alpha():
    return load_campaign(Path(__file__).parents[1] / "campaigns/ALPHA_BENCHMARK_V1.yaml")


def test_planned_alpha_has_public_identity_and_unresolved_artifact(alpha):
    assert alpha.status == "planned"
    assert {k: getattr(alpha, k) for k in TargetMetadata.model_fields} == {
        "target_name": "tadr-core", "target_package_version": "0.1.0",
        "target_source_distribution": "proprietary", "target_repository_url_or_null": None,
        "target_installation_artifact_sha256": None, "target_algorithm_version": "1.0",
        "target_threshold_profile": "MVP_V1", "target_bundle_protocol": "1.0", "target_baseline_revision": "1.0.12"}
    assert not alpha.execution_readiness.target_artifact_verified
    assert not alpha.execution_readiness.target_metadata_verified
    assert not alpha.execution_readiness.host_provisioned
    assert not alpha.execution_readiness.instrumentation_validated
    assert alpha.benchmark_git_commit is None


@pytest.mark.parametrize("status", ["ready", "frozen"])
def test_proprietary_target_gate_requires_artifact_and_reviewed_metadata(alpha, status):
    # Metadata validation only: never changes or freezes the real campaign.
    data = {**alpha.model_dump(), "status": status, "benchmark_git_commit": "b" * 40,
            "frozen_date": "2026-01-01" if status == "frozen" else None,
            "target_installation_artifact_sha256": "a" * 64,
            "execution_readiness": {**alpha.execution_readiness.model_dump(),
                "host_provisioned": True, "instrumentation_validated": True,
                "target_artifact_verified": True, "target_metadata_verified": True}}
    approved = CampaignManifest.model_validate(data)
    assert approved.target_source_distribution == "proprietary"
    assert approved.target_repository_url_or_null is None
    with pytest.raises(ValidationError, match="artifact fingerprint"):
        CampaignManifest.model_validate({**data, "target_installation_artifact_sha256": None})
    for flag in ("target_artifact_verified", "target_metadata_verified", "instrumentation_validated", "host_provisioned"):
        with pytest.raises(ValidationError):
            CampaignManifest.model_validate({**data, "execution_readiness": {**data["execution_readiness"], flag: False}})


@pytest.mark.parametrize("field", ["target_name", "target_package_version", "target_algorithm_version",
                                   "target_threshold_profile", "target_bundle_protocol", "target_baseline_revision"])
def test_alpha_rejects_changed_target_contract(alpha, field):
    with pytest.raises(ValidationError, match="approved contract"):
        CampaignManifest.model_validate({**alpha.model_dump(), field: "wrong"})


@pytest.mark.parametrize("field, value", [("target_git_commit", "a" * 40),
    ("reproducibility_status", "target_unavailable"), ("target_artifact_path", "private/fixture.whl"),
    ("target_repository_url_or_null", "https://example.org/target")])
def test_public_contract_rejects_obsolete_or_private_provenance(alpha, field, value):
    with pytest.raises(ValidationError):
        CampaignManifest.model_validate({**alpha.model_dump(), field: value})


def test_retrieval_flag_is_removed(alpha):
    with pytest.raises(ValidationError, match="Extra inputs"):
        CampaignManifest.model_validate({**alpha.model_dump(), "execution_readiness": {
            **alpha.execution_readiness.model_dump(), "target_retrieval_verified": True}})


@pytest.mark.parametrize("value", ["", "a" * 63, "a" * 65, "A" * 64, "z" * 64, 123])
def test_artifact_fingerprint_rejects_non_sha256_values(alpha, value):
    with pytest.raises(ValidationError):
        CampaignManifest.model_validate({**alpha.model_dump(), "target_installation_artifact_sha256": value})


def test_report_and_registry_distinguish_public_method_from_proprietary_artifact(tmp_path, alpha, campaign, completed):
    report = campaign_report(campaign, aggregate(campaign.campaign_id, completed[0]))
    assert "TADR Core implementation is proprietary" in report
    assert "cannot rebuild the evaluated implementation from public source" in report
    assert campaign.target_installation_artifact_sha256 in report
    assert "neither the proprietary artifact nor its source code" in report
    index = results_index(tmp_path, [alpha])
    assert "Not run | Proprietary target; artifact pending | Not available" in index
    assert "PLANNED / NOT YET RUN" in index
    for name, text in [("REPORT.md", report), ("RESULTS.md", index), ("manifest.json", alpha.model_dump_json())]:
        (tmp_path / name).write_text(text, encoding="utf-8")
    assert scan_files(tmp_path, ["REPORT.md", "RESULTS.md", "manifest.json"]) == []
