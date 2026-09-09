# Isolated execution and attempt history

The explicit `campaigns.runner.run_campaign` API accepts a resolved READY plan.
There is no campaign execution in pull-request CI. PLANNED manifests cannot run,
and the execution API never publishes or freezes results. Alpha still requires
its approved Linux host, instrumentation validation and target provenance.

## Execution schedule

Canonical RunSpecs remain sorted by stable run ID in persisted plans and ledger
bindings. The runner traverses a separate deterministic schedule: correctness,
ordinary sampling reference/bounded pairs, small determinism, sampled determinism,
regular scale, then 5M scale. Reordering does not change RunSpec or attempt identity.

Correctness and sampling scenarios use scenario-ID order, with the reference arm
first in each ordinary sampling pair. The two sampled-determinism cases receive
their bounded arm in the later determinism block. Determinism uses scenario-ID
order and contexts standard, hash_one, hash_fortytwo, timezone_berlin, decimal_low,
decimal_high, with repeat zero before repeat one.

Scale cells are ordered by rows, columns, task, representation and stable
scenario/variant/context identity. Each regular cell runs warmup zero followed
contiguously by measurements zero, one and two. The 5M cell runs only measurements
zero and one. Auxiliary diagnostics remain attached to eligible successful sampling
primaries outside timing. Resume traverses the same schedule, validates existing
bindings and returns selected outcomes without invoking the target again; it does
not repeat completed warmups or add measurements.

## Worker and measurement barriers

Linux cleanup retains the dedicated session identity established at worker
creation. It signals the session's process groups and waits for group disappearance,
including when the direct worker has already exited. The existing two-second
graceful and five-second forced cleanup waits bound this termination barrier;
elapsed time alone never establishes completion. Cleanup is idempotent after
success, rejects an observed reused leader identity, and reports an unverifiable
or incomplete barrier as an infrastructure instrumentation failure. Internal
session/process identifiers never enter public observations. Windows retains its
Job Object and descendant cleanup path. These cleanup waits do not change the
analysis timeout, RSS guardian or measurement brackets.

The supervisor starts a new interpreter for every primary invocation. Hash seed,
timezone and four Polars threads are supplied at process creation; timezone and
Decimal context are applied and verified before importing the public `tadr` API.
The worker acknowledges only allowlisted context fields. Linux uses `tzset` and
checks effective civil times. An unsupported context is an infrastructure failure.

Imports, target provenance checks and task/constraint construction precede the
ready acknowledgement. The supervisor samples baseline RSS and releases the
analyze barrier. `perf_counter_ns` brackets only public `tadr.analyze(...)`.
The returned report remains alive until the supervisor takes and acknowledges
the final RSS sample. Canonical serialization and persistence follow that barrier;
the original bytes remain untouched. Startup-ready latency is separate.

Headline `peak_rss_bytes` is the absolute maximum sampled sum for the worker and
recursively discovered live descendants, excluding the supervisor. Shared resident
pages can contribute more than once to this sum. Requested sampling interval is
10 ms for Alpha. Successful sample count, largest observed gap, baseline, vanished
descendants, discovery failures and completeness are retained. Unknown memory
does not become zero. `incremental_peak_rss_bytes` is an optional baseline-relative
diagnostic and does not replace the headline metric. Short-lived peaks can be missed.

Alpha uses supervisor timeouts of 600 seconds for correctness/determinism,
1800 for sampling, 3600 for ordinary scale, and 7200 for the 5M case. Its sampled
8 GiB RSS guardian aborts the worker tree; it is not a hard memory guarantee.
Windows uses a kill-on-close job object and Linux uses an isolated process group.
Normal exit, deadline/resource termination and handled interruption clean up the
worker tree. Timeout/resource outcomes carry observed elapsed time and policy
limits, without a fabricated completed runtime or report.

## Working sources and persistence

Sources are generated under ignored `.work/datasets/`. Reuse checks the complete
scenario recipe, independent logical rows/schema, source-file hash and saved
dataset receipt. A mismatch prevents reuse. Generation and external checksum
reads occur outside target timing. Cache conditions are recently prepared and
uncontrolled; these measurements do not support a cold-cache claim.

An exclusive working ledger binds the complete RunSpec plan, manifest, environment
and scenario inventory. Immutable reservations, completion records, original
reports, instrumentation and resolution receipts use flushed atomic writes.
An interrupted reservation remains an unresolved infrastructure attempt. Resume
checks provenance and original report hashes before returning completed work.
An immutable completion receipt also binds the reservation, selected outcome and
instrumentation bytes, so changed timing or RSS metadata cannot silently be reused.

`attempts.jsonl` is the authoritative operational history. Its typed version 1.0
records include deterministic attempt ordinal/identity, immediate retry lineage,
execution group, safe status/code, resolution state, the complete provenance-bound
typed outcome and its canonical SHA-256, and available instrumentation.

Only explicitly diagnosed and resolved infrastructure failures permit a retry.
Resolution uses an additional immutable receipt with an allowlisted code. A valid
report, typed target rejection, target analysis failure, approved timeout or resource
termination is final. The first valid scientific terminal outcome is selected;
there is no fastest-attempt, lowest-memory or favorable-score selection.

`runs.jsonl` and `failures.jsonl` contain that selected outcome exactly once per
RunSpec. Operational attempts and retries never increase scientific support,
determinism repetitions or performance repeat counts. Unresolved infrastructure,
orphan retries, changed provenance and missing/multiple selected outcomes block freeze.

## Auxiliary diagnostics

Separate fresh processes call public
`TADREngine.build_analysis_bundle(..., include_check_facts=True)` outside primary
timing. Exposed Algorithm/profile/bundle versions are checked against the target
pin. Shared profile, analysis mode and sample ratio must match the primary report.
The companion binds the primary report and shared profile hashes.
Typed bundle Decimal fields are compared at the pinned canonical report's numeric
precision; literal source strings retain their types. The original primary report
bytes are never regenerated. Canonical sample ratio is 0.6667 for the planned
200k/300k bounded population; the independent population definition remains exact.
Working diagnostic files have immutable checksum receipts, and resume verifies
their full primary provenance and shared profile before reuse.

Only named numeric primitive counts leave this path. Missing exposed values use
null plus `not_exposed`, and irrelevant metrics use null plus `not_applicable`.
The benchmark neither exports arbitrary bundle contents nor reconstructs absent
primitive counts. Auxiliary calls do not count as performance repeats.

## Software/protocol preflight

`tadr-benchmark preflight` explicitly executes six fixed NON-RESEARCH primary
calls: clean 10k CSV, numeric parse-boundary 10k string Parquet, the same 300k
missingness source under full-reference and bounded constraints, and 100k native
Parquet sources with 20 and 100 columns. Sampling arms also use separate untimed
public-bundle calls. No larger scale or campaign run can be selected by this command.

Ignored `.work/preflight/software_protocol_v1` retains the declared plan, original
reports, source hashes, instrumentation and a receipt. Development provenance
records the base Git revision and a hash of the actual working-source inventory.
An existing directory is never overwritten. After diagnosing and repairing a
diagnostic infrastructure fault, explicit `preflight --resume` retains prior
successful primary invocations and appends a linked plan/receipt. Completed
source/report/specification/instrumentation hashes are verified. Target failures
and mode/population mismatches cannot be resumed through this path.

Preflight observations are operational checks, excluded from campaign artifacts,
scientific aggregation and the results index. They do not establish Linux host
readiness or authorize a full Alpha campaign. Pull-request CI runs software tests
only; it never invokes this live preflight.

## Public output

Completed-run and diagnostic companion validation compare the observed sampling
mode and ratio exactly against the same expected public representation. The
expected ratio from the declared counts is rounded to four decimal places using
round-half-even. Observed report values are not rounded or rewritten, and no
numeric tolerance admits a different canonical value.

Post-execution validation may use a reviewed benchmark revision different from
the revision that produced the observations. Candidate processing records a
separate `processing_provenance.json` with `execution_git_commit`,
`processing_git_commit`, hashes of the immutable execution binding and typed
attempt export, and the processing environment. The processing revision must be
clean and committed. The campaign manifest, RunResults, attempts and diagnostic
records retain their original execution revision. This sidecar records processing
history; it does not authorize a freeze, change scientific support or replace the
execution binding. Freeze remains a separate reviewed operation.

No attempt, failure or instrumentation artifact contains process identifiers,
command lines, local paths, environment dumps, raw exception messages or tracebacks.
Strict contracts and public-safety checks apply before freezing. See the
[result schema](result_schema.md) and [freeze requirements](campaign_versioning.md).
