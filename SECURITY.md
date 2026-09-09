# Security policy

## Reporting a sensitive issue

Do not put credentials, private source values, disclosed data or machine-identifying
metadata in public issues or reports. Use the repository's private vulnerability
reporting feature if it is available.

This repository does not publish a separate private contact address. If private
reporting is unavailable, ask a maintainer how to establish a private channel,
sharing only the request for contact. Wait for that channel before sending
sensitive details. Availability of hosted reporting features is not guaranteed
by this document.

## Working with benchmark inputs

The benchmark processes files and can invoke an installed target. Use reviewed
inputs and isolated execution environments. Follow the
[public repository policy](docs/public_repository_policy.md) when preparing
artifacts for publication.

Maintainers should enable secret scanning, push protection and private reporting
where supported. Hosting controls require administrator configuration; automated
repository checks are defense in depth, not a disclosure guarantee.
