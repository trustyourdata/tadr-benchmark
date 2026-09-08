# Campaign versioning and freeze

The campaign lifecycle is `planned` -> `ready` -> `frozen`. Planned manifests
may have no concrete scenarios or execution policy, but still declare candidate
target metadata and intended scope. A ready manifest requires exact benchmark
and target commits, Python version, concrete scenarios, variants, determinism
contexts, warmup/repeat counts and instrumentation policy. It also declares
whether the target revision is public or unavailable.

Campaign IDs identify experiments. `benchmark_protocol_version` and
`result_schema_version` currently accept only `1.0`; `scenario_set_version` is
independent. Each scenario has its own version and canonical content hash.
Unknown protocol/result versions are rejected until an explicit reader migration
exists. Never change historical records to make them fit a newer schema.

The selected scenario list defines concrete task/format/scale cases. Execution
expands these cases over declared variants, determinism contexts and warmup/
measurement repetitions only. Stable run IDs hash that complete identity. An
empty planned scenario list cannot execute. A new check gets new scenarios;
historical scenarios remain available through frozen snapshots.

## Freeze requirements

`campaigns.freeze.freeze` accepts reviewed artifacts; it does not run experiments.
It requires a ready manifest, explicit `public_reviewed=True`, a clean benchmark
working tree at its recorded revision, matching target/environment provenance,
complete requested warmups and measurements, independent truth for every
scenario, valid original report hashes and a passing public-safety scan.

It generates canonical scenario/report snapshots, the execution plan, raw run
records, summary, table, figure, report and checksums in ignored staging. These
are verified before a new frozen directory is created. Existing destinations
cannot be overwritten. Deterministic mismatches and missed defects remain
research outcomes in the published data, not infrastructure failures.

`verify-frozen` checks inventory, hashes, schemas, provenance, completion and
regenerated summaries/tables/reports. CI also compares frozen directories with
the pull-request base using `verify-history`, rejecting edits or deletions even
if a contributor rewrites the checksums. The active scenario corpus cannot
change the content of an ID/version already present in frozen snapshots.

Checksums detect corruption; they are not signatures or independent proof that
measurements were performed honestly. Publication review remains necessary.
After freezing, correct methodology or results by issuing a new campaign ID
with an explanation, preserving the historical artifact.
