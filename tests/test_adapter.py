from types import SimpleNamespace

import pytest

from tadr_benchmark.models import TargetMetadata
from tadr_benchmark.targets import tadr_core


@pytest.fixture
def installed_fixture(monkeypatch, campaign, tmp_path, private_wheel):
    (tmp_path / "tadr.py").write_text("# Synthetic target payload\n", encoding="utf-8")
    artifact, digest = private_wheel(tmp_path)
    target = TargetMetadata(**{**{f: getattr(campaign, f) for f in TargetMetadata.model_fields},
                               "target_installation_artifact_sha256": digest})
    public_model = SimpleNamespace(model_validate=lambda value: value)
    module = SimpleNamespace(__file__=str(tmp_path / "tadr.py"), __version__="0.1.0",
                             TaskIntent=public_model, DeploymentConstraints=public_model)
    monkeypatch.setattr(tadr_core.importlib, "import_module", lambda name: module)
    dist = SimpleNamespace(version="0.1.0", locate_file=lambda name: tmp_path / name)
    monkeypatch.setattr(tadr_core, "distribution", lambda name: dist)
    return tadr_core.TadrCoreAdapter(target, artifact), module, dist


def test_adapter_preserves_target_bytes_and_public_call(installed_fixture, tmp_path):
    adapter, module, _ = installed_fixture
    data = b'{"readiness_score":17,"findings":[]} '
    calls = []
    module.analyze = lambda **kw: calls.append(kw) or SimpleNamespace(canonical_bytes=lambda: data)
    report = adapter.analyze(tmp_path / "fixture.csv", {"task_type": "analytics"})
    assert report.canonical_bytes == data and report.data["readiness_score"] == 17
    assert calls == [{"data": tmp_path / "fixture.csv", "task": {"task_type": "analytics"}, "constraints": None}]
    module.analyze = lambda **kw: (_ for _ in ()).throw(RuntimeError("target failure"))
    with pytest.raises(RuntimeError, match="target failure"):
        adapter.analyze(tmp_path / "fixture.csv", {"task_type": "analytics"})


@pytest.mark.parametrize("change, message", [
    ("missing", "available installation artifact"), ("hash", "fingerprint"),
    ("payload", "payload differs"), ("metadata", "payload differs"),
    ("installed_version", "package version"), ("runtime_version", "public package version"),
    ("shadow", "shadows"), ("null_hash", "fingerprint")])
def test_artifact_and_installed_identity_fail_closed(installed_fixture, tmp_path, change, message):
    adapter, module, dist = installed_fixture
    if change == "missing":
        adapter.installation_artifact.unlink()
    elif change == "hash":
        adapter.installation_artifact.write_bytes(b"changed artifact")
    elif change == "payload":
        (tmp_path / "tadr.py").write_text("# changed payload\n")
    elif change == "metadata":
        (tmp_path / "tadr_core-0.1.0.dist-info/METADATA").write_text("changed metadata")
    elif change == "installed_version":
        dist.version = "0.2.0"
    elif change == "runtime_version":
        module.__version__ = "0.2.0"
    elif change == "shadow":
        module.__file__ = str(tmp_path / "shadow/tadr.py")
    else:
        adapter.expected = adapter.expected.model_copy(update={"target_installation_artifact_sha256": None})
    with pytest.raises(ValueError, match=message):
        adapter.metadata()


def test_ignored_configuration_and_verification_retain_only_public_metadata(installed_fixture, tmp_path):
    adapter, _, _ = installed_fixture
    path = tmp_path / "benchmark.local.toml"
    path.write_text('[target]\ninstallation_artifact = "fixture.whl"\n', encoding="utf-8")
    configured = tadr_core.TadrCoreAdapter.from_local_config(adapter.expected, tmp_path)
    assert configured.metadata() == adapter.expected
    assert configured.installation_artifact == adapter.installation_artifact.resolve()
    assert str(tmp_path) not in configured.metadata().model_dump_json()
    assert "fixture.whl" not in configured.metadata().model_dump_json()
    path.write_text('[target]\ncheckout = "example"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="local configuration"):
        tadr_core.TadrCoreAdapter.from_local_config(adapter.expected, tmp_path)


def test_package_wheel_inventory_is_verified(installed_fixture, tmp_path, private_wheel):
    adapter, module, _ = installed_fixture
    (tmp_path / "tadr.py").unlink()
    package = tmp_path / "tadr"
    package.mkdir()
    (package / "__init__.py").write_text("# Synthetic package facade\n")
    (package / "api.py").write_text("# Synthetic public API\n")
    artifact, digest = private_wheel(tmp_path)
    adapter.expected = adapter.expected.model_copy(update={"target_installation_artifact_sha256": digest})
    adapter.installation_artifact = artifact
    module.__file__ = str(package / "__init__.py")
    assert adapter.metadata() == adapter.expected
    (package / "unreviewed.py").write_text("# Not in the selected artifact\n")
    with pytest.raises(ValueError, match="inventory differs"):
        adapter.metadata()
    (package / "unreviewed.py").unlink()
    (package / "api.py").unlink()
    with pytest.raises(ValueError, match="payload differs"):
        adapter.metadata()


@pytest.mark.parametrize("change, message", [("name", "package metadata"),
    ("version", "package metadata"), ("layout", "wheel layout"), ("traversal", "wheel inventory")])
def test_even_fingerprinted_artifacts_require_valid_package_metadata_and_layout(installed_fixture, change, message):
    from hashlib import sha256
    from zipfile import ZipFile
    adapter, _, _ = installed_fixture
    artifact = adapter.installation_artifact
    with ZipFile(artifact) as wheel:
        entries = {n: wheel.read(n) for n in wheel.namelist()}
    metadata = "tadr_core-0.1.0.dist-info/METADATA"
    if change == "name":
        entries[metadata] = entries[metadata].replace(b"tadr-core", b"other-target")
    elif change == "version":
        entries[metadata] = entries[metadata].replace(b"0.1.0", b"0.2.0")
    else:
        entries["extra.py" if change == "layout" else "tadr/../extra.py"] = b"# fixture"
    with ZipFile(artifact, "w") as wheel:
        for name, content in entries.items():
            wheel.writestr(name, content)
    adapter.expected = adapter.expected.model_copy(update={
        "target_installation_artifact_sha256": sha256(artifact.read_bytes()).hexdigest()})
    with pytest.raises(ValueError, match=message):
        adapter.metadata()
