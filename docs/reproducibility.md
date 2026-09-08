# Reproducibility

Install the benchmark independently of the target. Development dependency ranges
are not publication pins. Each execution environment must record resolved
dependency versions, Python version and sanitized hardware/OS metadata. Frozen
campaigns also require an exact benchmark revision, fingerprinted target artifact
and versioned scenario, generator, injector, protocol, RNG and determinism definitions.

## Reproducibility boundary

The benchmark methodology, synthetic datasets, ground truth, execution protocol,
and published evaluation artifacts are public. The evaluated TADR Core
implementation is proprietary. The exact implementation used for a campaign is
identified by versioned target metadata and a cryptographic fingerprint of the
execution artifact; the proprietary artifact and its source code are not
distributed by this repository.

| Layer | Reproduction boundary |
| --- | --- |
| Benchmark methodology and scenarios | Public definitions, opportunity mapping and evaluation/aggregation code describe the method independently of Core source. |
| Synthetic datasets and ground truth | Public deterministic generators, recipes, independent labels and identity rules support regeneration without Core. Generated datasets remain ignored working artifacts. |
| Execution protocol | Public worker, timing, RSS, context, scheduling and retry contracts describe execution. Re-execution requires authorized access to the exact target artifact and a validated environment. |
| Published evaluation artifacts | Public frozen records, checksums and derivation code support verification and re-aggregation without Core. Alpha has no published measurements yet. |
| Target implementation | Reproducibly identified by artifact SHA-256 and version metadata. Source-level rebuild reproducibility is not publicly available. |

## Target installation provenance

`target_source_distribution: proprietary` describes a permanent source-distribution
boundary. `target_repository_url_or_null` is null. Public source retrieval is not
required for READY or freeze. Private source revisions and build/release records
stay outside the public benchmark contract.

`target_installation_artifact_sha256` is the lowercase 64-character SHA-256 of the
exact private installation wheel bytes. Do not substitute a source revision or a
hash of an installation directory. PLANNED may leave this field null. READY,
success/failure records and frozen provenance require a resolved fingerprint;
the same value binds manifests, outcomes, attempts and diagnostic companions.

Before READY, select and retain the authorized wheel in the execution environment,
hash it, install it, and verify it with `TadrCoreAdapter.metadata()` in that
prepared environment. Supply its private location through `installation_artifact`
or ignored `benchmark.local.toml`: the `[target]` table accepts only an
`installation_artifact` string, with relative paths resolved against the repository.
The worker uses that configuration when no explicit artifact is supplied. No
installer, artifact discovery, source checkout or public download is implicit.

The adapter verifies the exact wheel hash, wheel package name/version, installed
package version, matching installed payload and distribution metadata bytes,
import origin, and public runtime `__version__`. The supported Core wheel contains
`tadr/` and its distribution metadata; the verifier rejects other layouts rather
than guessing installation mappings. Every worker rechecks before the timed
analysis barrier. Local paths, artifact bytes, source contents and private Git
records are never copied into public provenance.

The Alpha target contract fixes package `tadr-core` `0.1.0`, Algorithm `1.0`, profile
`MVP_V1`, AnalysisBundle protocol `1.0` and implementation baseline `1.0.12`.
Algorithm/profile/bundle/baseline are reviewed release declarations bound to the
selected artifact; the public facade does not expose all of these as runtime
metadata. Hash verification proves artifact identity, not the truth of arbitrary
release declarations. Review the authorized release record against this contract
and verify installed package/runtime identity before recording
`target_metadata_verified: true`. Record `target_artifact_verified: true` only
after verifying that the selected artifact is available and matches its hash and
installation. These flags retain the readiness review; they do not bypass worker
verification. Keep the private revision-to-build record outside public artifacts.

A missing artifact, unresolved/mismatched fingerprint, unverified metadata or
unvalidated execution environment blocks scientific execution. Proprietary source
distribution limits source-level reproduction claims; it does not block READY.
No exact Alpha execution artifact has been selected here, so its fingerprint and
verification flags remain unresolved and its status remains PLANNED.

Frozen artifacts include exact canonical reports and hashes, canonical scenario
snapshots, all requested run records including warmups, environment inventory,
the execution plan, complete `attempts.jsonl` operational history, selected
`runs.jsonl`/`failures.jsonl`, frozen `protocol.md`, summary, generated
tables/figures/report and checksums. Attempt retries are not independent results.
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
summary/table/figure/protocol/report content and the entire file inventory.
Figure reproduction uses the recorded Matplotlib/dependency environment,
fixed SVG hash salt, stable data ordering and no generation date. Exact SVG
identity across different rendering-library versions is not promised.

The explicit campaign execution API requires a resolved READY manifest and uses
a verified working ledger. See [execution](execution.md) for worker barriers,
cache conditions and resumability. Reproduction uses the archived benchmark revision, fingerprinted target artifact and the
execution plan on a controlled environment. Detection and score comparisons may span different environments;
performance claims require explicit reviewed equivalence and identical protocol.

The tracked source benchmark SHA stays null. Resolve a clean existing HEAD before
execution and bind all success/failure records to that revision; freeze resolves
and rechecks it. Initial schema/protocol versions remain 1.0 and package 0.1.0.
Alpha prefers Linux x86_64, Python 3.11.9 and POLARS_MAX_THREADS=4. Its actual host
and instrumentation validation remain unresolved; it is PLANNED, with no
measurements. Parquet writer behavior pins PyArrow 25.0.1;
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
