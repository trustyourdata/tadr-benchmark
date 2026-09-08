# Security policy

Do not include credentials, private source values or machine-identifying metadata
in public reports. The benchmark processes files and invokes an installed target;
use reviewed inputs and isolated environments for future execution.

For a sensitive vulnerability or accidental disclosure, use the repository's
private vulnerability reporting feature if enabled. If unavailable, ask a
maintainer for a private reporting channel without posting sensitive details.
Do not open a public issue containing exploit credentials or disclosed data.

Maintainers should enable secret scanning, push protection and private reporting
where available. These repository-hosting settings are not configured by this
local bootstrap. Automated checks are defense in depth, not a disclosure guarantee.
