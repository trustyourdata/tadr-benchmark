"""Deliberate freeze of completed, reviewed artifacts; never executes a target."""

import json
import subprocess
import tempfile
from pathlib import Path

from ..models import CampaignManifest, CampaignSummary, EnvironmentInfo, RunResult, ScenarioSpec
from ..paths import campaign_directory, contained
from ..reporting.aggregate import aggregate, run_bytes
from ..reporting.figures import write_runtime_figure
from ..reporting.markdown import campaign_report
from ..reporting.tables import summary_csv
from ..safety import repository_issues, scan_files
from ..serialization import canonical_bytes, sha256
from ..validation import planned_runs, validate_completed, validate_historical_scenarios


def require_clean_revision(root: Path, expected: str) -> None:
    def git(*args):
        return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    if git("status", "--porcelain", "--untracked-files=all"):
        raise ValueError("benchmark working tree must be clean before freeze")
    if git("rev-parse", "HEAD") != expected:
        raise ValueError("benchmark checkout differs from campaign revision")


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


def freeze(root: Path, manifest: CampaignManifest, scenarios: list[ScenarioSpec],
           runs: list[RunResult], environments: dict[str, EnvironmentInfo],
           reports: dict[str, bytes], frozen_date: str, *, public_reviewed: bool) -> Path:
    if not public_reviewed:
        raise ValueError("publication review must be explicitly recorded before freeze")
    if manifest.status != "ready":
        raise ValueError("only a ready campaign can be frozen")
    destination = campaign_directory(root, manifest.campaign_id)
    if destination.exists():
        raise ValueError("frozen campaign directory already exists; create a new campaign ID")
    require_clean_revision(root, manifest.benchmark_git_commit)
    if repository_issues(root, include_untracked=True):
        raise ValueError("repository public-safety scan failed")
    validate_completed(manifest, scenarios, runs, environments)
    validate_historical_scenarios(root, scenarios)
    validate_reports(runs, reports)
    summary = aggregate(manifest.campaign_id, runs)
    frozen = CampaignManifest.model_validate({**manifest.model_dump(), "status": "frozen", "frozen_date": frozen_date})
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
            "run_specs.json": canonical_bytes([run.model_dump(mode="json") for run in planned_runs(manifest, scenarios)]),
            "tables/summary.csv": summary_csv(summary).encode("utf-8"),
            "REPORT.md": campaign_report(frozen, summary).encode("utf-8"),
            **{f"scenarios/{scenario.scenario_id}.json": canonical_bytes(scenario) for scenario in scenarios},
            **{f"reports/{run_id}.json": data for run_id, data in reports.items()},
        }
        for relative, data in artifacts.items():
            path = contained(stage, relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        (stage / "figures").mkdir()
        write_runtime_figure(summary, stage / "figures" / "runtime.svg")
        files = sorted(path.relative_to(stage).as_posix() for path in stage.rglob("*") if path.is_file())
        if scan_files(stage, files):
            raise ValueError("generated artifacts failed public-safety scan")
        checksums = "".join(f"{sha256((stage / name).read_bytes())}  {name}\n" for name in files)
        (stage / "checksums.sha256").write_text(checksums, encoding="utf-8", newline="\n")
        verify_frozen(stage, check_directory_name=False)
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
    environments = {key: EnvironmentInfo.model_validate_json(json.dumps(value)) for key, value in
                    json.loads((directory / "environment.json").read_bytes()).items()}
    validate_completed(manifest, scenarios, runs, environments)
    if (directory / "run_specs.json").read_bytes() != canonical_bytes(
            [run.model_dump(mode="json") for run in planned_runs(manifest, scenarios)]):
        raise ValueError("frozen execution plan mismatch")
    validate_reports(runs, {path.stem: path.read_bytes() for path in (directory / "reports").glob("*.json")})
    summary = CampaignSummary.model_validate_json((directory / "summary.json").read_bytes())
    if summary != aggregate(manifest.campaign_id, runs):
        raise ValueError("frozen summary does not derive from run records")
    if (directory / "tables" / "summary.csv").read_text(encoding="utf-8") != summary_csv(summary):
        raise ValueError("frozen table is stale")
    if (directory / "REPORT.md").read_text(encoding="utf-8") != campaign_report(manifest, summary):
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
