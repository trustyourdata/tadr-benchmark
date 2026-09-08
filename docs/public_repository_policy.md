# Public repository policy

Every tracked file must be appropriate for unrestricted publication. Keep
credentials, personal identifiers, confidential materials, private datasets,
developer paths and temporary implementation/review material out of the repository.
Use ignored `.work/` for generated datasets, runs, diagnostics and staging, and
ignored local configuration for development paths. No `.env` file is permitted.

Environment metadata is allowlisted by construction. Capture uses known OS and
architecture values, a numeric OS-release prefix, Python version, core counts,
total memory and explicitly enumerated package versions. It never reads user,
host, network or arbitrary environment values. CPU model is omitted rather than
trusting portable processor strings. Unknown schema fields are rejected.

The `safety` CLI scans Git-tracked files, including force-added ignored files;
`--include-untracked` adds nonignored candidates before a commit. Rules detect
obvious developer paths, network/machine identifiers, common secret formats,
credential URLs and restricted artifacts. Symlinks and unreviewable binaries are
rejected. Diagnostics identify rule/file without echoing matched content.

Frozen artifacts are scanned again before publication. Generated figure binaries
under frozen campaign directories require human visual/metadata review; SVG is
the bootstrap's output format and remains scanned text. Pattern-based validation
cannot prove the absence of secrets, identify all confidential prose or establish
data licensing. Review source values in canonical reports as well as metadata.

Do not add detector allowlists to bypass a real disclosure. Test detector behavior
with synthetic strings assembled at runtime, so test sources themselves do not
contain apparent leaked values. Publication requires explicit review in addition
to automated checks. No third-party datasets are included in this foundation.

Repository administrators should enable secret scanning and push protection where
available and configure branch protection requiring CI. These hosting settings
are not changed by local bootstrap work.
