"""Adapter using only the installed tadr public analysis/report API."""

import importlib
import json
import tomllib
from dataclasses import dataclass
from email.parser import BytesParser
from hashlib import file_digest
from importlib.metadata import distribution
from pathlib import Path, PurePosixPath
from zipfile import ZipFile

from ..models import TargetMetadata
from .base import TargetReport


@dataclass(frozen=True)
class PreparedAnalysis:
    public_api: object
    dataset_path: Path
    intent: object
    constraints: object

    def invoke(self):
        """Exactly the public call; preparation and canonical encoding are outside."""
        return self.public_api.analyze(data=self.dataset_path, task=self.intent, constraints=self.constraints)


class TadrCoreAdapter:
    def __init__(self, expected: TargetMetadata, installation_artifact: Path | None = None):
        self.expected = expected
        self.installation_artifact = installation_artifact

    @classmethod
    def from_local_config(cls, expected: TargetMetadata, repository: Path):
        """Read only the ignored benchmark.local.toml developer configuration."""
        config = tomllib.loads((repository / "benchmark.local.toml").read_text(encoding="utf-8"))
        target = config.get("target")
        if (set(config) != {"target"} or not isinstance(target, dict) or set(target) != {"installation_artifact"}
                or not isinstance(target["installation_artifact"], str) or not target["installation_artifact"]):
            raise ValueError("local configuration requires only target.installation_artifact")
        artifact = Path(target["installation_artifact"]).expanduser()
        if not artifact.is_absolute():
            artifact = repository / artifact
        return cls(expected, installation_artifact=artifact.resolve())

    def metadata(self) -> TargetMetadata:
        """Verify a private wheel and installed payload without source-retrieval claims.

        Algorithm/profile/bundle/baseline remain reviewed release declarations:
        they are not all exposed by the public facade. The READY review binds
        those declarations to this hash; the adapter checks bytes and public
        package/runtime identity before the analysis timing barrier.
        """
        artifact = self.installation_artifact
        if not self.expected.target_installation_artifact_sha256 or artifact is None or not artifact.is_file():
            raise ValueError("target requires an available installation artifact and fingerprint")
        installed = distribution("tadr-core")
        if installed.version != self.expected.target_package_version:
            raise ValueError("installed target package version differs from pin")
        root = Path(installed.locate_file("")).resolve()
        with artifact.open("rb") as stream:
            if file_digest(stream, "sha256").hexdigest() != self.expected.target_installation_artifact_sha256:
                raise ValueError("target installation artifact fingerprint differs from pin")
            stream.seek(0)
            with ZipFile(stream) as wheel:
                names = [i.filename for i in wheel.infolist() if not i.is_dir()]
                if len(names) != len(set(names)) or any(
                        PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts or "\\" in n or ":" in n
                        for n in names):
                    raise ValueError("invalid target wheel inventory")
                metadata = [n for n in names if n.endswith(".dist-info/METADATA")]
                payload = [n for n in names if n.startswith("tadr/") or n == "tadr.py"]
                if len(metadata) != 1 or not payload or any(
                        not (n in payload or n.startswith(metadata[0].rsplit("/", 1)[0] + "/")) for n in names):
                    raise ValueError("unsupported target wheel layout")
                info = BytesParser().parsebytes(wheel.read(metadata[0]))
                if (info["Name"], info["Version"]) != (self.expected.target_name, self.expected.target_package_version):
                    raise ValueError("artifact package metadata differs from pin")
                for name in payload + metadata:
                    path = (root / name).resolve()
                    if (not path.is_relative_to(root) or not path.is_file()
                            or path.read_bytes() != wheel.read(name)):
                        raise ValueError("installed target payload differs from artifact")
                if (root / "tadr").is_dir():
                    actual = {p.relative_to(root).as_posix() for p in (root / "tadr").rglob("*")
                              if p.is_file() and "__pycache__" not in p.parts}
                    if actual != set(payload):
                        raise ValueError("installed target payload inventory differs from artifact")
        module = importlib.import_module("tadr")
        if Path(module.__file__).resolve() not in {root / n for n in payload if n in {"tadr.py", "tadr/__init__.py"}}:
            raise ValueError("imported target shadows the verified installed distribution")
        if getattr(module, "__version__", None) != self.expected.target_package_version:
            raise ValueError("public package version differs from target pin")
        return self.expected

    def analyze(self, dataset_path: Path, task: dict,
                constraints: dict | None = None) -> TargetReport:
        prepared = self.prepare(dataset_path, task, constraints)
        report = prepared.invoke()
        original = report.canonical_bytes()
        return TargetReport(canonical_bytes=original, data=json.loads(original))

    def prepare(self, dataset_path: Path, task: dict,
                constraints: dict | None = None) -> PreparedAnalysis:
        self.metadata()
        tadr = importlib.import_module("tadr")
        intent = tadr.TaskIntent.model_validate(task)
        limits = None if constraints is None else tadr.DeploymentConstraints.model_validate(constraints)
        return PreparedAnalysis(tadr, dataset_path, intent, limits)
