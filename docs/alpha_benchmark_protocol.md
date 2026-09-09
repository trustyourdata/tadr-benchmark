# Alpha benchmark protocol

The [frozen Alpha report](../results/campaigns/alpha_benchmark_v1/REPORT.md)
records the completed experiment and publication dated 2026-09-09.

The scientific design is fixed for this frozen campaign. Scientific-methodology
changes require explicit new review.

This document specifies the Alpha campaign inventory, source representations and
execution protocol. Scenario definitions and supporting infrastructure are
implemented. The source READY manifest is the preserved launch declaration, not
an assertion that execution remains pending. Package version is 0.1.0;
benchmark, result, instrumentation, scenario and annotation versions are 1.0.

## Inventory and independent construction

Publication retains original preregistered labels/results and the separately
approved post-execution normative adjudication. The full machine-readable overlay
and original history accompany the release; physical truth, scientific inputs
and reports remain unchanged. Publication revision never replaces either
scientific execution or historical aggregation revision.

`scenarios/families/ALPHA_BENCHMARK_V1.json` declares finite templates/axes.
`scenarios.families.expand_families` expands strict concrete specifications;
the campaign's exhaustive ID inventory is independently checked against them.

| Family | Concrete specifications |
| --- | ---: |
| Clean task controls | 8 |
| Numeric parsing | 24 |
| Feature/target missingness | 30 |
| Row/key duplicates | 36 |
| Class imbalance/support | 24 |
| Identifier cardinality/support | 16 |
| Timestamp validity/absence | 36 |
| Time-split applicability | 12 |
| Repeated entities and group suppression | 42 |
| Inference availability | 20 |
| Direct leakage and controls | 40 |
| Role/task negative controls | 6 |
| Lexical specificity challenge | 2 |
| Composites | 24 |
| Sampling placements | 36 |
| Scale selections | 14 |
| Total | 370 |

The legitimate measurement subfamily (six cases) and lexical challenge (two)
are specificity challenges outside the eight primary clean controls. Expected
INFO signals remain visible. Ten-thousand-row leakage controls include
`.n10000.` in their IDs; support49/support50/support200 retain their unambiguous
support-derived identities. The lexical ID is `challenge.lexical_paid.n10000` with
its representation suffix.

Integer recipes construct jointly unique coordinates, low-cardinality nuisance
features and task-specific targets/timestamps. No global RNG is used. Row-level
injection creates exact null/malformed masks, excess copies, complete composite
keys, repeated participants, class support, timestamp validity and target-derived
probes. Row/key excess and repeated-entity participant counts are distinct.
Rows are addressable without materializing a large table. Tests recount small
conditions and inspect isolated rows and mathematical masks for large definitions.

`scenarios.ledger` independently authors physical masks/counts from recipes.
`scenarios.expectations` separately authors pinned-Alpha severity/subject/gate/
suppression labels and research challenges. Neither reads target reports,
Findings or scores, imports target internals, or uses observed output to change
labels. Software tests prohibit live target imports and inspect this module
dependency boundary. The benchmark does not implement a scoring oracle.

Scenario snapshots and annotations follow the shared [freeze requirements](campaign_versioning.md).
Variant-specific sampling labels override the full-reference coarse
expectations for run evaluation; labels are never reconstructed from Findings.

## Logical and physical identity

Logical identity version 1.0 hashes a canonical JSON header containing ordered
schema and row count, then one canonical JSON array per ordered row. UTF-8,
sorted object keys, compact separators and LF are fixed. Null, string, bool and
int64 are distinct; schema/order/count changes change logical identity.

CSV and pqstr use identical nonmissing strings and nulls. CSV is uncompressed
UTF-8 without BOM, LF, comma delimiter, one header, standard double-quote
escaping and empty-field nulls. Literal empty nonmissing strings are rejected.
pqstr stores UTF-8 Arrow strings and native nulls. Native Parquet is limited to
the scale arm: int64 numeric fields, native bool flags, UTF-8 segment/date fields.
Its typed logical identity is distinct from string-only transports.

Parquet writer policy pins PyArrow 25.0.1, format 2.6, Zstandard level 3,
100000-row groups, data page version 1.0, 1 MiB page size, 1024 write batch,
statistics enabled, dictionary/page-index/page-checksum/byte-stream-split disabled,
and stored Arrow schema. Polars is pinned to 1.44.1. Alpha used the validated
Ubuntu 24.04 WSL2 execution environment described in
[reproducibility](reproducibility.md). Exact generated file bytes receive a separate SHA-256.
Changed serialization with unchanged logical rows never qualifies as identical
physical input. Strict performance comparison requires matching source hashes.

Generated sources and dataset manifests follow the
[public repository policy](public_repository_policy.md) and
[reproducibility requirements](reproducibility.md).

## Selective execution and terminal outcomes

Seven groups declare intended scenario/variant/context cells and repeats. Exact
IDs and literal prefixes select only from the finite campaign inventory; explicit
exclusions, unknown selections, overlaps and uncovered scenarios/axes are checked.
An independent Alpha coverage contract also rejects a missing sampling arm or
determinism repeat even when other cells still cover the scenario and axes.
There is no implicit global Cartesian workload when groups are present.

The nominal plan contains 578 primary invocations, including 13 warmups, plus
72 untimed public-bundle sampling diagnostic calls. Twelve existing scenarios
have six fresh-process contexts and two repeats. Thirteen regular scale cases
have one warmup and three measurements; the 5M case has zero warmups and two
measurements. These are planned counts, not observations or execution approval.

Sampling uses 300k rows. The mathematical bounded population is head rows below
50000 plus positions `50000 + floor(5*j/3)`, for j from 0 through 149999.
Placements in its unselected residues are explicit masks. Expected mode/ratio is
full/1 for the reference and sampled/2/3 for the bounded arm. Full-scan counters
retain full-data denominators. Auxiliary diagnostics use allowlisted primitives;
unavailable values are null with a reason. A successful standard repeat-zero
sampling arm requires a diagnostic companion. A failed primary has its typed
terminal failure instead of invented diagnostics.

Successful observations and adverse terminal outcomes use the shared
[result contracts](result_schema.md). Complete outcome accounting and the
distinction between infrastructure failure and valid adverse target outcomes
follow the [campaign freeze requirements](campaign_versioning.md).

## Execution prerequisites

Alpha used validated Linux x86_64, Python 3.11.9, POLARS_MAX_THREADS=4 under
Ubuntu 24.04 WSL2. A future execution host requires validation before READY. The [execution contract](execution.md) defines
worker barriers, the analyze-only timer, sampled process-tree RSS, context
acknowledgements, supervisor limits, recently prepared cache conditions and
immutable attempt history.

Source manifests retain a null benchmark SHA. Clean-tree resolution at execution
binds runs and the frozen manifest to that scientific execution revision. Historical
processing and publication assembly have separate recorded revisions; neither
replaces the execution binding. Frozen verification does not require the reader's
HEAD to match the execution revision.
The approved Core package/algorithm/profile/bundle/baseline metadata remain fixed.
The implementation is proprietary, with no public source URL or source-rebuild
claim. READY requires an available fingerprinted installation artifact and verified
installed target metadata, together with a validated scientific execution host.
The manifest records the verified artifact fingerprint and execution readiness. See the
[reproducibility boundary](reproducibility.md).

Execution and publication require review before measured tables or figures are
released. Software test success does not establish benchmark research outcomes.
