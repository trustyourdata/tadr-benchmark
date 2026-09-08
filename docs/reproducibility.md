# Reproducibility

Install the benchmark independently of the target. Development dependency ranges
are not publication pins. Each execution environment must record resolved
dependency versions, Python version and sanitized hardware/OS metadata. Frozen
campaigns also require exact benchmark and target commits and versioned scenario,
generator, injector, protocol, RNG and determinism definitions.

The Alpha manifest records an observed candidate Core revision and current public
contract metadata. Its URL is null because public retrieval was not verified.
`unverified` cannot become a ready/frozen campaign. Before execution, either
verify public availability and supply the repository URL with `public_revision`,
or explicitly use `target_unavailable`. Do not imply external reproducibility
when source retrieval is unavailable.

The Core adapter verifies Git provenance from an installed VCS distribution's
`direct_url.json`. A local editable checkout may instead be passed explicitly as
`local_checkout`; it must be clean, at the configured commit, and contain the
imported module. `TadrCoreAdapter.from_local_config(metadata, repository)` reads
ignored `benchmark.local.toml` with a `[target]` table and one `checkout` string;
relative paths resolve against the benchmark repository. No path is embedded in
campaign/result metadata. No local
configuration file is created by bootstrap, and the CLI does not silently install
or discover a target. The target repository is treated as read-only.

Frozen artifacts include exact canonical reports and hashes, canonical scenario
snapshots, all requested run records including warmups, environment inventory,
the execution plan, summary, generated tables/figures/report and checksums.
Generated source datasets remain in `.work/datasets/`; generators reproduce
logical rows from the same family snapshots and versioned integer recipes.
`logical_dataset_sha256` hashes canonical schema/ordered rows independently of
container bytes; `source_file_sha256` hashes exact input bytes. CSV/string-Parquet
equivalence can share the logical hash, while container hashes differ. Regenerated
Parquet with changed serialization remains a different physical input even if its
logical hash matches. Strict performance comparison requires identical source hashes.
For artifacts too large for Git, a later explicit release mechanism should retain
immutable manifest, checksums and release reference in the repository. Such an
external-artifact transport is not implemented at bootstrap.

Use `verify-frozen` before analyzing a frozen artifact. The verifier rechecks
schemas, relational consistency, original report hashes, run completion, derived
summary/table/report content and the entire file inventory. Figure bytes are
checksummed; reproduction uses the recorded Matplotlib/dependency environment,
fixed SVG hash salt, stable data ordering and no generation date. Exact SVG
identity across different rendering-library versions is not promised.

The full campaign runner is intentionally deferred. Once implemented and reviewed,
reproduction will use the archived revisions and execution plan on a controlled
environment. Detection and score comparisons may span different environments;
performance claims require explicit reviewed equivalence and identical protocol.

The tracked source benchmark SHA stays null. Resolve a clean existing HEAD before
execution and bind all success/failure records to that revision; freeze resolves
and rechecks it. Initial schema/protocol versions remain 1.0 and package 0.1.0.
Alpha prefers Linux x86_64, Python 3.11.9 and POLARS_MAX_THREADS=4. Its actual host,
instrumentation validation and public target retrieval remain unresolved; it is
PLANNED, with no measurements. Parquet writer behavior pins PyArrow 25.0.1;
Polars is pinned to 1.44.1. These pins do not claim the future Linux host is validated.

Current lightweight verification:

```sh
python -m pytest --tb=short
python -m pip check
git diff --check
python -m tadr_benchmark.cli validate
python -m tadr_benchmark.cli safety --include-untracked
python -m tadr_benchmark.cli results-index --check
```
