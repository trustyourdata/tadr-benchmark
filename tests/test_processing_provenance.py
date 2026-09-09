import pytest

from tadr_benchmark.campaigns import processing
from tadr_benchmark.serialization import canonical_bytes, sha256


def test_processing_revision_does_not_replace_execution(campaign, environment, monkeypatch, tmp_path):
    monkeypatch.setattr(processing, "require_clean_revision", lambda _: "c"*40)
    original = canonical_bytes(campaign)
    binding = canonical_bytes({"manifest": campaign.model_dump(mode="json")})
    attempts = b"synthetic immutable attempt bytes\n"
    result = processing.processing_provenance(tmp_path, campaign, binding, attempts, environment)
    assert result.execution_git_commit == "b"*40
    assert result.processing_git_commit == "c"*40
    assert result.execution_binding_sha256 == sha256(binding)
    assert result.attempts_sha256 == sha256(attempts)
    assert canonical_bytes(campaign) == original
    changed = canonical_bytes({"manifest": {**campaign.model_dump(mode="json"), "benchmark_git_commit": "c"*40}})
    with pytest.raises(ValueError, match="binding differs"):
        processing.processing_provenance(tmp_path, campaign, changed, attempts, environment)


def test_dirty_processing_revision_is_not_recorded(campaign, environment, monkeypatch, tmp_path):
    def dirty(_):
        raise ValueError("benchmark working tree must be clean")
    monkeypatch.setattr(processing, "require_clean_revision", dirty)
    with pytest.raises(ValueError, match="clean"):
        processing.processing_provenance(tmp_path, campaign,
            canonical_bytes({"manifest": campaign.model_dump(mode="json")}), b"", environment)
