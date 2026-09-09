"""Complete, target-free publication assembly with three provenance roles."""

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator

from ..companions import (DatasetIdentity, DiagnosticRecord, InstrumentationRecord,
                          RunFailure, ScenarioExpectations)
from ..execution.attempts import AttemptRecord, validate_attempts
from ..instrumentation.environment import capture_environment
from ..models import (CampaignManifest, CampaignSummary, Commit, Contract, Digest,
                      EnvironmentInfo, RunResult, ScenarioSpec)
from ..paths import campaign_directory, contained, safe_relative
from ..reporting.aggregate import aggregate
from ..reporting.markdown import campaign_report
from ..reporting.plots import build_figures
from ..reporting.protocol import protocol_bytes
from ..reporting.queries import ReportInputs, TABLE_COLUMNS, csv_bytes, table_rows
from ..reporting.tables import summary_csv
from ..safety import repository_issues, scan_files
from ..serialization import canonical_bytes, sha256
from ..validation import planned_runs, validate_completed, validate_historical_scenarios
from .companions import validate_companions
from .processing import ProcessingProvenance


HISTORY = {
    "manifest.json": "history/ready_manifest.json",
    "REPORT.md": "history/candidate_REPORT.md",
    "checksums.sha256": "history/candidate_checksums.sha256",
}
SCIENTIFIC_REVIEW = "history/ALPHA_BENCHMARK_V1_SCIENTIFIC_RESULT_REVIEW.md"
PUBLICATION_FILES = {
    "manifest.json", "REPORT.md", "checksums.sha256", SCIENTIFIC_REVIEW,
    "publication_provenance.json", "publication_inventory.json",
    "ADJUDICATION_REPRODUCTION.md",
}
ALPHA_CANDIDATE_CHECKSUM = "6bfde18953a2a822218f1ad31f3e007ad809526e188374daf2b8ddc6daf1d498"
ALPHA_ADJUDICATION_CHECKSUM = "902b999c831170161836dca353e6031bab19f1fcdbfa6c2dce75d76ddcbbb4e4"


def require(condition, message):
    if not condition:
        raise ValueError(message)


class PublicationProvenance(Contract):
    publication_provenance_version: Literal["1.0"] = "1.0"
    state: Literal["staged", "frozen"]
    scientific_execution_revision: Commit
    historical_processing_revision: Commit
    publication_assembly_revision: Commit | None
    target_installation_artifact_sha256: Digest
    original_candidate_checksums_sha256: Digest
    adjudication_checksums_sha256: Digest
    scientific_review_sha256: Digest
    execution_provenance_sha256: Digest
    processing_provenance_sha256: Digest
    publication_environment: EnvironmentInfo
    generator_files: dict[str, Digest]
    generator_identity_sha256: Digest

    @field_validator("generator_files")
    @classmethod
    def safe_generator_names(cls, value):
        require(bool(value), "publication generator inventory is empty")
        for name in value:
            safe_relative(name)
        return value

    @model_validator(mode="after")
    def role_bindings(self):
        require((self.publication_assembly_revision is None) == (self.state == "staged"),
                "only a staged publication may have an unresolved assembly revision")
        require(self.generator_identity_sha256 == sha256(canonical_bytes(self.generator_files)),
                "publication generator identity mismatch")
        return self


class PublicationEntry(Contract):
    path: str
    classification: Literal["AUTHORITATIVE", "DERIVED", "SUPPLEMENTAL ADJUDICATION"]

    @field_validator("path")
    @classmethod
    def safe_name(cls, value):
        safe_relative(value)
        return value


class PublicationInventory(Contract):
    publication_inventory_version: Literal["1.0"] = "1.0"
    entries: list[PublicationEntry]
    original_candidate_mapping: dict[str, str]

    @model_validator(mode="after")
    def exact_paths(self):
        names = [entry.path for entry in self.entries]
        require(names == sorted(set(names)), "publication inventory paths must be unique and sorted")
        for source, destination in self.original_candidate_mapping.items():
            safe_relative(source)
            safe_relative(destination)
        require(len(set(self.original_candidate_mapping.values())) == len(self.original_candidate_mapping),
                "original candidate mapping is not one-to-one")
        return self


@dataclass(frozen=True)
class PublicationSources:
    """Private operator locations, never serialized into public provenance."""
    candidate: Path
    adjudication: Path
    scientific_review: Path


@dataclass
class OriginalEvidence:
    artifacts: dict[str, bytes]
    inputs: ReportInputs
    environments: dict[str, EnvironmentInfo]
    instrumentation: list[InstrumentationRecord]
    datasets: list[DatasetIdentity]
    processing: ProcessingProvenance
    summary: CampaignSummary
    tables: dict[str, list[dict]]
    figures: dict[str, bytes]


def checksum_bytes(artifacts: dict[str, bytes]) -> bytes:
    return "".join(f"{sha256(raw)}  {name}\n" for name, raw in sorted(artifacts.items())
                   if name != "checksums.sha256").encode("utf-8")


def verify_checksums(artifacts: dict[str, bytes]) -> None:
    require("checksums.sha256" in artifacts, "missing checksum manifest")
    expected = {}
    for line in artifacts["checksums.sha256"].decode("utf-8").splitlines():
        parts = line.split("  ", 1)
        require(len(parts) == 2, "malformed checksum entry")
        digest, name = parts
        safe_relative(name)
        require(name not in expected and name != "checksums.sha256",
                "duplicate or recursive checksum entry")
        require(name in artifacts and sha256(artifacts[name]) == digest,
                "publication artifact checksum mismatch")
        expected[name] = digest
    require(set(artifacts) == set(expected) | {"checksums.sha256"},
            "unchecksummed or missing publication artifact")


def read_artifacts(directory: Path) -> dict[str, bytes]:
    require(directory.is_dir() and not directory.is_symlink(), "unsafe publication directory")
    paths = sorted(directory.rglob("*"))
    require(not any(p.is_symlink() for p in paths), "publication symlinks are forbidden")
    names = [p.relative_to(directory).as_posix() for p in paths if p.is_file()]
    require(not scan_files(directory, names), "publication public-safety scan failed")
    result = {name: contained(directory, name).read_bytes() for name in names}
    verify_checksums(result)
    return result


def original_evidence(artifacts: dict[str, bytes]) -> OriginalEvidence:
    """Validate originals without interpreting new publication fields as execution."""
    from .freeze import validate_observation_bindings, validate_reports

    verify_checksums(artifacts)
    def read(name):
        return json.loads(artifacts[name])
    def lines(name, model):
        return [model.model_validate_json(line) for line in artifacts[name].splitlines()]

    manifest = CampaignManifest.model_validate(read("manifest.json"))
    require(manifest.status == "ready" and manifest.benchmark_git_commit is not None,
            "original candidate requires a resolved READY execution manifest")
    if manifest.campaign_id == "ALPHA_BENCHMARK_V1":
        require(len(artifacts) == 1062 and sha256(artifacts["checksums.sha256"]) == ALPHA_CANDIDATE_CHECKSUM,
                "approved original Alpha candidate changed")
    scenarios = [ScenarioSpec.model_validate_json(raw) for name, raw in sorted(artifacts.items())
                 if name.startswith("scenarios/")]
    runs, failures = lines("runs.jsonl", RunResult), lines("failures.jsonl", RunFailure)
    attempts = lines("attempts.jsonl", AttemptRecord)
    expectations = [ScenarioExpectations.model_validate(v) for v in read("expectations.json")]
    datasets = [DatasetIdentity.model_validate(v) for v in read("dataset_manifest.json")]
    instrumentation = lines("instrumentation.jsonl", InstrumentationRecord)
    diagnostics = [DiagnosticRecord.model_validate_json(raw) for name, raw in sorted(artifacts.items())
                   if name.startswith("diagnostics/")]
    reports = {Path(name).stem: raw for name, raw in artifacts.items() if name.startswith("reports/")}
    environments = {key: EnvironmentInfo.model_validate(v) for key, v in read("environment.json").items()}
    processing = ProcessingProvenance.model_validate(read("processing_provenance.json"))
    binding = read("execution_provenance.json")
    require(binding["manifest"] == manifest.model_dump(mode="json"), "execution manifest binding mismatch")
    require(processing.execution_git_commit == manifest.benchmark_git_commit,
            "processing record changed the execution revision")
    require(processing.execution_binding_sha256 == sha256(artifacts["execution_provenance.json"])
            and processing.attempts_sha256 == sha256(artifacts["attempts.jsonl"]),
            "historical processing evidence binding mismatch")
    require(binding["environment"] in [e.model_dump(mode="json") for e in environments.values()],
            "execution environment binding mismatch")
    validate_completed(manifest, scenarios, runs, environments, failures)
    validate_companions(manifest, scenarios, runs, failures, expectations, datasets, instrumentation, diagnostics)
    validate_attempts(planned_runs(manifest, scenarios), attempts, runs, failures)
    validate_reports(runs, reports)
    validate_observation_bindings(attempts, instrumentation, diagnostics, reports)
    require(artifacts["run_specs.json"] == canonical_bytes(
        [s.model_dump(mode="json") for s in planned_runs(manifest, scenarios)]), "original RunSpec plan mismatch")
    summary = aggregate(manifest.campaign_id, runs, failures, attempts)
    require(summary == CampaignSummary.model_validate(read("summary.json")), "original aggregate mismatch")
    require(artifacts["tables/summary.csv"] == summary_csv(summary).encode("utf-8"), "original summary table mismatch")
    inputs = ReportInputs(manifest, scenarios, runs, failures, reports, attempts, expectations, diagnostics)
    tables = table_rows(inputs)
    figures = build_figures(tables, attempts=attempts)
    for name, data in tables.items():
        require(artifacts.get("tables/" + name) == csv_bytes(TABLE_COLUMNS[name], data),
                "original derived table is stale")
    for name, data in figures.items():
        require(artifacts.get("figures/" + name) == data, "original derived figure is stale")
    require(artifacts["protocol.md"] == protocol_bytes(manifest), "original protocol mismatch")
    # Preserve the historical generator and candidate-only banner verbatim.
    report_body = artifacts["REPORT.md"].decode("utf-8")
    if report_body.startswith("CANDIDATE FOR REVIEW"):
        report_body = report_body.split("\n\n", 1)[1]
    require(report_body == campaign_report(manifest, summary, tables=tables, figures=figures),
            "historical candidate report is stale")
    expected = {
        "manifest.json", "environment.json", "execution_provenance.json", "processing_provenance.json",
        "summary.json", "runs.jsonl", "attempts.jsonl", "failures.jsonl", "expectations.json",
        "dataset_manifest.json", "instrumentation.jsonl", "run_specs.json", "tables/summary.csv",
        "protocol.md", "REPORT.md", "checksums.sha256",
        *(f"scenarios/{s.scenario_id}.json" for s in scenarios),
        *(f"reports/{r.run_id}.json" for r in runs),
        *(f"diagnostics/{d.primary_run_id}.json" for d in diagnostics),
        *("tables/" + name for name in tables), *("figures/" + name for name in figures),
    }
    require(set(artifacts) == expected, "original candidate inventory mismatch")
    return OriginalEvidence(artifacts, inputs, environments, instrumentation, datasets, processing,
                            summary, tables, figures)


def generator_files() -> dict[str, str]:
    """Identify shipped benchmark code, including uncommitted staging changes."""
    package = Path(__file__).parents[1]
    return {"src/tadr_benchmark/" + path.relative_to(package).as_posix(): sha256(path.read_bytes())
            for path in sorted(package.rglob("*.py"))}


def require_publication_code(root: Path) -> None:
    """The clean publication checkout must contain the code doing assembly."""
    tracked = subprocess.run(
        ["git", "ls-files", "-z", "--", "src/tadr_benchmark"], cwd=root,
        check=True, capture_output=True, text=True).stdout.split("\0")
    files = {name: sha256(contained(root, name).read_bytes())
             for name in tracked if name.endswith(".py")}
    require(files == generator_files(), "assembly code differs from the clean publication checkout")


def publication_inventory(original, bundle) -> PublicationInventory:
    mapping = {name: HISTORY.get(name, name) for name in sorted(original)}
    names = set(mapping.values()) | PUBLICATION_FILES | {"adjudication_v1/" + name for name in bundle}
    def kind(name):
        if name.startswith("adjudication_v1/") or name == "ADJUDICATION_REPRODUCTION.md":
            return "SUPPLEMENTAL ADJUDICATION"
        if name.startswith(("tables/", "figures/")) or name in {
                "REPORT.md", "summary.json", "history/candidate_REPORT.md", SCIENTIFIC_REVIEW}:
            return "DERIVED"
        return "AUTHORITATIVE"
    return PublicationInventory(entries=[PublicationEntry(path=name, classification=kind(name))
                                         for name in sorted(names)], original_candidate_mapping=mapping)


def _assemble(root: Path, sources: PublicationSources, *, frozen_date: str | None,
              publication_revision: str | None) -> dict[str, bytes]:
    from .adjudication import verify_adjudication
    from ..reporting.publication import adjudication_reproduction, publication_report

    original = read_artifacts(sources.candidate)
    bundle = read_artifacts(sources.adjudication)
    evidence = original_evidence(original)
    validate_historical_scenarios(root, evidence.inputs.scenarios)
    review = sources.scientific_review.read_bytes()
    require(not sources.scientific_review.is_symlink(), "scientific review cannot be a symlink")
    require(not scan_files(sources.scientific_review.parent, [sources.scientific_review.name]),
            "scientific review public-safety scan failed")
    adjudication = verify_adjudication(evidence, bundle, review)
    source_manifest = evidence.inputs.manifest
    frozen = publication_revision is not None
    require(frozen == (frozen_date is not None), "publication date and revision must resolve together")
    manifest = CampaignManifest.model_validate({**source_manifest.model_dump(),
        "status": "frozen" if frozen else "ready", "frozen_date": frozen_date})
    generators = generator_files()
    provenance = PublicationProvenance(
        state="frozen" if frozen else "staged",
        scientific_execution_revision=source_manifest.benchmark_git_commit,
        historical_processing_revision=evidence.processing.processing_git_commit,
        publication_assembly_revision=publication_revision,
        target_installation_artifact_sha256=source_manifest.target_installation_artifact_sha256,
        original_candidate_checksums_sha256=sha256(original["checksums.sha256"]),
        adjudication_checksums_sha256=sha256(bundle["checksums.sha256"]),
        scientific_review_sha256=sha256(review),
        execution_provenance_sha256=sha256(original["execution_provenance.json"]),
        processing_provenance_sha256=sha256(original["processing_provenance.json"]),
        publication_environment=capture_environment(), generator_files=generators,
        generator_identity_sha256=sha256(canonical_bytes(generators)))
    inventory = publication_inventory(original, bundle)
    artifacts = {HISTORY.get(name, name): raw for name, raw in original.items()}
    artifacts.update({"adjudication_v1/" + name: raw for name, raw in bundle.items()})
    artifacts.update({
        "manifest.json": canonical_bytes(manifest),
        SCIENTIFIC_REVIEW: review,
        "publication_provenance.json": canonical_bytes(provenance),
        "publication_inventory.json": canonical_bytes(inventory),
        "REPORT.md": publication_report(evidence, adjudication, provenance, manifest).encode("utf-8"),
        "ADJUDICATION_REPRODUCTION.md": adjudication_reproduction(bundle).encode("utf-8"),
    })
    artifacts["checksums.sha256"] = checksum_bytes(artifacts)
    require(set(artifacts) == {e.path for e in inventory.entries}, "assembled publication inventory mismatch")
    return artifacts


def _write_stage(destination: Path, artifacts: dict[str, bytes]) -> None:
    require(not destination.exists(), "publication staging destination already exists")
    destination.mkdir(parents=True)
    for name, raw in sorted(artifacts.items()):
        path = contained(destination, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)


def stage_publication(root: Path, sources: PublicationSources, destination: Path) -> Path:
    """Dry-run only: unresolved publication revision/date, never a frozen campaign."""
    root = root.resolve()
    destination = destination.resolve()
    require(destination.is_relative_to(root / ".work"), "dry-run stage must remain under ignored .work")
    require(not destination.is_relative_to(sources.candidate.resolve())
            and not destination.is_relative_to(sources.adjudication.resolve()),
            "stage cannot modify original evidence")
    artifacts = _assemble(root, sources, frozen_date=None, publication_revision=None)
    _write_stage(destination, artifacts)
    verify_publication(destination, check_directory_name=False, allow_staged=True)
    return destination


def freeze_publication(root: Path, sources: PublicationSources, frozen_date: str, *,
                       public_reviewed: bool) -> Path:
    """Create one immutable complete release; target imports/execution are unnecessary."""
    from .freeze import require_clean_revision

    require(public_reviewed, "publication review must be explicitly recorded before freeze")
    publication_revision = require_clean_revision(root)
    require_publication_code(root)
    require(not repository_issues(root, include_untracked=True), "repository public-safety scan failed")
    artifacts = _assemble(root, sources, frozen_date=frozen_date, publication_revision=publication_revision)
    manifest = CampaignManifest.model_validate_json(artifacts["manifest.json"])
    destination = campaign_directory(root, manifest.campaign_id)
    require(not destination.exists(), "frozen campaign directory already exists")
    work = contained(root, ".work/freeze")
    work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=work) as temporary:
        stage = Path(temporary) / "campaign"
        _write_stage(stage, artifacts)
        verify_publication(stage, check_directory_name=False)
        require_clean_revision(root, publication_revision)
        require(generator_files() == json.loads(artifacts["publication_provenance.json"])["generator_files"],
                "publication generator changed during assembly")
        require(not destination.exists(), "frozen destination appeared during validation")
        destination.parent.mkdir(parents=True, exist_ok=True)
        stage.rename(destination)
    return destination


def verify_publication(directory: Path, *, check_directory_name: bool = True,
                       allow_staged: bool = False) -> tuple[CampaignManifest, CampaignSummary]:
    from .adjudication import verify_adjudication
    from ..reporting.publication import adjudication_reproduction, publication_report

    artifacts = read_artifacts(directory)
    provenance = PublicationProvenance.model_validate_json(artifacts["publication_provenance.json"])
    require(provenance.state == "frozen" or allow_staged, "publication assembly revision is unresolved")
    manifest = CampaignManifest.model_validate_json(artifacts["manifest.json"])
    require(manifest.status == ("ready" if provenance.state == "staged" else "frozen"),
            "publication lifecycle mismatch")
    if check_directory_name:
        require(directory.name == manifest.campaign_id.lower(), "campaign directory identity mismatch")
    inventory = PublicationInventory.model_validate_json(artifacts["publication_inventory.json"])
    require(set(artifacts) == {e.path for e in inventory.entries}, "publication inventory mismatch")
    require(PUBLICATION_FILES | set(HISTORY.values()) <= set(artifacts),
            "publication or historical companion is missing")
    # Derive the archive mapping ourselves, never trust a supplied mapping to hide evidence.
    historical_checksums = artifacts[HISTORY["checksums.sha256"]].decode("utf-8").splitlines()
    require(all(len(line.split("  ", 1)) == 2 for line in historical_checksums),
            "malformed historical checksum entry")
    original_names = [line.split("  ", 1)[1] for line in historical_checksums] + ["checksums.sha256"]
    require(all(HISTORY.get(name, name) in artifacts for name in original_names),
            "historical candidate artifact is missing")
    original = {name: artifacts[HISTORY.get(name, name)] for name in original_names}
    evidence = original_evidence(original)
    bundle = {name.removeprefix("adjudication_v1/"): raw for name, raw in artifacts.items()
              if name.startswith("adjudication_v1/")}
    require("checksums.sha256" in bundle, "adjudication inner checksums are missing")
    require(inventory == publication_inventory(original, bundle), "publication inventory classification or mapping mismatch")
    source_manifest = evidence.inputs.manifest
    require({**manifest.model_dump(), "status": "ready", "frozen_date": None} == source_manifest.model_dump(),
            "frozen manifest changed scientific execution fields")
    require(provenance.scientific_execution_revision == source_manifest.benchmark_git_commit
            and provenance.historical_processing_revision == evidence.processing.processing_git_commit
            and provenance.target_installation_artifact_sha256 == source_manifest.target_installation_artifact_sha256,
            "publication provenance role mismatch")
    for key, raw in (
        ("original_candidate_checksums_sha256", original["checksums.sha256"]),
        ("adjudication_checksums_sha256", bundle["checksums.sha256"]),
        ("scientific_review_sha256", artifacts[SCIENTIFIC_REVIEW]),
        ("execution_provenance_sha256", original["execution_provenance.json"]),
        ("processing_provenance_sha256", original["processing_provenance.json"]),
    ):
        require(getattr(provenance, key) == sha256(raw), "publication provenance content binding mismatch")
    # Historical code identities are verified by content, never by the reviewer's HEAD.
    require(provenance.generator_files == generator_files(), "use the declared publication generator code")
    adjudication = verify_adjudication(evidence, bundle, artifacts[SCIENTIFIC_REVIEW])
    require(artifacts["REPORT.md"] == publication_report(
        evidence, adjudication, provenance, manifest).encode("utf-8"), "public report is stale")
    require(artifacts["ADJUDICATION_REPRODUCTION.md"] == adjudication_reproduction(bundle).encode("utf-8"),
            "adjudication reproduction note is stale")
    return manifest, evidence.summary
