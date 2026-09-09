# TADR Benchmark

TADR Benchmark is an independent evaluation framework for deterministic,
task-aware dataset readiness assessment. Evaluation uses controlled experiments
and independently defined ground truth. The repository defines the scenarios and
measurement protocol, implements the evaluation tooling, and publishes the
resulting research artifacts. TADR Core (`tadr-core`, imported as `tadr`) is the
proprietary reference implementation under evaluation.

## Latest benchmark

**ALPHA_BENCHMARK_V1 — frozen 2026-09-09.** Scientific execution, review,
adjudication and immutable publication are complete.

Read the **[frozen Alpha report](results/campaigns/alpha_benchmark_v1/REPORT.md)**
for findings, tables, 11 SVG figures, limitations and provenance. The generated
[results index](RESULTS.md) is the registry for Alpha and future frozen campaigns.

| Alpha observation | Result and scope |
| --- | --- |
| Original preregistered-label whole-cell normative conformance | 234/320 |
| Adjudicated pinned-contract whole-cell normative conformance | 320/320; a separate post-execution annotation layer |
| Physical-condition detection | 246/314; 68 misses remain |
| Repeat determinism | 72/72 selected context/repeat pairs byte-identical; singleton groups are not repeat-tested |
| Sampling Finding-set agreement | 28/36 reference/bounded pairs; 8 disagreements |
| Strict format comparison | 42 mismatches, despite agreement in observed decision fields |

Pinned-contract conformance is not real-world detection effectiveness. Alpha
exposed adverse identifier warnings, sampling blind spots, strict format
mismatches and scoring limitations. These results describe a controlled synthetic
corpus; they do not establish population accuracy, calibration, production safety
or downstream model quality. Performance is specific to the recorded WSL2
environment, with sampled RSS, uncontrolled cache conditions and limited repeats.
The report preserves both normative result layers and all adverse findings.

## What this benchmark evaluates

The benchmark studies detection and negative controls, score and hard-gate
behavior, repeat determinism, bounded sampling, format differences and resource
cost. Alpha covers eleven Check Set A checks with fixed `MVP_V1` heuristics.
Its design contains 370 scenarios: 320 correctness cases, 36 sampling placements
and 14 scale cases.

See the [methodology](docs/methodology.md) for experimental units and limitations,
and the [Alpha protocol](docs/alpha_benchmark_protocol.md) for the fixed design.

## Why the benchmark is independent from TADR Core

Target unit tests cannot establish detection quality or analysis cost across an
independently constructed corpus. Physical conditions and original expectations
are defined independently before execution. The benchmark calls the target's
public API and retains its canonical report bytes. It does not copy Core scoring
formulas or infer physical truth from target Findings.

Alpha's approved normative adjudication is a separate post-execution layer based
on the pre-existing pinned contract. Original labels and results remain available;
physical truth and observations are unchanged. The
[opportunity policy](docs/opportunity_mapping.md) keeps physical detection,
check-specific conformance and suppression denominators separate.

## How it works

Versioned scenario families expand into concrete experiments. Deterministic
recipes generate inputs and independent truth; isolated workers capture target
reports and timing/resource observations. Evaluation produces tables and figures
from retained evidence. Reviewed campaigns are frozen with checksums and separate
execution, processing and publication provenance.

The [software architecture](docs/architecture.md) describes component ownership.
The [execution reference](docs/execution.md) covers scheduling, measurement
barriers and attempt history.

## Inspect and reproduce

Start with the [frozen report](results/campaigns/alpha_benchmark_v1/REPORT.md).
Public reports, tables, figures, scenario snapshots, recipes and dataset identities
support evidence inspection, verification and re-aggregation without Core.

Generated scientific source CSV/Parquet datasets are excluded from publication;
CSV result tables are published. Core source and wheel bytes are also excluded.
Re-execution requires authorized access to the exact fingerprinted target artifact
and the specified environment. Public source-level rebuilding of Core is not
available. See [reproducibility](docs/reproducibility.md) for these boundaries and
[adjudication reconstruction](results/campaigns/alpha_benchmark_v1/ADJUDICATION_REPRODUCTION.md)
for the original and corrected annotation layers.

With Python 3.11 or newer, install the benchmark independently of Core:

```sh
python -m venv .venv
# Activate .venv using your shell's activation command.
python -m pip install -e '.[test]'
python -m tadr_benchmark.cli verify-frozen results/campaigns/alpha_benchmark_v1
python -m tadr_benchmark.cli results-index --check
```

These checks do not execute the target. Byte-identical figure verification
requires the recorded rendering dependencies. On Windows,
`.venv\Scripts\python.exe` can replace `python` without activation.
Contributor checks and live execution prerequisites are documented separately.

## Documentation

The **[documentation index](docs/README.md)** provides reading paths for
researchers, artifact users, contributors and operators. Use the
[artifact/schema reference](docs/result_schema.md) to inspect data contracts and
[campaign versioning](docs/campaign_versioning.md) for lifecycle and provenance.

## Repository structure

| Location | Contents |
| --- | --- |
| [campaigns/](campaigns/README.md) | Source campaign manifests and launch declarations |
| [scenarios/](scenarios/README.md) | Versioned scenario families and construction definitions |
| [results/](results/README.md) | Immutable reviewed publications |
| [docs/](docs/README.md) | Research, reproduction and implementation guides |
| `src/tadr_benchmark/` | Independent benchmark package |
| `tests/` | Software fixtures and contract tests, not benchmark evidence |
| `.work/` | Ignored input datasets, working runs, logs and staging |

## Project status and roadmap

Alpha is the first frozen campaign. Its source READY manifest is retained as a
historical launch declaration; it does not describe a pending experiment.
The frozen publication cannot be overwritten or appended to. Scientific changes
require review and versioning under the campaign policy.

Future work includes complete Algorithm v1 (`TADR_BENCHMARK_V1`), optimized
Algorithm v1 (`TADR_BENCHMARK_V1_FINAL_RESULTS`) and later calibrated/Algorithm
campaigns. These require separate experiments and compatibility assessments;
no results are implied by the roadmap.

## Contributing, security and licensing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development checks and Conventional
Commits, [SECURITY.md](SECURITY.md) for disclosure guidance, and the
[public repository policy](docs/public_repository_policy.md) for content review.

Repository-authored code and documentation use [Apache-2.0](LICENSE). This license
does not cover proprietary TADR Core or grant rights to external datasets.
No third-party datasets are included; [THIRD_PARTY_DATA.md](THIRD_PARTY_DATA.md)
sets the review requirements for any future data release.
