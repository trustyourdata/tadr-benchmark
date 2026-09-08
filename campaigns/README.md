# Campaign manifests

`ALPHA_BENCHMARK_V1.yaml` is a planned scope skeleton, not an execution request.
It intentionally has no scenario IDs, repetition counts, instrumented execution
policy or benchmark commit yet. The observed candidate target commit is pinned;
its public retrieval status remains unverified.

See [versioning](../docs/campaign_versioning.md) for the lifecycle and required
ready/frozen fields. Validate definitions with `tadr-benchmark validate`.
Selected scenarios define concrete format/task/scale cases; no implicit full
Cartesian workload is generated from planned scale points.
