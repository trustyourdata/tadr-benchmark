import pytest
from pydantic import ValidationError

from tadr_benchmark.instrumentation import environment as capture
from tadr_benchmark.models import EnvironmentInfo
from tadr_benchmark.paths import campaign_directory, contained, safe_relative
from tadr_benchmark.safety import scan_files, text_issues


@pytest.mark.parametrize("value", ["C:" + "/" + "Users/example/data", "/" + "home/example/data",
                                  "ghp_" + "a" * 30, "password=" + "a" * 20,
                                  ".".join(["192", "168", "1", "2"]),
                                  ":".join(["ab"] * 6), "N" + "IW"])
def test_detects_public_text_leakage(value):
    assert text_issues(value)


def test_scanner_covers_sensitive_filenames_and_binary(tmp_path):
    (tmp_path / ".env").write_text("plain", encoding="utf-8")
    (tmp_path / "data.bin").write_bytes(b"\x00\xff")
    issues = scan_files(tmp_path, [".env", "data.bin"])
    assert len(issues) == 2


def test_environment_rejects_unknown_and_unsafe_fields(environment):
    with pytest.raises(ValidationError):
        EnvironmentInfo.model_validate({**environment.model_dump(), "hostname": "example"})
    with pytest.raises(ValidationError):
        EnvironmentInfo.model_validate({**environment.model_dump(), "cpu_model": "C:" + "/" + "Users/example"})


def test_capture_omits_untrusted_platform_strings(monkeypatch):
    monkeypatch.setattr(capture.platform, "release", lambda: "6.8.0-build-host-private")
    monkeypatch.setattr(capture.platform, "machine", lambda: "untrusted-machine")
    monkeypatch.setattr(capture.platform, "processor", lambda: pytest.fail("must not read arbitrary CPU text"))
    monkeypatch.setattr(capture.platform, "node", lambda: pytest.fail("must not read hostname"))
    env = capture.capture_environment()
    assert env.os_version == "6.8.0"
    assert env.architecture == "other"
    assert env.cpu_model is None
    assert "private" not in env.model_dump_json()


@pytest.mark.parametrize("value", ["../escape", "/absolute", "a/../b", "a\\b", "a//b", "a/./b", "C:" + "/a"])
def test_paths_reject_escape(value):
    with pytest.raises(ValueError):
        safe_relative(value)


def test_result_directory_conventions(tmp_path):
    assert campaign_directory(tmp_path, "ALPHA_BENCHMARK_V1") == tmp_path / "results/campaigns/alpha_benchmark_v1"
    assert contained(tmp_path, ".work/datasets/fixture.csv").is_relative_to(tmp_path)
    with pytest.raises(ValueError):
        campaign_directory(tmp_path, "../escape")
