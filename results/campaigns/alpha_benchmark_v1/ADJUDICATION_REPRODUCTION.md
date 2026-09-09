# Adjudication reproduction

The ORIGINAL PREREGISTERED-LABEL RESULT is retained in root expectations.json,
runs.jsonl evaluation fields, summary.json, tables and original figures.
The ADJUDICATED PINNED-CONTRACT RESULT is supplemental: it records post-execution
normative corrections derived from the pre-existing Algorithm 1.0 contract.
No physical truth, primary-clean denominator, input, report or target execution changed.

## Artifact roles and original path mapping

Read [publication_inventory.json](publication_inventory.json) for the exact file
inventory and original_candidate_mapping. Original manifest.json, REPORT.md and
checksums.sha256 map respectively to history/ready_manifest.json,
history/candidate_REPORT.md and history/candidate_checksums.sha256. Every other
original candidate file retains its root-relative path.

The original scientific review is preserved under history. Its relative links
and the bundled ADJUDICATION_REVIEW.md links describe the historical operator
layout. Historical alpha_execution/candidate/X and ../candidate/X references map
to the original-candidate mapping above; alpha_execution/adjudication_v1/X maps
to adjudication_v1/X. Use the working links in the public [REPORT](REPORT.md).
Historical NOT READY/NOT FROZEN banners are original review history, not the
current publication state.

## Pure correction and evaluation reconstruction

No target package import is needed. Using the public benchmark code identified
in publication_provenance.json, verify_frozen validates the complete release;
verify_publication also supports an explicitly allowed unresolved dry-run stage.
Neither function invokes TADR.

To independently reconstruct the annotation transformation:

1. Load original scenarios, expectations and the full_reference opportunity frame
   from the original tables/scenario_matrix.csv.
2. Import only correct_annotation from the supplied alpha_v1_rules.py (public
   benchmark dependencies are required). Pass the scenario dictionary, original
   VariantExpectations dictionary and original frame. The function takes no report.
3. Compare the returned labels/frames to adjudication.json and
   corrected_normative_annotations.json. Keep the physical frame identical.
4. Select standard-context measured repeat zero for each correctness scenario.
   Apply benchmark evaluate_scenario/evaluate_frame to the unchanged canonical
   report and original/corrected normative labels separately. Compare results to
   adjudicated_scenario_metrics.json, both adjudicated tables and summary.json.
5. Retain 234/320 as original-label history and 320/320 as adjudicated conformance;
   retain the adverse practical_event_key.json observations and all physical misses.

The durable verifier reads the reviewed bundle as data and recomputes its metrics;
it never executes embedded operator scripts. The supplied pure rule module makes
the contract-based transformation independently inspectable/reconstructible.

## Supplemental script identities

| Script | SHA-256 |
| --- | --- |
| [alpha_v1_adjudicate.py](adjudication_v1/alpha_v1_adjudicate.py) | e7a6158920923107a0c367b5b3250b8a36d35a95300a72a099b31ac8d0e213c6 |
| [alpha_v1_review.py](adjudication_v1/alpha_v1_review.py) | 332577b17c64d0bdf92ef24c8d3fc9e01ce828835d112184a6e3a1d32fa1b1fc |
| [alpha_v1_rules.py](adjudication_v1/alpha_v1_rules.py) | 9b0e069505274238bcb5ebb4d96524dc27c931612b192473e0c6aed8ebd48a35 |

These operator bytes were not assigned a fictitious Git commit. Historical
benchmark processing revision remains 4887bd579d394de523bab0ccb227840d66447fd9.
The annotation-processing environment in adjudication_provenance.json is the
actual historical Windows environment, distinct from the original Linux scientific
execution and processing environments.

The original alpha_v1_adjudicate.py wrapper assumes its original working-directory
layout, a clean historical checkout and environment recapture. It is not a portable
one-command verifier of an arbitrarily relocated directory. Use the durable
publication verifier or pure reconstruction above; do not rewrite historical
environment metadata to match the reviewing machine.

## Reproduction and proprietary boundary

Public recipes/generators and identities support source regeneration, but generated
source CSV/Parquet files are excluded. Exact source bytes require the recorded writer
stack; logical equality alone is not exact-file equality. Original SVG reproduction
requires recorded rendering dependencies and stable selected attempt_id ordering.

The tadr-core implementation and wheel remain proprietary and are not distributed.
Execution requires authorized access to the fingerprinted wheel. Independent semantic
inspection of its implementation also requires authorized artifact access. Named
contract symbols/member hashes and reviewed rules do not provide public Core source
or source-level rebuild reproducibility. Public benchmark aggregation and the
annotation overlay can be inspected and reproduced without executing Core.
