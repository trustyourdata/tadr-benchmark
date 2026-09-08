# Campaign versioning and freeze

The campaign lifecycle is `planned` -> `ready` -> `frozen`. Planned manifests
may have no concrete scenarios or execution policy, but still declare candidate
target metadata and intended scope. A ready manifest requires an exact target
commit, Python version, concrete scenarios, variants, determinism
contexts, warmup/repeat counts and instrumentation policy. It also declares
whether the target revision is public or unavailable.

Tracked source manifests keep `benchmark_git_commit` null. `resolve_manifest`
requires a clean working tree, resolves existing HEAD, and binds execution and
frozen provenance to that SHA. Freeze checks that the revision remains clean and
unchanged; it never requires a self-referential SHA edit in a source manifest.
Alpha also requires provisioned/validated Linux x86_64 execution, Python 3.11.9,
four Polars threads and an explicit target-availability decision before READY.

Campaign IDs identify experiments. `benchmark_protocol_version` and
`result_schema_version` currently accept only `1.0`; `scenario_set_version` is
independent. Each scenario has its own version and canonical content hash.
Unknown protocol/result versions are rejected until an explicit reader migration
exists. The approved Alpha additions belong to initial 1.0 contracts and package
0.1.0; there is no compatibility reader for the unpublished bootstrap draft.
Historical compatibility starts with the first frozen campaign or explicit public
schema/package release. Never rewrite those historical records for a newer schema.

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

`campaigns.freeze.freeze` accepts reviewed artifacts; it does not run experiments.
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
