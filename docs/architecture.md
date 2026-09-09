# Architecture

The benchmark owns evaluation. The target owns profiling, checks, thresholds,
Findings, scores and report serialization. Import only the public `tadr` facade
inside the Core adapter; do not add a dependency on target implementation modules.

| Contract | Responsibility |
| --- | --- |
| `ScenarioSpec` | Immutable experimental conditions, versioned generator/injectors and expectations |
| `GroundTruth` | Independently authored expected/absent Finding patterns and subjects, affected columns and gate expectation |
| `DatasetArtifact` / `DatasetIdentity` | Separate logical-row and exact source-byte hashes, writer policy and spec provenance |
| `TargetAdapter` | Exact target metadata and unchanged canonical report transport |
| `RunSpec` | One planned repeat, variant and determinism context, with stable identity |
| `RunResult` | One completed execution, raw observations, instrumentation and evaluation |
| `RunFailure` / `OutcomeAccounting` | Typed adverse terminal outcomes, unresolved/infrastructure failures and exact plan coverage |
| `AttemptRecord` | Immutable operational history, explicit infrastructure resolution and exactly one selected scientific outcome per RunSpec |
| `ScenarioExpectations` | Physical ledger, pinned normative labels and separate research challenges |
| `InstrumentationRecord` / `DiagnosticRecord` | Allowlisted monitor evidence and untimed diagnostic companions |
| `EnvironmentInfo` | Sanitized allowlisted metadata and content-derived identity |
| `CampaignManifest` | Experimental scope, exact provenance and execution policies |
| `CampaignSummary` | Groups derived from measured records; warmups excluded |
| `ComparisonResult` | Eligibility, reasons and optional deltas with performance guardrails |
| `SamplingComparison` | Full-reference/sample agreement and score/risk/confidence deltas |

The installed package has no implicit target installation, source-path discovery
or benchmark execution. Versioned family expansion, row-addressable
construction/injection and pinned CSV/Parquet writers supply isolated workers
through a verified source cache and attempt ledger. Tests recount small constructed conditions and inspect scale schemas
and mathematical placement ledgers without materializing research-scale datasets.

## Transport and observations

`TargetReport` holds original canonical bytes and their parsed JSON object. The
adapter checks the private installation artifact hash, installed payload, and
package/runtime identity before analysis. Algorithm/profile/bundle/baseline
metadata are reviewed release declarations bound to that artifact, because these
are not all exposed by the public facade. See the
[target provenance contract](reproducibility.md#target-installation-provenance).
The adapter propagates target errors. It does not repair reports or infer missing
checks. The current frozen-report validator recognizes the Core Alpha report
transport; future report contracts require an explicit adapter and schema review.

## Execution boundary

The supervisor, worker, source cache, ledger and auxiliary diagnostic path follow
the [execution contract](execution.md). Public target import occurs only in a
fresh context-controlled worker. Target logical planning budgets and measured
process-tree RSS remain separate quantities.

Do not use a global RNG. A generator must return independently authored truth
and dataset/spec hashes. The runner must verify those artifacts, call the target,
preserve canonical bytes, record observations, and evaluate expected conditions.
Missing defects are completed experimental outcomes. Infrastructure failures
block freeze. Valid adverse target outcomes use adjudicated `RunFailure` records;
they count toward terminal coverage and never invent a report or successful timing.

## Output boundaries

Generated datasets and working runs belong under `.work/`. A frozen destination
is `results/campaigns/<lowercase-campaign-id>/`; IDs cannot contain path separators.
Path helpers reject traversal and resolved escapes. Publication staging occurs
under `.work/freeze/`; final destinations cannot already exist.

Reporting groups by scenario/version, analysis variant, context and environment. Campaign
validation fixes the remaining dimensions within each group. Compare explicitly
matched records; do not pool non-equivalent hardware into one timing claim.
Declared check-scope additions are calculated from manifests, not from whether
a check happened to produce a Finding.
