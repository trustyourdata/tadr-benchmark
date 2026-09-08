"""Deliberate freeze of completed, reviewed artifacts; never executes a target."""

import json
import subprocess
import tempfile
from pathlib import Path

from ..models import CampaignManifest, CampaignSummary, EnvironmentInfo, RunResult, ScenarioSpec
from ..companions import (DatasetIdentity, DiagnosticRecord, InstrumentationRecord,
                          RunFailure, ScenarioExpectations)
from .companions import validate_companions
from ..paths import campaign_directory, contained
from ..reporting.aggregate import aggregate, run_bytes
from ..reporting.markdown import campaign_report
from ..reporting.tables import summary_csv
from ..reporting.queries import ReportInputs, TABLE_COLUMNS, csv_bytes, table_rows
from ..reporting.plots import build_figures
from ..reporting.protocol import protocol_bytes
from ..safety import repository_issues, scan_files
from ..serialization import canonical_bytes, sha256
from ..execution.attempts import AttemptRecord, attempt_bytes, validate_attempts
from ..validation import planned_runs, validate_completed, validate_historical_scenarios


def require_clean_revision(root: Path, expected: str | None = None) -> str:
    def git(*args):
        return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    if git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("benchmark working tree must be clean before freeze")
    revision = git("rev-parse", "HEAD")
    if expected is not None and revision != expected:
        raise ValueError("benchmark checkout differs from campaign revision")
    return revision


def resolve_manifest(root: Path, manifest: CampaignManifest) -> CampaignManifest:
    """Bind execution to an existing clean revision without editing source YAML."""
    if manifest.status != "ready":
        raise ValueError("only ready campaigns can resolve execution provenance")
    revision = require_clean_revision(root, manifest.benchmark_git_commit)
    return CampaignManifest.model_validate({**manifest.model_dump(), "benchmark_git_commit": revision})


def validate_reports(runs: list[RunResult], reports: dict[str, bytes]) -> None:
    if set(reports) != {run.run_id for run in runs}:
        raise ValueError("canonical report inventory differs from runs")
    for run in runs:
        original = reports[run.run_id]
        if sha256(original) != run.canonical_report_sha256:
            raise ValueError("canonical report checksum mismatch")
        report = json.loads(original)
        for field in ("readiness_score", "report_confidence", "total_risk"):
            if float(report[field]) != getattr(run, field):
                raise ValueError(f"result differs from target report: {field}")
        if {key: float(value) for key, value in report["category_risks"].items()} != run.category_risks:
            raise ValueError("result risks differ from target report")
        findings = report["findings"]
        if ([item["id"] for item in findings] != run.finding_ids
                or [item["severity"] for item in findings] != run.finding_severities
                or [item["metadata"]["subject_key"] for item in findings] != run.finding_subjects):
            raise ValueError("result Findings differ from target report")
        stats = report["analysis_stats"]
        for source, target in (("row_count", "row_count"), ("col_count", "column_count"),
                               ("analysis_mode", "analysis_mode")):
            if stats[source] != getattr(run, target):
                raise ValueError("result analysis metadata differs from report")
        if float(stats["sample_ratio"]) != run.sample_ratio:
            raise ValueError("result sampling ratio differs from report")
        gates = [item["reason"] for item in report["score_breakdown"]["caps_applied"]
                 if item["type"] == "hard_gate"]
        if gates != run.hard_gates or [item["id"] for item in report["remediation_plan"]] != run.remediation_ids:
            raise ValueError("result gates or remediations differ from report")


def validate_observation_bindings(attempts, instrumentation, diagnostics, reports):
    monitors = {i.run_id: i for i in instrumentation}
    for attempt in attempts:
        if attempt.selected_as_final_outcome and monitors and attempt.instrumentation != monitors.get(attempt.run_id):
            raise ValueError("selected attempt instrumentation differs from authoritative monitor")
    for diagnostic in diagnostics:
        profile = json.loads(reports[diagnostic.primary_run_id])["dataset_profile"]
        if diagnostic.shared_profile_sha256 != sha256(canonical_bytes(profile)):
            raise ValueError("diagnostic shared profile hash differs from primary report")


def freeze(root: Path, manifest: CampaignManifest, scenarios: list[ScenarioSpec],
           runs: list[RunResult], environments: dict[str, EnvironmentInfo],
           reports: dict[str, bytes], frozen_date: str, *, public_reviewed: bool,
           attempts: list[AttemptRecord],
           failures: list[RunFailure] | None = None,
           expectations: list[ScenarioExpectations] | None = None,
           datasets: list[DatasetIdentity] | None = None,
           instrumentation: list[InstrumentationRecord] | None = None,
           diagnostics: list[DiagnosticRecord] | None = None) -> Path:
    if not public_reviewed:
        raise ValueError("publication review must be explicitly recorded before freeze")
    if manifest.status != "ready":
        raise ValueError("only a ready campaign can be frozen")
    destination = campaign_directory(root, manifest.campaign_id)
    if destination.exists():
        raise ValueError("frozen campaign directory already exists; create a new campaign ID")
    manifest = resolve_manifest(root, manifest)
    failures, expectations, datasets = failures or [], expectations or [], datasets or []
    instrumentation, diagnostics = instrumentation or [], diagnostics or []
    if repository_issues(root, include_untracked=True):
        raise ValueError("repository public-safety scan failed")
    validate_completed(manifest, scenarios, runs, environments, failures)
    validate_companions(manifest, scenarios, runs, failures, expectations, datasets, instrumentation, diagnostics)
    validate_historical_scenarios(root, scenarios)
    validate_reports(runs, reports)
    validate_attempts(planned_runs(manifest, scenarios), attempts, runs, failures)
    validate_observation_bindings(attempts, instrumentation, diagnostics, reports)
    summary = aggregate(manifest.campaign_id, runs, failures, attempts)
    frozen = CampaignManifest.model_validate({**manifest.model_dump(), "status": "frozen", "frozen_date": frozen_date})
    derived_tables = table_rows(ReportInputs(frozen, scenarios, runs, failures, reports, attempts, expectations, diagnostics))
    figures = build_figures(derived_tables)
    work = contained(root, ".work/freeze")
    work.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=work) as temporary:
        stage = Path(temporary) / "campaign"
        stage.mkdir()
        artifacts = {
            "manifest.json": canonical_bytes(frozen),
            "environment.json": canonical_bytes({key: env.model_dump(mode="json") for key, env in environments.items()}),
            "summary.json": canonical_bytes(summary),
            "runs.jsonl": run_bytes(runs),
            "failures.jsonl": run_bytes(failures),
            "attempts.jsonl": attempt_bytes(attempts),
            "expectations.json": canonical_bytes([e.model_dump(mode="json") for e in sorted(expectations, key=lambda e: e.scenario_id)]),
            "dataset_manifest.json": canonical_bytes([d.model_dump(mode="json") for d in sorted(datasets, key=lambda d: d.scenario_id)]),
            "instrumentation.jsonl": b"".join(canonical_bytes(i) for i in sorted(instrumentation, key=lambda i: i.run_id)),
            "run_specs.json": canonical_bytes([run.model_dump(mode="json") for run in planned_runs(manifest, scenarios)]),
            "tables/summary.csv": summary_csv(summary).encode("utf-8"),
            **{f"tables/{name}": csv_bytes(TABLE_COLUMNS[name], data) for name, data in derived_tables.items()},
            **{f"figures/{name}": data for name, data in figures.items()},
            "protocol.md": protocol_bytes(frozen),
            "REPORT.md": campaign_report(frozen, summary, tables=derived_tables, figures=figures).encode("utf-8"),
            **{f"scenarios/{scenario.scenario_id}.json": canonical_bytes(scenario) for scenario in scenarios},
            **{f"reports/{run_id}.json": data for run_id, data in reports.items()},
            **{f"diagnostics/{d.primary_run_id}.json": canonical_bytes(d) for d in diagnostics},
        }
        for relative, data in artifacts.items():
            path = contained(stage, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        files = sorted(path.relative_to(stage).as_posix() for path in stage.rglob("*") if path.is_file())
        if scan_files(stage, files):
            raise ValueError("generated artifacts failed public-safety scan")
        checksums = "".join(f"{sha256((stage / name).read_bytes())}  {name}\n" for name in files)
        (stage / "checksums.sha256").write_text(checksums, encoding="utf-8", newline="\n")
        verify_frozen(stage, check_directory_name=False)
        require_clean_revision(root, manifest.benchmark_git_commit)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise ValueError("frozen destination appeared during validation")
        stage.rename(destination)
    return destination


def verify_frozen(directory: Path, *, check_directory_name: bool = True) -> tuple[CampaignManifest, CampaignSummary]:
    if directory.is_symlink():
        raise ValueError("frozen directories cannot be symlinks")
    if any(path.is_symlink() for path in directory.rglob("*")):
        raise ValueError("frozen artifacts cannot contain symlinks")
    expected = {}
    for line in (directory / "checksums.sha256").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        if relative in expected or relative == "checksums.sha256":
            raise ValueError("duplicate or recursive checksum entry")
        path = contained(directory, relative)
        if sha256(path.read_bytes()) != digest:
            raise ValueError("frozen artifact checksum mismatch")
        expected[relative] = digest
    actual = {path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file()}
    if actual != set(expected) | {"checksums.sha256"}:
        raise ValueError("unchecksummed or missing frozen artifacts")
    if scan_files(directory, sorted(actual)):
        raise ValueError("frozen artifacts failed public-safety scan")
    manifest = CampaignManifest.model_validate_json((directory / "manifest.json").read_bytes())
    if manifest.status != "frozen":
        raise ValueError("missing frozen status")
    if check_directory_name and directory.name != manifest.campaign_id.lower():
        raise ValueError("campaign directory identity mismatch")
    scenarios = [ScenarioSpec.model_validate_json(path.read_bytes())
                 for path in sorted((directory / "scenarios").glob("*.json"))]
    runs = [RunResult.model_validate_json(line) for line in (directory / "runs.jsonl").read_bytes().splitlines()]
    failures = [RunFailure.model_validate_json(line) for line in (directory / "failures.jsonl").read_bytes().splitlines()]
    attempts = [AttemptRecord.model_validate_json(line) for line in (directory / "attempts.jsonl").read_bytes().splitlines()]
    expectations = [ScenarioExpectations.model_validate_json(json.dumps(item)) for item in
                    json.loads((directory / "expectations.json").read_bytes())]
    datasets = [DatasetIdentity.model_validate_json(json.dumps(item)) for item in
                json.loads((directory / "dataset_manifest.json").read_bytes())]
    instrumentation = [InstrumentationRecord.model_validate_json(line) for line in
                       (directory / "instrumentation.jsonl").read_bytes().splitlines()]
    diagnostics = [DiagnosticRecord.model_validate_json(p.read_bytes()) for p in
                   sorted((directory / "diagnostics").glob("*.json"))]
    environments = {key: EnvironmentInfo.model_validate_json(json.dumps(value)) for key, value in
                    json.loads((directory / "environment.json").read_bytes()).items()}
    validate_completed(manifest, scenarios, runs, environments, failures)
    validate_attempts(planned_runs(manifest, scenarios), attempts, runs, failures)
    validate_companions(manifest, scenarios, runs, failures, expectations, datasets, instrumentation, diagnostics)
    if (directory / "run_specs.json").read_bytes() != canonical_bytes(
            [run.model_dump(mode="json") for run in planned_runs(manifest, scenarios)]):
        raise ValueError("frozen execution plan mismatch")
    reports = {path.stem: path.read_bytes() for path in (directory / "reports").glob("*.json")}
    validate_reports(runs, reports)
    validate_observation_bindings(attempts, instrumentation, diagnostics, reports)
    summary = CampaignSummary.model_validate_json((directory / "summary.json").read_bytes())
    if summary != aggregate(manifest.campaign_id, runs, failures, attempts):
        raise ValueError("frozen summary does not derive from run records")
    if (directory / "tables" / "summary.csv").read_text(encoding="utf-8") != summary_csv(summary):
        raise ValueError("frozen table is stale")
    derived_tables = table_rows(ReportInputs(manifest, scenarios, runs, failures, reports, attempts, expectations, diagnostics))
    figures = build_figures(derived_tables)
    if set(p.name for p in (directory / "tables").iterdir()) != set(derived_tables) | {"summary.csv"}:
        raise ValueError("frozen table inventory mismatch")
    if set(p.name for p in (directory / "figures").glob("*")) != set(figures):
        raise ValueError("frozen figure inventory mismatch")
    for name, data in derived_tables.items():
        if (directory / "tables" / name).read_bytes() != csv_bytes(TABLE_COLUMNS[name], data):
            raise ValueError("frozen derived table is stale")
    for name, data in figures.items():
        if (directory / "figures" / name).read_bytes() != data:
            raise ValueError("frozen derived figure is stale")
    if (directory / "protocol.md").read_bytes() != protocol_bytes(manifest):
        raise ValueError("frozen protocol differs from declared measurement semantics")
    if (directory / "REPORT.md").read_text(encoding="utf-8") != campaign_report(manifest, summary, tables=derived_tables, figures=figures):
        raise ValueError("frozen report is stale")
    return manifest, summary


def verify_history(root: Path, base_ref: str) -> None:
    """Reject rewrites/deletions of campaigns already frozen in the PR base."""
    result = subprocess.run(["git", "ls-tree", "-r", "--name-only", base_ref, "--", "results/campaigns"],
                            cwd=root, check=True, capture_output=True, text=True)
    for name in result.stdout.splitlines():
        if name.endswith("/manifest.json"):
            old = subprocess.run(["git", "show", f"{base_ref}:{name}"], cwd=root,
                                 check=True, capture_output=True).stdout
            if json.loads(old).get("status") == "frozen":
                unchanged = subprocess.run(["git", "diff", "--quiet", base_ref, "--", str(Path(name).parent)], cwd=root)
                if unchanged.returncode:
                    raise ValueError("historical frozen campaign changed; use a new campaign ID")
