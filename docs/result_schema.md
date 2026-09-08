# Result and environment schemas

Pydantic contracts live in `src/tadr_benchmark/models.py`. Unknown fields and
invalid types are rejected; non-finite numbers are forbidden. Get the exact JSON
schema with `tadr-benchmark schema CampaignManifest`, `ScenarioSpec`, `RunSpec`,
`RunResult`, `TargetMetadata` or `EnvironmentInfo`. Serialized objects sort keys;
arrays retain their declared order. Target canonical bytes use the target's own
serializer and are never reconstructed for hashing.

| Model | Required information |
| --- | --- |
| Campaign | Identity/status; protocol/scenario/result versions; flattened target provenance; benchmark/Python provenance; formats/tasks/scales; repeat/instrumentation policy; scenarios; variants; determinism contexts; planned scope |
| Scenario | Identity/version; description/task parameters; dimensions/format; generator/version/parameters; explicit RNG/seed pair; defect/injector definitions; expected/absent Findings; affected columns; gate expectation; rationale/tags |
| Run specification | Campaign/scenario identity and hash; stable run ID; phase/repeat; variant/constraints; complete determinism context |
| Result | Run specification; exact dataset/report hashes; flattened target and benchmark provenance; dimensions/task/format; mode/sample ratio; runtime/throughput/RSS; original report observations; independent detection outcome; environment ID and measurement policy |
| Environment | OS/version; architecture; Python; optional CPU model/core counts; RAM; allowlisted dependency versions |

All target provenance fields use the `target_` prefix: `name`, `package_version`,
`git_commit`, `repository_url_or_null`, `algorithm_version`, `threshold_profile`,
`bundle_protocol` and `baseline_revision`. Commits are full lowercase 40-character
Git SHA-1 IDs; content hashes are 64-character SHA-256. Public target URLs must
use HTTPS without credentials, query strings or fragments. Public reachability
is a separate reviewed claim; the model does not make network requests.

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

Environment IDs hash canonical allowlisted metadata. CPU model is currently
omitted at capture. Hardware equivalence approvals are supplied separately to
comparison functions; metadata equality does not automatically authorize a
speedup claim. Canonical reports are retained only after public-data review.

Summary records bind to the SHA-256 of canonical, run-ID-sorted `runs.jsonl`.
They exclude warmups and group only compatible scenario/variant/environment
records. Comparison schemas expose eligibility reasons and null deltas when
ineligible. Added/removed Findings are observations, not automatic labels of
improvement/regression. Sampling comparison records have their own eligibility
rules and preserve risk, score and confidence deltas.
