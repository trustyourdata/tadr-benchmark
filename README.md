# TADR Benchmark

TADR Benchmark is a reproducible evaluation framework for deterministic,
task-aware dataset readiness assessment. It owns experimental specifications,
independent ground truth, measurement contracts and public research artifacts.
TADR Core (`tadr-core`, imported as `tadr`) is the reference implementation under
evaluation.

**Status: Experimental framework. `ALPHA_BENCHMARK_V1` execution and scientific
adjudication are complete; immutable publication awaits final freeze authorization.**
There are no published benchmark measurements, generated campaign datasets or
Alpha figures. The [results index](RESULTS.md) records campaign status and will
link to the immutable report only after verified freeze. Its current launch
status is historical; the index is deliberately updated after freeze.

## Why an independent benchmark

A deterministic readiness report can be reproducible and still miss defects,
raise unnecessary warnings or respond poorly to sampling. Unit tests of the
reference implementation cannot establish detection quality or the practical
cost of analysis over a controlled experimental matrix. The benchmark tests
those questions with independently specified conditions and retains unfavorable
outcomes as research evidence.

TADR Core implements profiling, checks, Findings and scoring. This repository
does not copy its scoring formulas or infer ground truth from target reports.
Pinned contract boundaries are independently authored experimental expectations,
separate from physical-condition and research-challenge labels. The adapter calls the installed public
`tadr.analyze` API and preserves the target's canonical report bytes. Ground
truth is authored before target execution.

## Research questions

- Which injected conditions are detected, missed or associated with unexpected Findings?
- How often do clean controls trigger Findings, and which subjects are affected?
- How do scores, risk categories and hard gates behave near documented boundaries
  and under combined defects?
- Do reports remain byte-identical across fresh processes, hash seeds, timezones
  and Decimal contexts?
- What is lost when bounded `HEAD_STRIDE_V1` analysis replaces full-data analysis?
- How do wall time, throughput and measured peak RSS change across selected scales?
- Which behaviors improve or regress between exact target artifacts on common scenarios?

## Principles and methodology

Use controlled synthetic data, clean negative controls and explicit boundary
cases. Select the experimental matrix for information value; do not assume every
format, task, defect and scale combination is useful. Record actual outcomes,
including negative results. Distinguish repeated measurements of one scenario
from independent experimental units. Preserve raw measurements before aggregation.

The [methodology](docs/methodology.md) covers detection, score characterization,
determinism, sampling fidelity, robustness and statistical limitations. Fixed
heuristic thresholds are evaluated as properties of the target implementation, not
recalibrated implicitly by the benchmark.

## Architecture

```text
Versioned family specifications -> concrete ScenarioSpec
  -> deterministic generator / injector
  -> DatasetArtifact + independent GroundTruth
  -> TargetAdapter
  -> instrumented execution / RunSpec
  -> strict RunResult or typed RunFailure
  -> evaluation / CampaignSummary
  -> tables, figures and REPORT.md
  -> immutable campaign / longitudinal comparison
```

The package implements strict models, declarative scenarios, independent generators,
verified working sources, isolated public-API workers, sampled RSS instrumentation,
an immutable attempt ledger, typed outcomes, comparison queries and deterministic
artifact generation/verification. Scientific campaign execution requires a READY
manifest and the approved environment. See the [execution contract](docs/execution.md).

Repository areas:

| Location | Responsibility |
| --- | --- |
| `src/tadr_benchmark/` | Independent evaluation package |
| `campaigns/` | Versioned campaign manifests |
| `scenarios/` | Versioned family specifications expanded into concrete scenarios |
| `tests/` | Small harness fixtures and behavioral tests |
| `docs/` | Methodology, schemas, versioning and reproducibility |
| `.work/` | Ignored datasets, runs, logs, temporary figures and staging |
| `results/campaigns/` | Reviewed frozen artifacts, created only when data exist |
| `RESULTS.md` | Deterministically generated longitudinal results index |

See [architecture](docs/architecture.md) for contracts and extension boundaries.

## Campaigns and scenario versions

Campaign identity, benchmark protocol, scenario-set version, result-schema version
and target Algorithm version are separate. A campaign fixes exact target and
benchmark revisions, selected scenario IDs, formats/tasks/scales, repetition
policy, measurement policy, determinism contexts and analysis variants.

A scenario fixes its ID/version, dimensions, generator version and parameters,
explicit RNG/seed if used, defect specifications, expected Finding patterns and
subjects, absent Findings, affected columns and gate expectation. It carries an
independent rationale. Numeric target scores are not detection ground truth.

The current [Alpha manifest](campaigns/ALPHA_BENCHMARK_V1.yaml) describes eleven
Check Set A checks, clean controls, single defects, composites and boundary
studies. CSV and Parquet and classification, regression, time-series and analytics
tasks are included where applicable. Scale points are 10k, 100k, 1M and
5M rows, plus 300k paired sampling and small support cases. The approved finite
plan contains 320 correctness, 36 sampling and 14 scale scenarios; 578 primary
analysis calls (13 warmups included) and 72 auxiliary diagnostic calls. Execution
is complete; raw evidence remains unpublished pending freeze. See the
[Alpha benchmark protocol](docs/alpha_benchmark_protocol.md).

Once frozen, a campaign and its scenario snapshots are immutable. A new method
requires a new campaign identity; changing a scenario requires a new version.
See [campaign versioning](docs/campaign_versioning.md).

## Metrics and comparisons

Raw run records retain original report hashes, ordered Finding IDs, severities
and subjects, readiness/confidence, total/category risks, hard-gate reasons and
remediation IDs. They also retain wall time, throughput, sampled process-tree
peak RSS, dimensions, analysis mode and sampling ratio. Optional instrumentation
fields distinguish unavailable CPU/spill/scan/batch measurements from measured zero.

Expectation matching records misses and explicit negative-control violations;
unexpected Findings remain visible. Summary tables report counts, score ranges,
runtime median, median absolute deviation and RSS/throughput medians. These
counts are not automatically interpreted as population precision or recall.

Finding-based precision, recall and FPR are conditional on successful canonical
reports and are always paired with planned/evaluable opportunity support, report
coverage and terminal failures by category. End-to-end physical detection yield
separately includes planned positive opportunities without reports. The
[opportunity policy](docs/opportunity_mapping.md) defines these denominators.

Cross-version comparisons require matching scenario content, data, format, task,
scale and semantic/measurement protocol. Detection and score comparisons can
remain eligible across hardware. Runtime/RSS/throughput percentage comparisons
additionally require the same exact source-file hash and explicitly approved equivalent environment classes. An
environment fingerprint alone is not approval. Compare common historical
scenarios separately from newly supported check families. Sampling comparisons
have a separate full-reference-versus-`HEAD_STRIDE_V1` contract.

## Reproducibility and target pinning

Frozen artifacts identify the proprietary `tadr-core` implementation by package
version `0.1.0`, Algorithm `1.0`, threshold profile `MVP_V1`, AnalysisBundle
protocol `1.0`, implementation baseline `1.0.12` and the SHA-256 of the exact
installation artifact. They also record the benchmark revision, Python and
dependency versions. `target_source_distribution` is `proprietary`; the public
source URL is null.

The benchmark methodology, synthetic generators/recipes, ground truth, scenario definitions,
execution protocol, evaluation code and published evaluation artifacts are public.
The evaluated TADR Core implementation is proprietary. The exact implementation
used for a campaign is identified by versioned target metadata and a cryptographic
fingerprint of the execution artifact; the proprietary artifact and its source
code are not distributed by this repository. Source-level rebuild reproducibility
is not publicly available. Re-execution requires authorized access to the exact
artifact. Generated source CSV/Parquet files are excluded from the release;
public recipes and identities support regeneration. See the
[reproducibility boundary](docs/reproducibility.md).

Install the target from an authorized private wheel. The adapter verifies the
wheel hash, installed payload and package/runtime version before analysis. The
artifact location is supplied through the execution API's `installation_artifact`
argument or ignored `benchmark.local.toml`, whose `[target]` table contains only
an `installation_artifact` string. Relative paths resolve against the benchmark
repository. Local paths never enter public campaign metadata. Core remains an
optional system under test, not an automatic benchmark dependency.

Environment capture allows OS/version, architecture, Python, core counts, total
RAM and allowlisted dependency versions. CPU model is nullable and currently
omitted because portable APIs may expose identifying text. It does not collect
hostnames, usernames, network identifiers, repository paths or environment dumps.
Exact dependency inventories are captured at execution, not inferred later from
this package's development dependency ranges.

## Quickstart

Python 3.11 or newer is required. From this repository:

```sh
python -m venv .venv
# Activate .venv using your shell's activation command.
python -m pip install -e '.[test]'
python -m pytest --tb=short
python -m pip check
tadr-benchmark validate
tadr-benchmark safety --include-untracked
tadr-benchmark results-index --check
```

On Windows, `.venv\Scripts\python.exe` can replace `python` without activation;
use `python -m tadr_benchmark.cli` instead of the console command if needed.
Inspect the machine-readable contracts with `tadr-benchmark schema RunResult`.
`tadr-benchmark environment` emits sanitized metadata only.

After installing the pinned target, `tadr-benchmark preflight` explicitly runs a
fixed six-case NON-RESEARCH software/protocol check under ignored `.work/`.
It covers two 10k inputs, one 300k full/bounded pair and 100k inputs with 20 and
100 columns. It never freezes results or updates the results index. See
[execution](docs/execution.md) for scope, continuation and host requirements.

## Running future campaigns

The explicit `campaigns.runner.run_campaign` API uses fresh workers and a verified
resume ledger. There is no `run` CLI command. The source manifest keeps `benchmark_git_commit` null; clean-tree
resolution records the existing HEAD in execution provenance and the frozen manifest.
Alpha executed in the validated Ubuntu 24.04 WSL2 execution
environment: Linux x86_64, Python 3.11.9, POLARS_MAX_THREADS=4 and WSL-native
ext4 scientific storage. The manifest records verified instrumentation, target
metadata and the exact private installation-artifact SHA-256. Scientific-methodology
changes after READY require explicit new review. The source manifest retains its
historical READY launch declaration and a null source SHA; original evidence
retains the resolved scientific execution revision.
`expand_run_plan` validates a finite plan without execution; `planned_runs` rejects PLANNED campaigns.
All data and working outputs go under `.work/`.

The generic freeze API accepts completed records, independent scenario specifications,
environment records, original canonical reports, typed terminal failures and
required independent/observation companions. It requires a clean benchmark
revision, complete terminal outcome inventory and explicit publication review; it validates
and generates artifacts before creating a new frozen directory. It never executes
the target. Generated figures and tables are functions of the same raw records.

## Reproducing frozen results

Alpha uses `campaigns.publication.freeze_publication` to include the full
adjudication and original candidate history before checksumming and immutable
creation. Execution, historical processing and publication assembly revisions
are distinct. `stage_publication` validates the same package under ignored
working storage with an unresolved publication revision/date; it cannot enter
the results index or pass normal frozen verification. Both original-label and
adjudicated results and all adverse observations remain visible.

No frozen campaigns exist yet. The publication format contains `manifest.json`,
`environment.json`, `run_specs.json`, `attempts.jsonl`, selected `runs.jsonl` and `failures.jsonl`, typed label,
dataset identity, instrumentation and diagnostic companions, `summary.json`, scenario and
canonical report snapshots, `protocol.md`, original tables/figures, original
candidate history, the full `adjudication_v1/` bundle, publication provenance/
inventory, `ADJUDICATION_REPRODUCTION.md`, public `REPORT.md` and outer checksums.
Verify it with `tadr-benchmark verify-frozen results/campaigns/<campaign>` and use
its exact benchmark revision, fingerprinted target artifact, dependencies and
execution plan with the isolated runner.
Update the root index with `tadr-benchmark results-index`. Schema migrations must
be explicit; readers reject unknown schema versions. See
[reproducibility](docs/reproducibility.md) and [result schema](docs/result_schema.md).

## Public data and licensing

Repository-authored code and documentation use Apache-2.0; that license does not
cover the proprietary TADR Core implementation. No third-party data
are included. A downloadable dataset is not automatically redistributable;
[THIRD_PARTY_DATA.md](THIRD_PARTY_DATA.md) defines the required registry. Generated
datasets remain ignored working artifacts; publishing them requires an explicit
data-license decision. Only deliberately public synthetic source values may
appear in frozen canonical reports.

The automated safety scan checks tracked text and optionally untracked candidates
for obvious paths, credentials, identifiers and prohibited artifacts. It does
not replace human disclosure/license review. See the
[public repository policy](docs/public_repository_policy.md) and [SECURITY.md](SECURITY.md).

## Limitations and roadmap

Alpha evaluates Check Set A with fixed `MVP_V1` heuristics. Check Sets B/C are
outside its scope. Controlled synthetic data do not establish real-world defect
prevalence, fairness, downstream model quality or production suitability.
Deterministic sampling can miss adversarially placed defects; sampled RSS can
miss short-lived peaks. Harness test success is not a scientific benchmark result.

1. Authorize and verify immutable `ALPHA_BENCHMARK_V1` publication using its
   completed evidence and approved scientific adjudication.
2. Evaluate complete Algorithm v1 in `TADR_BENCHMARK_V1` with an expanded corpus.
3. Evaluate optimized Algorithm v1 in `TADR_BENCHMARK_V1_FINAL_RESULTS` while
   preserving the common historical subset.
4. Add calibrated and future Algorithm campaigns through versioned schemas and
   explicit comparisons, retaining historical outcomes.

See [CONTRIBUTING.md](CONTRIBUTING.md) for validation and Conventional Commits.
The repository license is [Apache-2.0](LICENSE).
