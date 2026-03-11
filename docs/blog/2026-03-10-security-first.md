---
title: "Security First, Always"
date: 2026-03-10
author: ProwlrBot Team
tags: [deep-dive, alert]
summary: "We found 26 security vulnerabilities in the original codebase and fixed them all. Here's how we think about security."
---

# Security First, Always

## We Inherited Problems

When we forked the original codebase, we ran a full security audit. What we found wasn't great:

- API keys stored in plaintext config files
- No authentication on the web console
- Shell command execution with no sandboxing
- File operations without path traversal protection
- Hardcoded secrets in source code
- No rate limiting on any endpoint

26 vulnerabilities total. We fixed every single one.

## What We Changed

### Secrets Never Touch Disk Unencrypted

```
Before:  ~/.prowlrbot/config.json  → API keys in plaintext
After:   ~/.prowlrbot.secret/envs.json  → mode 0o600, separate directory
```

Secrets live in `~/.prowlrbot.secret/` with restricted file permissions. The main config file never contains API keys. Environment variables are the primary input method.

### Shell Commands Are Sandboxed

The shell tool blocks dangerous commands by default:

- `rm -rf /` — blocked
- `curl ... | bash` — blocked
- `chmod 777` — blocked
- `dd if=/dev/zero` — blocked

We maintain a blocklist of patterns that could cause damage. The blocklist is extensible — add your own patterns in the config.

### File Operations Stay In Bounds

Every file read/write operation checks:
1. Is the path within the working directory?
2. Does it traverse outside with `../`?
3. Is it a sensitive system file?

Path traversal attacks get caught before any I/O happens.

### The War Room Uses Advisory Locking

ProwlrHub's file locking is advisory — it warns agents, it doesn't prevent filesystem access. This is deliberate:

- **Hard locks** can deadlock if an agent crashes
- **Advisory locks** let agents make informed decisions
- **Hooks** catch violations before they happen

If an agent ignores the warning and edits a locked file anyway, the audit log records it. You'll know who did it and when.

### Cross-Machine Communication Is Authenticated

The HTTP bridge for cross-machine war room access:
- Validates all requests
- Logs every operation
- Supports IP filtering
- Can run behind Tailscale VPN for encrypted transport

### Marketplace Skills Are Reviewed

Community-submitted skills go through review before they're listed:

1. Code review for malicious patterns
2. Permission scope validation
3. Dependency audit
4. Sandbox testing

No skill can access your filesystem, network, or secrets without explicit permission declarations in its manifest.

## Our Security Principles

1. **No hardcoded secrets** — ever, anywhere, for any reason
2. **Least privilege** — agents get only the permissions they need
3. **Defense in depth** — multiple layers, not one big wall
4. **Fail closed** — if something's wrong, deny access
5. **Audit everything** — if it happened, there's a log
6. **Encrypt in transit** — Tailscale VPN for cross-machine, HTTPS for web

## Reporting Vulnerabilities

Found something? We want to know.

- **Email**: Open a [GitHub issue](https://github.com/prowlrbot/prowlrbot/issues) with the `security` label
- **Severity**: Use CVSS scoring if you can
- **Disclosure**: We'll acknowledge within 48 hours and patch within 7 days for critical issues

We don't have a bug bounty yet, but we credit every reporter in our changelog.

## What's Next

We're working on:
- **JWT authentication** for the web console
- **Role-based access control** for multi-user deployments
- **Encrypted SQLite** for the war room database
- **Certificate pinning** for bridge connections

Security isn't a feature. It's a foundation.

---

*Full security audit: [docs/plans/2026-03-09-prowlrbot-leapfrog-design.md](../plans/2026-03-09-prowlrbot-leapfrog-design.md) (Security section)*
