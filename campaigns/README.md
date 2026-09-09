# Campaign manifests

[ALPHA_BENCHMARK_V1.yaml](ALPHA_BENCHMARK_V1.yaml) preserves the source READY launch
declaration, including its historical `READY / NOT YET RUN` note. Alpha has since
completed execution, review, adjudication and immutable publication. Its current
status and evidence are in the [results index](../RESULTS.md) and
[frozen report](../results/campaigns/alpha_benchmark_v1/REPORT.md).

The declaration fixes 370 scenario IDs and seven selective execution groups,
with repeat, context, variant and instrumentation policies. Its finite design
contains 578 primary calls and 72 auxiliary diagnostics. Validation does not
execute that plan or create an implicit Cartesian workload.

The proprietary target is identified by public version metadata and a verified
installation-artifact fingerprint. Source manifests retain a null benchmark Git
SHA. Execution resolves a clean committed revision into runtime evidence;
publication records a separate assembly revision without replacing execution or
historical processing provenance. The source launch declaration stays unchanged.

See [campaign versioning](../docs/campaign_versioning.md) for lifecycle fields and
immutability, and [execution](../docs/execution.md) for the operator contract.
Validate definitions with `tadr-benchmark validate`. Scientific-methodology
changes after READY require explicit new review.
