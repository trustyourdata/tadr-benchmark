import json
from types import SimpleNamespace

import pytest

from tadr_benchmark.models import TargetMetadata
from tadr_benchmark.targets import tadr_core


def test_adapter_preserves_target_bytes_and_public_call(monkeypatch, campaign, tmp_path):
    target = TargetMetadata(**{field: getattr(campaign, field) for field in TargetMetadata.model_fields})
    data = b'{"readiness_score":17,"findings":[]} '
    calls = []
    public_model = SimpleNamespace(model_validate=lambda value: value)
    module = SimpleNamespace(TaskIntent=public_model, DeploymentConstraints=public_model,
                             analyze=lambda **kwargs: calls.append(kwargs) or SimpleNamespace(canonical_bytes=lambda: data))
    monkeypatch.setattr(tadr_core.importlib, "import_module", lambda name: module)
    dist = SimpleNamespace(version=target.target_package_version,
                           read_text=lambda name: json.dumps({"vcs_info": {"commit_id": target.target_git_commit}}))
    monkeypatch.setattr(tadr_core, "distribution", lambda name: dist)
    adapter = tadr_core.TadrCoreAdapter(target)
    report = adapter.analyze(tmp_path / "fixture.csv", {"task_type": "analytics"})
    assert report.canonical_bytes == data
    assert report.data["readiness_score"] == 17
    assert calls[0]["constraints"] is None
    module.analyze = lambda **kwargs: (_ for _ in ()).throw(RuntimeError("target failure"))
    with pytest.raises(RuntimeError, match="target failure"):
        adapter.analyze(tmp_path / "fixture.csv", {"task_type": "analytics"})


def test_adapter_rejects_unverifiable_installation(monkeypatch, campaign):
    target = TargetMetadata(**{field: getattr(campaign, field) for field in TargetMetadata.model_fields})
    monkeypatch.setattr(tadr_core, "distribution", lambda name: SimpleNamespace(version="0.1.0", read_text=lambda name: None))
    with pytest.raises(ValueError, match="revision"):
        tadr_core.TadrCoreAdapter(target).metadata()


def test_ignored_developer_configuration_does_not_enter_metadata(tmp_path, campaign):
    target = TargetMetadata(**{field: getattr(campaign, field) for field in TargetMetadata.model_fields})
    path = tmp_path / "benchmark.local.toml"
    path.write_text('[target]\ncheckout = "../target-checkout"\n', encoding="utf-8")
    adapter = tadr_core.TadrCoreAdapter.from_local_config(target, tmp_path)
    assert adapter.local_checkout == (tmp_path.parent / "target-checkout").resolve()
    assert "checkout" not in adapter.expected.model_dump_json()
    path.write_text('[target]\ncheckout = "example"\nextra = true\n', encoding="utf-8")
    with pytest.raises(ValueError, match="local configuration"):
        tadr_core.TadrCoreAdapter.from_local_config(target, tmp_path)
