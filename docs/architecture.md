# Architecture

The benchmark owns evaluation. The target owns profiling, checks, thresholds,
Findings, scores and report serialization. Import only the public `tadr` facade
inside the Core adapter; do not add a dependency on target implementation modules.

| Contract | Responsibility |
| --- | --- |
| `ScenarioSpec` | Immutable experimental conditions, versioned generator/injectors and expectations |
| `GroundTruth` | Independently authored expected/absent Finding patterns and subjects, affected columns and gate expectation |
| `DatasetArtifact` | Working relative path, dataset/spec hashes and independently produced truth |
| `TargetAdapter` | Exact target metadata and unchanged canonical report transport |
| `RunSpec` | One planned repeat, variant and determinism context, with stable identity |
| `RunResult` | One completed execution, raw observations, instrumentation and evaluation |
| `EnvironmentInfo` | Sanitized allowlisted metadata and content-derived identity |
| `CampaignManifest` | Experimental scope, exact provenance and execution policies |
| `CampaignSummary` | Groups derived from measured records; warmups excluded |
| `ComparisonResult` | Eligibility, reasons and optional deltas with performance guardrails |
| `SamplingComparison` | Full-reference/sample agreement and score/risk/confidence deltas |

The installed package has no implicit target installation, source-path discovery
or benchmark execution. Generator/injector and executor protocols are extension
points for the next pass. The bootstrap's executable paths cover loading,
validation, environment capture, adapter transport, evaluation and reporting.
Unit tests use tiny in-memory harness fixtures; they are not Alpha scenarios.

## Transport and observations

`TargetReport` holds original canonical bytes and their parsed JSON object. The
adapter checks the installed package version and Git provenance before analysis.
Algorithm/profile/bundle/baseline metadata are reviewed declarations associated
with that exact revision, because these are not all exposed by the public facade.
The adapter propagates target errors. It does not repair reports or infer missing
checks. The current frozen-report validator recognizes the Core Alpha report
transport; future report contracts require an explicit adapter and schema review.

## Future execution boundary

The executor must launch a fresh worker with the configured hash seed, timezone
and Decimal context before target import. It must enforce timeout externally,
sample worker-and-child RSS, and measure wall time around target analysis only.
Generation, environment discovery and process startup are outside target wall
time. Process-tree RSS is a sampled sum, potentially including shared pages more
than once. Do not substitute a logical memory budget for this measurement.

Do not use a global RNG. A generator must return independently authored truth
and dataset/spec hashes. The runner must verify those artifacts, call the target,
preserve canonical bytes, record observations, and evaluate expected conditions.
Missing defects are completed experimental outcomes. Infrastructure failures
remain working diagnostics and cannot be submitted as successful `RunResult`s.

## Output boundaries

Generated datasets and working runs belong under `.work/`. A frozen destination
is `results/campaigns/<lowercase-campaign-id>/`; IDs cannot contain path separators.
Path helpers reject traversal and resolved escapes. Publication staging occurs
under `.work/freeze/`; final destinations cannot already exist.

Reporting groups by scenario/version, analysis variant and environment. Campaign
validation fixes the remaining dimensions within each group. Compare explicitly
matched records; do not pool non-equivalent hardware into one timing claim.
Declared check-scope additions are calculated from manifests, not from whether
a check happened to produce a Finding.
