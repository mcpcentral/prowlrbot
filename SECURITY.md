# Security Policy

If you believe you've found a security issue in ProwlrBot, please report it privately.

## Reporting

Report vulnerabilities via [GitHub Issues](https://github.com/mcpcentral/prowlrbot/issues) with the `security` label, or email the maintainers directly.

### Required in Reports

1. **Title**
2. **Severity assessment**
3. **Impact**
4. **Affected component** (e.g. channel adapter, skill, config loading)
5. **Technical reproduction steps**
6. **Demonstrated impact** (how it crosses a trust boundary, not just theoretical)
7. **Environment** (Python version, OS, how ProwlrBot is run)
8. **Remediation advice** (if you have suggestions)

Reports without reproduction steps, demonstrated impact, and remediation advice will be deprioritized.

### Report Acceptance Gate

For fastest triage, include all of the following:

- Exact vulnerable path (file, function, and line range) on a current revision.
- Tested version details (ProwlrBot version and/or commit SHA).
- Reproducible PoC against latest `main` or latest released version.
- Demonstrated impact tied to ProwlrBot's documented trust boundaries (see below).
- For exposed-secret reports: proof the credential is ProwlrBot-owned or grants access to ProwlrBot-operated infrastructure/services.
- Scope check explaining why the report is **not** covered by the Out of Scope section below.

Reports that miss these requirements may be closed as `invalid` or `no-action`.

### Common False-Positive Patterns

- Prompt-injection-only chains without a boundary bypass (prompt injection is out of scope).
- Operator-intended local features (e.g. skills or commands the operator explicitly enabled) presented as remote injection.
- Authorized user-triggered actions presented as privilege escalation (e.g. an allowed sender triggering a skill that writes to an allowed path). In this trust model, authorized user actions are trusted unless you demonstrate an auth/sandbox/boundary bypass.
- Reports that only show a malicious skill executing privileged actions after a trusted operator installs/enables it.
- Reports that assume per-user multi-tenant authorization on a shared ProwlrBot instance/config.
- ReDoS/DoS claims that require trusted operator configuration input without a trust-boundary bypass.
- Scanner-only claims against stale or nonexistent paths, or claims without a working repro.

### Duplicate Report Handling

- Search existing advisories and issues before filing.
- Include likely duplicate advisory IDs in your report when applicable.
- Maintainers may close lower-quality or later duplicates in favor of the earliest high-quality canonical report.

## Security & Trust

Security handling is owned by the ProwlrBot maintainers. For sensitive reports, use a private channel as above.

## Bug Bounties

ProwlrBot is a community open-source project. There is no formal bug bounty program, but we credit every reporter in our changelog. Please disclose responsibly so we can fix issues quickly.

## Operator Trust Model

ProwlrBot does **not** model one instance as a multi-tenant, adversarial user boundary.

- Authenticated callers to the same ProwlrBot instance (same config, same channel workspace) are treated as **trusted operators** for that instance.
- Session identifiers and labels are routing/context controls, not per-user authorization boundaries.
- If one operator can see or trigger what another operator can on the same instance, that is expected in this trust model.
- **Recommended mode**: one user per machine/host (or per OS user), one ProwlrBot config for that user, and one or more agents/skills inside that instance.
- If multiple users need ProwlrBot, use one host/OS user (or VPS) per user, or strict isolation; sharing one instance by mutually untrusted users is not the recommended default.
- Skills run with the same privileges as the ProwlrBot process; only install and enable skills you trust.

## Trusted Skills Concept

Skills/extensions are part of ProwlrBot's **trusted computing base** for an instance.

- Installing or enabling a skill grants it the same trust level as local code running for that instance.
- Skill behavior such as reading env/files or running host commands is expected inside this trust boundary.
- Security reports must show a **boundary bypass** (e.g. unauthenticated skill load, allowlist/policy bypass, or path-safety bypass), not only malicious behavior from a trusted-installed skill.

## Out of Scope

- Public internet exposure of ProwlrBot when the docs recommend against it.
- Using ProwlrBot in ways that the docs recommend not to.
- Deployments where mutually untrusted/adversarial operators share one ProwlrBot instance and config.
- **Prompt-injection-only** attacks (without a policy/auth/sandbox boundary bypass).
- Reports that require write access to trusted local state (working directory, config, memory files) to achieve impact.
- Reports where the only demonstrated impact is an already-authorized user intentionally invoking a skill or command that writes to an allowed path, without bypassing auth, sandbox, or another documented boundary.
- Reports where the only claim is that a trusted-installed/enabled skill can execute with process/host privileges (documented trust model behavior).
- Any report whose only claim is that an operator-enabled "dangerous" or break-glass option weakens defaults (these are explicit tradeoffs by design).
- Reports that depend on trusted operator-supplied configuration to trigger availability impact. These may still be fixed as defense-in-depth but are not security-boundary bypasses.
- Exposed secrets that are third-party or user-controlled credentials (not ProwlrBot-owned) without demonstrated ProwlrBot impact.
- Scanner-only claims against stale or nonexistent paths, or without a working repro.

## Deployment Assumptions

ProwlrBot security guidance assumes:

- The host where ProwlrBot runs is within a trusted OS/admin boundary.
- Anyone who can modify the ProwlrBot working directory and config (including `config.json`) is effectively a trusted operator.
- A single instance shared by mutually untrusted people is **not** a recommended setup. Use separate configs and, at minimum, separate OS users or hosts per trust boundary.
- Authenticated callers to the same instance are treated as trusted operators; session or context identifiers are routing controls, not per-user authorization boundaries.

## One-User Trust Model

ProwlrBot's security model is **"personal assistant"** (one trusted operator, potentially many agents/skills), not "shared multi-tenant bus."

- If multiple people can message the same tool-enabled ProwlrBot instance, they can all steer that agent within its granted permissions.
- Session or memory scoping reduces context bleed but does **not** create per-user host authorization boundaries.
- For mixed-trust or adversarial users, isolate by OS user/host and use separate config and credentials per boundary.

## Agent and Model Assumptions

- The model/agent is **not** a trusted principal. Assume prompt/content injection can manipulate behavior.
- Security boundaries come from host/config trust, channel/user allowlists, tool policy, and what skills are enabled.
- Prompt injection by itself is not a vulnerability report unless it crosses one of those boundaries.

## Working Directory and Config Trust Boundary

The ProwlrBot working directory (`~/.prowlrbot/`) is treated as **trusted local operator state**.

- If someone can edit working directory files or config, they have already crossed the trusted operator boundary.
- Memory or context over those files is expected behavior, not a separate security boundary.
- Keep secrets out of the working directory and skill-accessible paths; secrets belong in `~/.prowlrbot.secret/`.

## Skills Trust Boundary

Skills are loaded and run **in-process** (or under the same trust boundary) as the ProwlrBot runtime and are treated as trusted code.

- Skills can execute with the same OS privileges as the ProwlrBot process.
- Runtime helpers used by skills are convenience APIs, not a sandbox boundary.
- Only install skills you trust, and restrict which skills are enabled in config where possible.

## Operational Guidance

- **Channels and users**: Restrict which channels and users can trigger the agent; use allowlists where possible.
- **Multi-user or shared inbox**: Use separate config/credentials and ideally separate OS users or hosts per trust boundary.
- **Skills**: Run with least privilege; sandbox where you can; limit tool scope to what you need.
- **Secrets**: Keep them out of the agent's working directory and skill-accessible paths. Use `~/.prowlrbot.secret/`.
- **Model**: Use a capable model when the agent has tools or handles untrusted input.
- **Review**: Review your config and skills regularly.

For more operational and hardening guidance, see the [documentation](docs/README.md) and the [security blog post](docs/blog/2026-03-10-security-first.md).

## Runtime Requirements

- **Python**: ProwlrBot requires Python 3.10+ (see [README](README.md)). Use a version with current security updates.
- **Docker or restricted environments**: When running in containers, run as a non-root user when possible. Use read-only mounts where feasible and limit capabilities to what is needed.
