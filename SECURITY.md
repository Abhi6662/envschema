# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.0   | ✅        |

## Reporting a Vulnerability

Please report security vulnerabilities to Abhishek Mandloi via GitHub Issues.
Do not create public issues for security concerns. Include details of the
affected version, steps to reproduce, and potential impact.

## Scope

This library validates environment variables and does not handle network
operations. Secrets are masked in `repr()` output but remain in memory as
plain strings — treat `.env` files as sensitive and exclude them from version
control.
