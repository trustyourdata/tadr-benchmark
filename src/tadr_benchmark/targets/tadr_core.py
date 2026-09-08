"""Adapter using only the installed tadr public analysis/report API."""

import importlib
import json
import subprocess
import tomllib
from importlib.metadata import distribution
from pathlib import Path

from ..models import TargetMetadata
from .base import TargetReport


class TadrCoreAdapter:
    def __init__(self, expected: TargetMetadata, local_checkout: Path | None = None):
        self.expected = expected
        self.local_checkout = local_checkout

    @classmethod
    def from_local_config(cls, expected: TargetMetadata, repository: Path):
        """Read only the ignored benchmark.local.toml developer configuration."""
        config = tomllib.loads((repository / "benchmark.local.toml").read_text(encoding="utf-8"))
        target = config.get("target")
        if (set(config) != {"target"} or not isinstance(target, dict) or set(target) != {"checkout"}
                or not isinstance(target["checkout"], str) or not target["checkout"]):
            raise ValueError("local configuration requires only target.checkout")
        checkout = Path(target["checkout"]).expanduser()
        if not checkout.is_absolute():
            checkout = repository / checkout
        return cls(expected, local_checkout=checkout.resolve())

    def metadata(self) -> TargetMetadata:
        installed = distribution("tadr-core")
        if installed.version != self.expected.target_package_version:
            raise ValueError("installed target package version differs from pin")
        if self.expected.target_git_commit is None:
            raise ValueError("target adapter requires an exact Git revision")
        if self.local_checkout is not None:
            checkout = self.local_checkout.resolve()
            module = importlib.import_module("tadr")
            if not Path(module.__file__).resolve().is_relative_to(checkout / "src"):
                raise ValueError("imported target is not the configured local checkout")
            revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=checkout,
                                      check=True, capture_output=True, text=True).stdout.strip()
            dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                                   cwd=checkout, check=True, capture_output=True, text=True).stdout
            if dirty:
                raise ValueError("target checkout must be clean")
        else:
            direct = json.loads(installed.read_text("direct_url.json") or "{}")
            revision = direct.get("vcs_info", {}).get("commit_id")
        if revision != self.expected.target_git_commit:
            raise ValueError("installed target Git revision is absent or differs from pin")
        # Algorithm/profile/bundle/baseline are reviewed provenance for this exact
        # revision, not inferred by importing target implementation constants.
        return self.expected

    def analyze(self, dataset_path: Path, task: dict,
                constraints: dict | None = None) -> TargetReport:
        self.metadata()
        tadr = importlib.import_module("tadr")
        intent = tadr.TaskIntent.model_validate(task)
        limits = None if constraints is None else tadr.DeploymentConstraints.model_validate(constraints)
        report = tadr.analyze(data=dataset_path, task=intent, constraints=limits)
        original = report.canonical_bytes()
        return TargetReport(canonical_bytes=original, data=json.loads(original))
