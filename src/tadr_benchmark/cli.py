import argparse
import json
from pathlib import Path

from .campaigns.freeze import verify_frozen, verify_history
from .instrumentation.environment import capture_environment
from .models import CampaignManifest, EnvironmentInfo, RunResult, RunSpec, ScenarioSpec, TargetMetadata
from .companions import (DatasetIdentity, DiagnosticRecord, InstrumentationRecord, OutcomeAccounting,
                         PhysicalLedger, RunFailure, ScenarioExpectations, WriterPolicy)
from .scenarios.families import FamilyDefinition, FamilyInventory
from .reporting.markdown import results_index
from .safety import repository_issues
from .serialization import canonical_bytes
from .validation import validate_repository
from .execution.attempts import AttemptRecord
from .evaluation.metrics import DetectionMetrics, ReportCoverage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="TADR Benchmark validation and explicit software preflight")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="validate campaigns, scenarios and any frozen artifacts")
    safety = sub.add_parser("safety", help="scan public repository files")
    safety.add_argument("--include-untracked", action="store_true")
    sub.add_parser("environment", help="print sanitized allowlisted metadata")
    preflight = sub.add_parser("preflight", help="execute only the fixed six-case NON-RESEARCH software/protocol preflight under .work")
    preflight.add_argument("--resume", action="store_true", help="continue after repaired diagnostic infrastructure; retain original primary calls")
    results = sub.add_parser("results-index", help="deterministically update RESULTS.md")
    results.add_argument("--check", action="store_true")
    frozen = sub.add_parser("verify-frozen", help="verify a frozen campaign directory")
    frozen.add_argument("directory", type=Path)
    history = sub.add_parser("verify-history", help="reject edits to historical frozen campaigns")
    history.add_argument("base_ref")
    schema = sub.add_parser("schema", help="print a versioned JSON schema")
    models = {model.__name__: model for model in (CampaignManifest, ScenarioSpec, RunSpec, RunResult, DetectionMetrics, ReportCoverage,
                                                 EnvironmentInfo, TargetMetadata, RunFailure, OutcomeAccounting, AttemptRecord,
                                                 ScenarioExpectations, PhysicalLedger, DatasetIdentity, WriterPolicy,
                                                 InstrumentationRecord, DiagnosticRecord, FamilyDefinition, FamilyInventory)}
    schema.add_argument("model", choices=sorted(models))
    args = parser.parse_args(argv)
    try:
        if args.command == "validate":
            manifests = validate_repository(args.root)
            print(f"Validated {len(manifests)} campaign manifest(s); no campaign executed.")
        elif args.command == "safety":
            issues = repository_issues(args.root, args.include_untracked)
            if issues:
                print("\n".join(issues))
                return 1
            print("Public-safety scan passed.")
        elif args.command == "environment":
            print(canonical_bytes(capture_environment()).decode(), end="")
        elif args.command == "preflight":
            from .execution.preflight import run_preflight
            receipt = run_preflight(args.root.resolve(), resume=args.resume)
            print(json.dumps({"preflight_status": receipt["status"], "research": False}))
            return 0 if receipt["status"] == "passed" else 1
        elif args.command == "results-index":
            expected = results_index(args.root, validate_repository(args.root))
            destination = args.root / "RESULTS.md"
            if args.check:
                if not destination.is_file() or destination.read_text(encoding="utf-8") != expected:
                    print("RESULTS.md is stale; run results-index.")
                    return 1
            else:
                destination.write_text(expected, encoding="utf-8", newline="\n")
        elif args.command == "verify-frozen":
            verify_frozen(args.directory)
            print("Frozen campaign verified.")
        elif args.command == "verify-history":
            verify_history(args.root, args.base_ref)
        elif args.command == "schema":
            print(json.dumps(models[args.model].model_json_schema(), indent=2, sort_keys=True))
    except (ValueError, OSError) as error:
        # Validation errors may embed input values and private paths. Keep CLI
        # diagnostics suitable for public CI; inspect details locally in Python.
        print(f"Validation failed ({type(error).__name__}); inspect inputs locally.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
