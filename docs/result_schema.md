# Result and environment schemas

## Schema discovery and ownership

Pydantic contracts reject unknown fields, invalid types and non-finite numbers.
Inspect a model with `tadr-benchmark schema <ModelName>`; `tadr-benchmark schema --help`
lists the available names. For example:

```sh
tadr-benchmark schema RunResult
tadr-benchmark schema PublicationProvenance
tadr-benchmark schema PublicationInventory
```

The CLI exposes models from these modules under `src/tadr_benchmark/`:

| Module | Exposed models |
| --- | --- |
| `models.py` | `CampaignManifest`, `ScenarioSpec`, `RunSpec`, `RunResult`, `TargetMetadata`, `EnvironmentInfo` |
| `companions.py` | `RunFailure`, `OutcomeAccounting`, `ScenarioExpectations`, `PhysicalLedger`, `DatasetIdentity`, `WriterPolicy`, `InstrumentationRecord`, `DiagnosticRecord` |
| `execution/attempts.py` | `AttemptRecord` |
| `scenarios/families.py` | `FamilyDefinition`, `FamilyInventory` |
| `evaluation/metrics.py` | `ReportCoverage`, `DetectionMetrics` |
| `campaigns/publication.py` | `PublicationProvenance`, `PublicationInventory` |

Serialized objects sort keys; arrays retain their declared order. Target canonical
bytes use the target's own serializer and are never reconstructed for hashing.

## Artifact roles

| Model | Required information |
| --- | --- |
| Campaign | Identity/status; protocol/scenario/result versions; flattened target provenance; benchmark/Python provenance; formats/tasks/scales; repeat/instrumentation policy; scenarios; variants; determinism contexts; planned scope |
| Scenario | Identity/version; description/task parameters; dimensions/format; generator/version/parameters; explicit RNG/seed pair; defect/injector definitions; expected/absent Findings; affected columns; gate expectation; rationale/tags |
| Run specification | Campaign/scenario identity and hash; stable run ID; phase/repeat; variant/constraints; complete determinism context |
| Result | Run specification; logical dataset/source-file/report hashes; flattened target and resolved benchmark provenance; dimensions/task/format; mode/sample ratio; runtime/throughput/RSS; original report observations; independent detection outcome; environment ID and measurement policy |
| Failure | Run specification and resolved provenance; logical/source hashes; safe enumerated failure kind/stage/code/class; input-validation and adjudication state; optional censored elapsed/limit diagnostics; no fictional success observations |
| Attempt | Deterministic attempt ID/ordinal and retry lineage; execution group; safe status/category/code; explicit infrastructure resolution; selected-outcome flag; complete typed provenance-bound outcome and canonical checksum; available safe instrumentation |
| Expectations | Scenario snapshot hash; independent physical conditions/counts/masks; variant-specific Finding severity/subject/population, gates, suppression and category caps; separate research challenges and primary clean-control eligibility |
| Dataset identity | Scenario/version/hash; canonical logical schema/row count; separate logical and exact file hashes; explicit pinned writer policy |
| Instrumentation / diagnostics | Typed allowlisted monitor evidence and untimed public-bundle primitive values, with null/unavailable reasons and primary-run provenance |
| Environment | OS/version; architecture; Python; optional CPU model/core counts; RAM; allowlisted dependency versions |
| Report coverage | Finding evaluability; planned/evaluable/unevaluable opportunities by positive/negative class; successful/planned/pending reports; selected target failures by category; opportunity-weighted coverage ratios |
| Detection metrics | Report coverage plus conditional TP/FP/FN/TN and precision/recall/FPR; separate physical end-to-end detection yield; severity/localization/scenario metrics; mapped detector details |
| Publication provenance | Separate scientific execution, historical processing and publication assembly revisions; target fingerprint; original/adjudication checksum bindings; review hash; generator source hashes and publication environment |
| Publication inventory | Sorted, unique artifact paths and classifications; one-to-one mapping for reconstructing original candidate files |

Publication contracts are defined in `campaigns/publication.py`. A staged package
has an unresolved assembly revision; a frozen publication records its committed
assembly revision. The inventory distinguishes authoritative, derived and
supplemental adjudication artifacts. See [campaign versioning](campaign_versioning.md)
for validation and immutable assembly, and [reproducibility](reproducibility.md)
for historical evidence reconstruction.

## Provenance and observations

All target provenance fields use the `target_` prefix: `name`, `package_version`,
`source_distribution`, `repository_url_or_null`, `algorithm_version`,
`threshold_profile`, `bundle_protocol`, `baseline_revision` and
`installation_artifact_sha256`. Source distribution is typed as `proprietary`;
the public source URL is null. Private source revisions and locations are excluded.

The artifact fingerprint may be null only for PLANNED metadata. READY/frozen
manifests and success/failure records require a lowercase 64-character SHA-256
of exact installation artifact bytes. It propagates through manifests, outcomes,
attempts and diagnostics and must agree across bound provenance. No private
artifact or source publication is implied. See
[installation provenance](reproducibility.md#target-installation-provenance).

Alpha readiness separately records `target_artifact_verified` and
`target_metadata_verified`, alongside the host/instrumentation gates. Its approved
package/algorithm/profile/bundle/baseline tuple is validated. Public source retrieval
is not a readiness requirement. Initial contract versions remain 1.0.

Run measurements require strictly positive wall time, nonnegative measured RSS,
sample ratio in [0,1], positive input dimensions and throughput equal to input
rows divided by wall seconds. Readiness/confidence use the current public 0–100
report contract. Category risks and total risk are observations, not recalculated
penalties. Optional CPU/spill/scan/batch metrics use null when unavailable.

Finding IDs, severities and subjects are positionally aligned arrays in target
order. IDs must be unique. `hard_gates` retains the ordered `reason` strings of
reported caps whose type is `hard_gate`; `remediation_ids` retains plan IDs in
order. The frozen-report validator compares those fields with original reports.
No additional suppression or scoring semantics are introduced.

`detection_outcome` partitions positive expectations into matched/missed indexes,
records violated absent-expectation indexes, unexpected Finding IDs and optional
gate agreement. Relational validation recomputes this from scenario truth.
Expected affected columns describe the experimental condition; exact subject
expectations are used when subject-specific matching is required.

Derived `ReportCoverage` and `DetectionMetrics` contracts live in
`src/tadr_benchmark/evaluation/metrics.py`. Every ratio carries `numerator`,
`denominator` and nullable `value`; validators check count partitions and exact
ratios. Tables flatten these as named numerator/denominator/value columns.
The conditional rate names are `conditional_precision`, `conditional_recall` and
`conditional_fpr`. Planned and evaluable positive/negative opportunity counts,
successful-report coverage and failure-category counts accompany each rate.
`end_to_end_detection_yield` applies only to the controlled-condition track;
its normative value is null. See the authoritative
[opportunity and denominator policy](opportunity_mapping.md).

Without a canonical report, Finding evaluation is `UNEVALUABLE`: confusion counts
receive no entries, and observed Finding lists/counts, gate/suppression observations
and scenario normative conformance are null. Mixed aggregates are
`PARTIALLY_EVALUABLE`. Clean-control rows retain failed cells and their unevaluable
negative opportunities. Pending reports remain distinct in partial working queries;
freeze rejects incomplete plans. No selected failure or operational retry is
converted into an FN, TN or an additional scientific observation.

Environment IDs hash canonical allowlisted metadata. CPU model is currently
omitted at capture. Hardware equivalence approvals are supplied separately to
comparison functions; metadata equality does not automatically authorize a
speedup claim. Canonical reports are retained only after public-data review.

Summary records bind to the SHA-256 of canonical, run-ID-sorted `runs.jsonl`.
They also bind to `failures.jsonl` and disclose successful/adverse terminal counts.
They bind separately to `attempts.jsonl` and disclose operational attempt, retry
and resolved-infrastructure counts. The selected attempt's complete outcome must
agree exactly with its record in `runs.jsonl` or `failures.jsonl`. Attempt schema
version is 1.0; scientific result multiplicity is unchanged. See
[execution and retry semantics](execution.md).
An all-adverse campaign can have zero successful summary groups and no performance
figure; failures cannot be silently dropped from coverage. Fine-grained labels,
dataset identities, monitor records and diagnostic snapshots are checksummed and
relationally validated at freeze. Initial result/protocol versions remain 1.0.
They exclude warmups and group only compatible scenario/variant/environment
and determinism-context records. Raw performance repeat values remain available;
the two-run 5M policy is marked weak evidence. Comparison schemas expose eligibility reasons and null deltas when
ineligible. Added/removed Findings are observations, not automatic labels of
improvement/regression. Sampling comparison records have their own eligibility
rules and preserve risk, score and confidence deltas.
