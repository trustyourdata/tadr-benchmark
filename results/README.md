# Frozen research artifacts

[ALPHA_BENCHMARK_V1](campaigns/alpha_benchmark_v1/REPORT.md) is frozen as of
2026-09-09. Its publication contains measured outcomes, canonical reports,
CSV result tables, 11 SVG figures, provenance and scientific/adjudication history.
The generated [results index](../RESULTS.md) is the longitudinal campaign registry.

## Reading the publication

The frozen [REPORT.md](campaigns/alpha_benchmark_v1/REPORT.md) is the public entry
point. It distinguishes original preregistered results from the separately
adjudicated normative layer and retains physical-condition findings and limitations.
Root tables and figures preserve original-label results; the adjudication bundle
contains the corrected normative layer.

The [publication inventory](campaigns/alpha_benchmark_v1/publication_inventory.json)
and verification tooling define the complete artifact set and original-candidate
mapping. [Publication provenance](campaigns/alpha_benchmark_v1/publication_provenance.json)
records assembly separately from scientific execution and historical processing.
The [reproduction note](campaigns/alpha_benchmark_v1/ADJUDICATION_REPRODUCTION.md)
explains archived paths and adjudication reconstruction. Historical banners and
relative links remain unchanged evidence.

## Publication boundaries

Frozen campaigns live under `results/campaigns/<lowercase-campaign-id>/`.
All contents are immutable: they cannot be overwritten, deleted or appended to.
Corrections require a new campaign identity under the
[campaign policy](../docs/campaign_versioning.md). Do not add empty measurement
files, placeholder charts or fabricated values.

Canonical reports contain reviewed public source values. Generated scientific
source CSV/Parquet datasets remain under ignored `.work/datasets/`; public recipes,
scenario snapshots and dataset identities support regeneration. CSV result tables
are published. Proprietary Core source and wheel bytes are excluded. See the
[reproducibility boundary](../docs/reproducibility.md).

Use `tadr-benchmark verify-frozen results/campaigns/alpha_benchmark_v1` to verify
Alpha. `tadr-benchmark results-index --check` checks the generated registry without
writing it; `results-index` updates it through tooling after verified freeze.
Neither command executes the target. Verification requires the recorded rendering
dependencies for byte-identical figures.

Future comparison artifacts and external transport for large publications require
separate review, compatibility assessment, checksums and registry references.
