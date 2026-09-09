# Campaign versioning and freeze

The campaign lifecycle is `planned` -> `ready` -> `frozen`. Planned manifests
may have no concrete scenarios or execution policy, but still declare candidate
target metadata and intended scope. A ready manifest requires an exact target
installation artifact fingerprint, Python version, concrete scenarios, variants,
determinism contexts, warmup/repeat counts and instrumentation policy.

Tracked source manifests keep `benchmark_git_commit` null. `resolve_manifest`
requires a clean working tree, resolves existing HEAD, and binds scientific
execution to that SHA. Publication has a separate revision; it never replaces
the execution SHA or requires a self-referential source SHA edit.
Alpha also requires provisioned/validated Linux x86_64 execution, Python 3.11.9,
four Polars threads before READY. The selected private target artifact must be
available, fingerprinted, and verified against installed package/runtime metadata;
the release declarations must match the approved Alpha target contract. Readiness
records artifact and metadata verification separately from host/instrumentation
validation. Public source retrieval is not required for the proprietary target.
See [target installation provenance](reproducibility.md#target-installation-provenance).
All other provenance, environment and completion gates apply.

Campaign IDs identify experiments. `benchmark_protocol_version` and
`result_schema_version` currently accept only `1.0`; `scenario_set_version` is
independent. Each scenario has its own version and canonical content hash.
Unknown protocol/result versions are rejected until an explicit reader migration
exists. The approved Alpha additions belong to initial 1.0 contracts and package
0.1.0; there is no compatibility reader for the earlier unpublished draft.
Historical compatibility starts with the first frozen campaign or explicit public
schema/package release. Alpha is now frozen and those compatibility obligations
apply. Never rewrite historical records for a newer schema.

The selected scenario list defines concrete task/format/scale cases. Execution
expands these cases over declared variants, determinism contexts and warmup/
measurement repetitions only. Selective execution groups replace the global
Cartesian product when present. Selectors use exact IDs/prefixes and explicit
exclusions over the finite campaign inventory; unknown/empty selections,
overlapping scenario/variant/context cells and uncovered scenarios/axes fail.
Each group has its own repeat and instrumentation policy. Stable run IDs hash
the campaign/scenario/version/variant/context/phase/repeat identity. An
empty planned scenario list cannot execute. A new check gets new scenarios;
historical scenarios remain available through frozen snapshots.

## Freeze requirements

### Complete Alpha publication

Alpha uses `campaigns.publication.freeze_publication(root, sources, frozen_date,
public_reviewed=True)`. `PublicationSources` supplies the original candidate,
complete adjudication directory and original scientific review. Generic freeze
rejects Alpha rather than omitting those companions.

Three identities remain separate: scientific execution, historical post-execution
processing, and clean publication assembly. Typed `publication_provenance.json`
binds each role, target fingerprint, original/adjudication checksum manifests,
original review, source-file generator hashes and actual publication environment.
Runs always retain execution SHA; verification never requires the reviewer's
HEAD to equal it. Use the publication generator code identified by content and
its recorded rendering dependencies.

`stage_publication(root, sources, destination)` supports pre-commit review under
`.work/`. Its publication state is staged, assembly revision is null, and the root
manifest remains READY with no freeze date. Explicitly validate with
`verify_frozen(..., check_directory_name=False, allow_staged=True)`; default
verification rejects unresolved stages. Staging never creates a results directory
or assigns a fictitious revision to uncommitted code.

The stage includes all original authoritative evidence and execution/processing
companions, original summary/tables/figures, historical READY manifest/candidate
report/checksums and scientific review, the entire existing `adjudication_v1/`
bundle, public report, publication provenance/inventory and
`ADJUDICATION_REPRODUCTION.md`. The inventory gives the exact original-candidate
reconstruction mapping. Outer checksums cover the inner checksum manifest too.

The frozen root manifest changes only status/date, retaining scientific
execution and target/environment fields. Original labels and results remain
historical evidence beside the post-execution normative overlay. Verification
checks archive reconstruction, provenance, complete overlay/inner checksums,
recomputed normative metrics, unchanged physical frames, practical event_key
evidence, all original tables/figures and deterministic public report/note.
Embedded operator scripts and target code are never executed.

Generation and verification use stable selected attempt-ID plotting order to
preserve original SVG bytes at tied x-values. All checks run before atomic
rename; the overlay cannot be appended afterward. Sources, private target bytes,
local configuration and preflight artifacts remain excluded. A staged package
requires a fresh clean, explicitly authorized assembly to become a release.

### Generic artifacts and common safeguards

`campaigns.freeze.freeze` accepts generic reviewed artifacts; it does not run experiments.
It requires a ready manifest, explicit `public_reviewed=True`, a clean benchmark
working tree at its recorded revision, matching target/environment provenance,
complete requested warmups and measurements as successful reports or adjudicated
adverse target outcomes, independent truth for every scenario, required companions,
valid original report hashes and a passing public-safety scan. Missing, pending or
unresolved infrastructure outcomes block freeze. Successful reports with missed Findings,
false positives or deterministic mismatches remain valid adverse research evidence.

It generates canonical scenario/report snapshots, the execution plan, raw run
records, summary, table, figure, report and checksums in ignored staging. These
are verified before a new frozen directory is created. Existing destinations
cannot be overwritten. Deterministic mismatches and missed defects remain
research outcomes in the published data, not infrastructure failures.

The authoritative artifact set is `manifest.json`, `environment.json`,
`run_specs.json`, `runs.jsonl`, `failures.jsonl`, `attempts.jsonl`, `scenarios/*.json`,
`expectations.json`, `dataset_manifest.json`, `reports/*.json`, `diagnostics/*.json`,
`instrumentation.jsonl`, `protocol.md`, `summary.json`, generated `tables/*`,
eligible `figures/*`, `REPORT.md` and `checksums.sha256`.

Attempt validation checks declared RunSpecs, sequential ordinals, immediate retry
lineage, exact outcome checksums, unchanged provenance, explicit infrastructure
resolution and one selected outcome per required RunSpec. Selected instrumentation
must agree with the authoritative monitor companion. Resolved failed attempts
remain permanently visible; retries never become extra scientific observations.
See [execution](execution.md) for the complete retry policy.

`verify-frozen` checks inventory, hashes, schemas, provenance, completion and
regenerated summaries, all table/figure bytes, protocol and report. Detection tables
derive conditional detection rates, planned opportunity coverage and separate
end-to-end physical detection yield from the declared plan and selected outcomes.
Failure-category and unevaluable-opportunity support cannot be removed by editing
a derived table. Figure regeneration
requires the recorded rendering dependencies. CI also compares frozen directories with
the pull-request base using `verify-history`, rejecting edits or deletions even
if a contributor rewrites the checksums. The active scenario corpus cannot
change the content of an ID/version already present in frozen snapshots.

Checksums detect corruption; they are not signatures or independent proof that
measurements were performed honestly. Publication review remains necessary.
After freezing, correct methodology or results by issuing a new campaign ID
with an explanation, preserving the historical artifact.
