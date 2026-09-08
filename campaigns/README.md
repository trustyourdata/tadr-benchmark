# Campaign manifests

`ALPHA_BENCHMARK_V1.yaml` remains PLANNED / NOT YET RUN. It lists 370 concrete IDs
and seven selective execution groups, with explicit repeat/context/variant and
instrumentation policies. Its 578 primary calls and 72 auxiliary diagnostic calls
are a finite research plan; validation never executes them. The proprietary target
has fixed public version metadata and a null source URL. Its installation-artifact
fingerprint remains null while PLANNED; an available, fingerprinted artifact and
verified installed target metadata are required before READY. Source benchmark Git provenance
stays null until a clean existing HEAD is resolved at execution/freeze time.

See [versioning](../docs/campaign_versioning.md) for the lifecycle and required
ready/frozen fields. Validate definitions with `tadr-benchmark validate`.
Selected scenarios define concrete format/task/scale cases; no implicit full
Cartesian workload is generated from planned scale points.
