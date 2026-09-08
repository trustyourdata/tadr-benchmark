# Scenario corpus

Phase 1 implements the approved 370-case Alpha corpus as versioned family
specifications in `families/ALPHA_BENCHMARK_V1.json`. No campaign datasets or
executed scenarios are included. Tiny software fixtures and small in-memory
construction recounts are never registered as benchmark evidence.

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

Before a first public release/freeze, approved draft semantics can be corrected
within initial version 1.0. Historical scenario snapshots must remain immutable
once compatibility obligations begin. See the [Alpha benchmark protocol](../docs/alpha_benchmark_protocol.md).

See [methodology](../docs/methodology.md) and [schema](../docs/result_schema.md).
