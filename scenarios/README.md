# Scenario corpus

This directory defines the 370-case Alpha corpus through versioned family
specifications in [families/ALPHA_BENCHMARK_V1.json](families/ALPHA_BENCHMARK_V1.json).
Generated scientific source datasets are excluded from publication. Executed
scenario snapshots and scientific evidence are retained in the
[frozen Alpha publication](../results/campaigns/alpha_benchmark_v1/REPORT.md).
Tiny software fixtures and small in-memory construction recounts are not
registered as benchmark evidence.

Each family declares an ID template and finite, explicit axes. Deterministic
expansion produces strict `ScenarioSpec` objects with task roles, dimensions,
versioned recipes, physical counts/masks and independent contract labels.
The campaign's concrete ID inventory is checked against expansion. Freeze retains
each expanded scenario snapshot and checksum, plus a typed expectations companion.
Construction uses no RNG: algorithm and seed are explicitly null.

Representations `csv` and `pqstr` share canonical string/null logical rows;
`pqnative` is the separate native scale arm. Source-format values remain csv/parquet.
The corpus contains 320 correctness cases, 36 sampling placements and 14 scale
points. Measurement and lexical-name specificity challenges are excluded from the
eight primary clean-control registrations; expected INFO Findings remain visible.

Alpha is frozen, so its scenario snapshots and versioned content are immutable.
The pre-first-release window for correcting draft semantics within version 1.0
has closed. Changes follow the [versioning policy](../docs/campaign_versioning.md). See the [Alpha benchmark protocol](../docs/alpha_benchmark_protocol.md).

See [methodology](../docs/methodology.md) and [schema](../docs/result_schema.md).
