# TADR Benchmark

TADR Benchmark is a reproducible evaluation framework for deterministic,
task-aware dataset readiness assessment. It owns experimental specifications,
independent ground truth, measurement contracts and public research artifacts.
TADR Core (`tadr-core`, imported as `tadr`) is the reference implementation under
evaluation.

**Status: repository foundation. `ALPHA_BENCHMARK_V1` is PLANNED / NOT YET RUN.**
There are no published benchmark measurements, generated campaign datasets or
Alpha figures. The [results index](RESULTS.md) records campaign status and will
link to immutable reports when campaigns have been executed and reviewed.

## Why an independent benchmark

A deterministic readiness report can be reproducible and still miss defects,
raise unnecessary warnings or respond poorly to sampling. Unit tests of the
reference implementation cannot establish detection quality or the practical
cost of analysis over a controlled experimental matrix. The benchmark tests
those questions with independently specified conditions and retains unfavorable
outcomes as research evidence.

TADR Core implements profiling, checks, Findings and scoring. This repository
does not copy its formulas, reproduce its thresholds as evaluation logic or
infer correctness from its own reports. The adapter calls the installed public
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
- Which behaviors improve or regress between exact target revisions on common scenarios?

## Principles and methodology

Use controlled synthetic data, clean negative controls and explicit boundary
cases. Select the experimental matrix for information value; do not assume every
format, task, defect and scale combination is useful. Record actual outcomes,
including negative results. Distinguish repeated measurements of one scenario
from independent experimental units. Preserve raw measurements before aggregation.

The [methodology](docs/methodology.md) covers detection, score characterization,
determinism, sampling fidelity, robustness and statistical limitations. Fixed
heuristic thresholds are evaluated as properties of the target revision, not
recalibrated implicitly by the benchmark.

## Architecture

```text
Versioned ScenarioSpec
  -> deterministic generator / injector
  -> DatasetArtifact + independent GroundTruth
  -> TargetAdapter
  -> instrumented execution / RunSpec
  -> strict RunResult
  -> evaluation / CampaignSummary
  -> tables, figures and REPORT.md
  -> immutable campaign / longitudinal comparison
```

The foundation implements strict models, declarative loaders, target transport,
environment capture, expectation evaluation, aggregation, comparison eligibility,
report generation and artifact freezing/verification. Generator, injector and
instrumented executor interfaces define the next implementation boundary.
**No Alpha generator corpus or live campaign runner is enabled yet.**

Repository areas:

| Location | Responsibility |
| --- | --- |
| `src/tadr_benchmark/` | Independent evaluation package |
| `campaigns/` | Versioned campaign manifests |
| `scenarios/` | Future declarative scenario corpus |
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
tasks are planned where applicable. Pilot scale candidates are 10k, 100k, 1M and
5M rows. These are plans, not allocated runs. The scenario list and execution
policies remain unset until the corpus and runner design pass.

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

Cross-version comparisons require matching scenario content, data, format, task,
scale and semantic/measurement protocol. Detection and score comparisons can
remain eligible across hardware. Runtime/RSS/throughput percentage comparisons
additionally require explicitly approved equivalent environment classes. An
environment fingerprint alone is not approval. Compare common historical
scenarios separately from newly supported check families. Sampling comparisons
have a separate full-reference-versus-`HEAD_STRIDE_V1` contract.

## Reproducibility and target pinning

Frozen artifacts record the exact target Git commit, package version, Algorithm
version, threshold profile, AnalysisBundle protocol and baseline revision, plus
the benchmark revision, Python and dependency versions. The candidate Alpha
metadata is package `0.1.0`, Algorithm `1.0`, profile `MVP_V1`, bundle `1.0`,
baseline `1.0.12`; the manifest records the observed candidate commit. Its public
availability has not been verified.

Install a target from an exact public Git revision when available. The adapter
checks installed distribution provenance and fails if the commit cannot be
verified. For an editable development checkout, callers may supply a local path
from ignored `benchmark.local.toml` configuration using
`TadrCoreAdapter.from_local_config(metadata, repository)`, or directly to
`TadrCoreAdapter(local_checkout=...)`. The TOML file has a `[target]` table with
a `checkout` string; relative paths resolve against the benchmark repository.
That checkout must be clean, at the pinned revision, and the imported package
must originate there. Local paths never belong in public campaign metadata.
Core is an optional system under test, not an automatic benchmark dependency.

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

## Running future campaigns

The next pass implements and reviews the actual scenario corpus and fresh-process
runner. There is deliberately no `run` command in this bootstrap. After that
review, select concrete scenarios and variants, pin both repositories, declare
warmups/repeats/timeouts/RSS interval and determinism contexts, then move the
manifest to `ready`. `planned_runs` derives a stable complete execution plan.
All data and working outputs go under `.work/`.

The freeze API accepts completed records, independent scenario specifications,
environment records and original canonical reports. It requires a clean benchmark
revision, complete run inventory and explicit publication review; it validates
and generates artifacts before creating a new frozen directory. It never executes
the target. Generated figures and tables are functions of the same raw records.

## Reproducing frozen results

No frozen campaigns exist yet. A future artifact contains `manifest.json`,
`environment.json`, `run_specs.json`, `runs.jsonl`, `summary.json`, scenario and
canonical report snapshots, tables, figures, `REPORT.md` and `checksums.sha256`.
Verify it with `tadr-benchmark verify-frozen results/campaigns/<campaign>` and use
its exact revisions, dependencies and execution plan with the future runner.
Update the root index with `tadr-benchmark results-index`. Schema migrations must
be explicit; readers reject unknown schema versions. See
[reproducibility](docs/reproducibility.md) and [result schema](docs/result_schema.md).

## Public data and licensing

Repository-authored code and documentation use Apache-2.0. No third-party data
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

1. Review this foundation, then implement and run `ALPHA_BENCHMARK_V1` explicitly.
2. Evaluate complete Algorithm v1 in `TADR_BENCHMARK_V1` with an expanded corpus.
3. Evaluate optimized Algorithm v1 in `TADR_BENCHMARK_V1_FINAL_RESULTS` while
   preserving the common historical subset.
4. Add calibrated and future Algorithm campaigns through versioned schemas and
   explicit comparisons, retaining historical outcomes.

See [CONTRIBUTING.md](CONTRIBUTING.md) for validation and Conventional Commits.
The repository license is [Apache-2.0](LICENSE).
