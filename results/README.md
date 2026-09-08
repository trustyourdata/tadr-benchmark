# Reviewed research artifacts

No campaigns have been run or frozen. Do not create empty measurement files,
placeholder charts or fabricated performance values here.

Future frozen output uses `results/campaigns/<lowercase-campaign-id>/` with:

```text
manifest.json
environment.json
run_specs.json
runs.jsonl
summary.json
scenarios/*.json
reports/*.json
tables/summary.csv
figures/runtime.svg
REPORT.md
checksums.sha256
```

Canonical reports must contain only reviewed public source values. Generated
datasets remain under ignored `.work/datasets/`. Verified comparison artifacts
may later live in `results/comparisons/`. Large immutable artifacts need a
separately reviewed release transport, checksums and registry reference.

Root [RESULTS.md](../RESULTS.md) is generated from validated campaign manifests
and frozen artifacts by `tadr-benchmark results-index`. Frozen contents cannot
be overwritten; corrections require a new campaign identity.
