# Security notes

## Download integrity

The current installer tries multiple GitHub proxy URLs. Its download helper checks that a downloaded file exceeds a minimal size, but does not verify a pinned SHA-256 checksum or validate every downloaded executable's Authenticode signature. Treat successful download as a transport result, not proof of integrity.

For a high-assurance installation, download the exact release assets directly from their upstream projects, verify any publisher-provided signature or checksum, and only then unpack/use them. Do not create a checksum from an unverified mirror download and treat that as a trusted baseline.

## Filesystem changes

The script creates and removes files under the selected installation directory and a temporary cache directory. Review the current script before running it, especially if those folders already contain files you need.

## Secret handling

Never place API keys in this repository or public issues. If a key is exposed, revoke it at the provider and replace it. Scrub keys and credentials from logs before sharing diagnostics.

## Reporting

Please report suspected malicious behavior or supply-chain issues through a private reporting channel available from the repository owner rather than posting credentials or exploit details publicly.
