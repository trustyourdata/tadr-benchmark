# Contributing

Keep benchmark evaluation independent from target checks and scoring. Propose
scenario changes with independently defined truth and a methodological rationale.
Do not update frozen campaigns or reuse a scenario version for changed content.
Retain unexpected and unfavorable outcomes.

Use Python 3.11 or newer and a repository-local virtual environment:

```sh
python -m pip install -e '.[test]'
python -m pytest --tb=short
python -m pip check
git diff --check
tadr-benchmark validate
tadr-benchmark safety --include-untracked
tadr-benchmark results-index --check
```

Use Conventional Commits, for example `feat: add campaign validation` or
`docs: clarify sampling methodology`. Permanent filenames describe behavior or
components. Keep generated data, logs and scratch work in ignored `.work/`.
Do not commit editor state, local configuration or temporary review material.

PRs should explain behavior and methodology changes, versioning impact and
validation performed. Add behavioral tests for schema, provenance, determinism
and measurement integrity changes. Harness fixtures are software tests, not
benchmark findings. Lightweight CI never runs the 1M/5M campaign workloads.

Review the [public policy](docs/public_repository_policy.md) and
[dataset registry](THIRD_PARTY_DATA.md) before adding artifacts. Report security
issues according to [SECURITY.md](SECURITY.md).
