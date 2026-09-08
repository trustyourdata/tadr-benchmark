"""Fixed small NON-RESEARCH software/protocol preflight, never a campaign freeze."""

import json
from copy import deepcopy
import subprocess
import time
from pathlib import Path

from ..campaigns.loader import load_campaign
from ..generators.identity import logical_dataset_sha256, source_file_sha256
from ..generators.tabular import iter_rows
from ..generators.writers import logical_schema, read_logical_source, read_source_schema, write_source
from ..instrumentation.environment import capture_environment
from ..models import RunSpec, TargetMetadata
from ..paths import contained
from ..scenarios.recipe import recipe_from_id, task_parameters
from ..serialization import canonical_bytes, sha256
from .diagnostics import request_diagnostic
from .ledger import write_once
from .supervisor import invoke_worker

CASES = (
    ("clean_10k", "clean.analytics.n10000.csv", "full_reference"),
    ("parse_boundary_10k", "parse.numeric.f100.n10000.pqstr", "full_reference"),
    ("sampling_full_300k", "sampling.missingness.head.n300000.pqstr", "full_reference"),
    ("sampling_bounded_300k", "sampling.missingness.head.n300000.pqstr", "HEAD_STRIDE_V1"),
    ("scale_100k_20", "scale.analytics.n100000.w20.pqnative", "scale_default"),
    ("scale_100k_100", "scale.analytics.n100000.w100.pqnative", "scale_default"),
)


def source_snapshot(root: Path) -> dict:
    """Bind development software without claiming that dirty code belongs to HEAD."""
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True).stdout.strip()
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root, check=True, capture_output=True).stdout != b""
    names = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                           cwd=root, check=True, capture_output=True).stdout.split(b"\0")
    inventory = {name.decode(): sha256((root / name.decode()).read_bytes()) for name in names
                 if name and (root / name.decode()).is_file()}
    return {"base_benchmark_git_commit": head, "dirty_working_tree": dirty,
            "working_source_inventory_sha256": sha256(canonical_bytes(inventory))}


def run_preflight(root: Path, *, local_checkout: Path | None = None, resume: bool = False) -> dict:
    manifest = load_campaign(root / "campaigns" / "ALPHA_BENCHMARK_V1.yaml")
    context = next(c for c in manifest.determinism_cases if c.case_id == "standard")
    variants = {v.variant_id: v for v in manifest.analysis_variants}
    target = {k: getattr(manifest, k) for k in TargetMetadata.model_fields}
    directory = contained(root, ".work/preflight/software_protocol_v1")
    previous = None
    receipt_path = directory / "receipt.json"
    if resume:
        history = sorted(directory.glob("receipt.*.json"))
        parent = history[-1] if history else receipt_path
        previous = json.loads(parent.read_bytes())
        if previous["status"] != "infrastructure_blocked" or any(
                r["failure_kind"] is not None or not r.get("planning_assumptions_held") for r in previous["cases"]):
            raise ValueError("preflight resume requires validation infrastructure failure after successful primary calls")
        plan = json.loads((directory / "plan.json").read_bytes())
        if plan["target"] != target or plan["declared_cases"] != [list(c) for c in CASES]:
            raise ValueError("preflight continuation target or declared cases differ")
        if [r["preflight_case"] for r in previous["cases"]] != [c[0] for c in CASES[:len(previous["cases"])]]:
            raise ValueError("preflight continuation has an invalid completed prefix")
        receipt_path = directory / f"receipt.{len(history)+1:03d}.json"
    else:
        directory.mkdir(parents=True, exist_ok=False)
    receipt = {"purpose": "NON-RESEARCH software/protocol preflight; excluded from Alpha results",
        "preflight_id": "PREFLIGHT_SOFTWARE_PROTOCOL_V1", "target": target,
        "benchmark_source": source_snapshot(root), "environment": capture_environment().model_dump(mode="json"),
        "cases": [], "status": "started", "primary_invocations": 0, "auxiliary_invocations": 0}
    if previous:
        receipt.update(parent_receipt_sha256=sha256(parent.read_bytes()),
            primary_invocations=previous["primary_invocations"], auxiliary_invocations=previous["auxiliary_invocations"],
            reused_primary_cases=[r["preflight_case"] for r in previous["cases"]],
            infrastructure_resolution="diagnostic_numeric_transport_fixed")
        write_once(directory / f"plan.{len(history)+1:03d}.json", canonical_bytes(receipt))
    else:
        write_once(directory / "plan.json", canonical_bytes({**receipt, "declared_cases": [list(c) for c in CASES]}))
    completed = {r["preflight_case"]: r for r in previous["cases"]} if previous else {}
    sources = {}
    started = time.perf_counter()
    try:
        for name, reference, variant in CASES:
            recipe = recipe_from_id(reference)
            if reference not in sources:
                source = directory / ("source_"+str(len(sources))+ (".csv" if recipe.representation == "csv" else ".parquet"))
                print(json.dumps({"preflight_case": name, "status": "preparing_source", "research": False}), flush=True)
                if not source.exists():
                    write_source(recipe, source)
                schema = logical_schema(recipe)
                if read_source_schema(source, recipe.representation) != schema:
                    raise ValueError("preflight source schema mismatch")
                expected = logical_dataset_sha256(schema, iter_rows(recipe), recipe.row_count)
                if logical_dataset_sha256(schema, read_logical_source(source, recipe.representation), recipe.row_count) != expected:
                    raise ValueError("preflight logical source mismatch")
                sources[reference] = (source, expected, source_file_sha256(source))
            source, logical, source_hash = sources[reference]
            scenario_snapshot = {"scenario_id": "preflight."+name, "reference_recipe": recipe.model_dump(mode="json"),
                                 "purpose": "NON-RESEARCH"}
            spec = RunSpec(campaign_id="PREFLIGHT_SOFTWARE_PROTOCOL_V1", scenario_id="preflight."+name,
                scenario_version="1.0", scenario_sha256=sha256(canonical_bytes(scenario_snapshot)), run_id="preflight."+name,
                repeat_index=0, phase="measurement", determinism_case_id=context.case_id, determinism_context=context,
                analysis_variant=variant, constraints=variants[variant].constraints, execution_group_id="software_preflight",
                instrumentation_policy={"timeout_seconds": 1800.0 if recipe.family == "sampling" else 600.0,
                                        "memory_sampling_interval_seconds": 0.01})
            spec_path = directory / (name+".spec.json")
            if name in completed:
                if spec_path.read_bytes() != canonical_bytes(spec):
                    raise ValueError("preflight completed specification mismatch")
            else:
                write_once(spec_path, canonical_bytes(spec))
            request = {"target": target, "source": str(source), "task": {"task_type": recipe.task, **task_parameters(recipe)},
                       "constraints": spec.constraints, "local_checkout": str(local_checkout) if local_checkout else None}
            if name in completed:
                row = deepcopy(completed[name])
                original = (directory / (name+".report.json")).read_bytes()
                if (sha256(original) != row["canonical_report_sha256"] or logical != row["logical_dataset_sha256"]
                        or source_hash != row["source_file_sha256"] or canonical_bytes(row["instrumentation"]) !=
                        (directory / (name+".instrumentation.json")).read_bytes()):
                    raise ValueError("preflight completed artifact checksum mismatch")
                row.setdefault("benchmark_source", previous["benchmark_source"])
                receipt["cases"].append(row)
                print(json.dumps({"preflight_case": name, "status": "reused_original_primary", "research": False}), flush=True)
            else:
                print(json.dumps({"preflight_case": name, "status": "analyzing", "research": False}), flush=True)
                observation = invoke_worker(spec, request, cwd=root)
                receipt["primary_invocations"] += 1
                row = {"preflight_case": name, "row_count": recipe.row_count, "column_count": len(logical_schema(recipe)),
                    "source_bytes": source.stat().st_size, "logical_dataset_sha256": logical, "source_file_sha256": source_hash,
                    "runtime_seconds": observation.runtime_ns/1e9 if observation.runtime_ns is not None else None,
                    "peak_rss_bytes": observation.peak_rss_bytes, "failure_kind": observation.failure_kind,
                    "safe_error_code": observation.error_code, "instrumentation": observation.instrumentation.model_dump(mode="json"),
                    "benchmark_source": receipt["benchmark_source"]}
                receipt["cases"].append(row)
                write_once(directory / (name+".instrumentation.json"), canonical_bytes(observation.instrumentation))
                if observation.failure_kind:
                    receipt["status"] = "protocol_blocked"
                    break
                original = observation.original_report
                write_once(directory / (name+".report.json"), original)
            row["canonical_report_sha256"] = sha256(original)
            if sha256((directory / (name+".report.json")).read_bytes()) != row["canonical_report_sha256"]:
                raise ValueError("preflight persisted report mismatch")
            report = json.loads(original)
            row["analysis_mode"] = report["analysis_stats"]["analysis_mode"]
            row["sample_ratio"] = float(report["analysis_stats"]["sample_ratio"])
            row["planning_assumptions_held"] = True
            if recipe.family == "sampling":
                # The pinned canonical report renders sample_ratio to four places.
                expected_mode, expected_ratio = ("full", 1.0) if variant == "full_reference" else ("sampled", 0.6667)
                row["planning_assumptions_held"] = row["analysis_mode"] == expected_mode and row["sample_ratio"] == expected_ratio
                if not row["planning_assumptions_held"]:
                    receipt["status"] = "protocol_blocked"
                    break
                diagnostic_path = directory / (name+".diagnostics.json")
                if diagnostic_path.exists():
                    payload = json.loads(diagnostic_path.read_bytes())
                    if sha256(diagnostic_path.read_bytes()) != row.get("diagnostic_sha256"):
                        raise ValueError("preflight cached diagnostic checksum mismatch")
                else:
                    receipt["auxiliary_invocations"] += 1
                    payload = request_diagnostic({**request, "context": context.model_dump(mode="json"), "case": recipe.case},
                                                 context, spec.instrumentation_policy.timeout_seconds)
                if any(payload[k] != report[k] for k in ("analysis_stats", "dataset_profile")):
                    raise ValueError("preflight diagnostic/primary disagreement")
                row["observable_bundle_provenance"] = {k: payload[k] for k in ("algorithm_version", "threshold_profile", "protocol_version")}
                if not diagnostic_path.exists():
                    write_once(diagnostic_path, canonical_bytes(payload))
                row["diagnostic_sha256"] = sha256(diagnostic_path.read_bytes())
            print(json.dumps({k: v for k, v in row.items() if k not in {"instrumentation", "logical_dataset_sha256", "source_file_sha256"}}), flush=True)
        else:
            receipt["status"] = "passed"
    except Exception:
        receipt["status"] = "infrastructure_blocked"
        receipt["safe_error_code"] = "preflight_validation"
        raise
    finally:
        receipt["total_elapsed_seconds"] = time.perf_counter()-started
        receipt["working_bytes_before_receipt"] = sum(p.stat().st_size for p in directory.rglob("*") if p.is_file())
        write_once(receipt_path, canonical_bytes(receipt))
    return receipt
