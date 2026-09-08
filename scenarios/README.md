# Scenario corpus

The Alpha scenario corpus will be designed in the next pass. No datasets or
executed scenarios are included at bootstrap. Tiny harness fixtures are defined
in tests and never registered as Alpha benchmark evidence.

Future definitions use versioned YAML `ScenarioSpec` records organized into
`clean`, `schema`, `quality`, `split`, `inference`, `leakage`, `composite` and
`scale` families as applicable. Declare generator/injector versions, parameters,
explicit randomness and independent expectations. A concrete scenario fixes
one format, task and scale. Use new versions for changed content and retain
historical snapshots in frozen campaigns.

See [methodology](../docs/methodology.md) and [schema](../docs/result_schema.md).
