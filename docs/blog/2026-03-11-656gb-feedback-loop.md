---
title: "How a Background Task Ate 656GB in 2 Minutes"
date: 2026-03-11
author: ProwlrBot Team
tags: [deep-dive, alert]
summary: "A single background command created a feedback loop that filled an entire 932GB disk. Here's what happened, why it's dangerous, and the safety rails we built because of it."
---

# How a Background Task Ate 656GB in 2 Minutes

*March 11, 2026 -- Dr34d*

---

We were debugging why some console pages wouldn't load. Routine stuff. The fix was straightforward -- a missing Vite proxy config and some overly aggressive rate limiting. But while investigating disk space on the machine, a single background command quietly consumed **656 gigabytes** in under two minutes and locked us out of everything.

This is the story of a feedback loop that nearly bricked a dev machine, and the three safety rails we added to ProwlrBot because of it.

## What Happened

During a debugging session, we ran this command in the background:

```bash
du -sh /* 2>/dev/null | sort -rh | head -15
```

Standard stuff. "Show me the biggest directories on disk." The kind of command you run without thinking.

Except this command was running as a **background task**, which means its output was being written to a file. That file lived in `/private/tmp/`. And `du -sh /*` recursively sizes **every directory on the filesystem** -- including `/private/tmp/`.

Here's the chain:

1. `du` starts scanning `/` and writing results to `/private/tmp/output.file`
2. `du` reaches `/private/tmp/` and starts measuring it
3. The output file is now part of what `du` is measuring
4. `du` writes more output about the growing file
5. The file grows because `du` is writing about it
6. `du` measures the larger file, writes more output
7. **Repeat until disk is full**

A textbook feedback loop. The file grew from 0 bytes to 656GB in roughly two minutes. The 932GB disk went from comfortable to 99% full (122MB remaining). At that point, everything stops. Git commands fail. File writes fail. Even deleting the file initially failed because the OS couldn't allocate space for the operation's metadata.

## Why This Is Dangerous

This isn't just a "whoops, restart and move on" situation. When a disk fills completely:

**Everything that writes to disk breaks simultaneously.** Databases can't commit transactions. Log files can't append. Temp files can't be created. Config saves fail silently. If ProwlrBot was running in production when this happened, every subsystem would fail at once -- not gracefully, not with error messages, just... stop.

**Data corruption is likely.** SQLite databases (our audit log, chat history, monitoring data) are particularly vulnerable. A write that gets partially committed because the disk filled mid-transaction can corrupt the database file permanently. WAL mode helps, but it's not bulletproof against zero-free-space conditions.

**Recovery is non-obvious.** When the disk is 100% full, you can't write new files, you can't create temp files, and many delete operations fail because they need to update filesystem metadata. We got lucky -- `rm` on macOS APFS worked. On ext4 or NTFS, you might need to boot from recovery media.

**The feedback loop is invisible.** There's no progress bar showing "your disk is filling up." The background task just runs silently. By the time you notice something is wrong (commands failing, apps crashing), the damage is done.

## The Uncomfortable Question

If this can happen on a developer's machine from a single `du` command, what happens when an **AI agent** has shell access?

ProwlrBot gives agents the ability to run shell commands. That's a core feature -- it's how agents interact with the system, run scripts, manage files. We already had safety rails: a command allowlist, a denylist for dangerous patterns (`rm -rf`, `sudo`, fork bombs), and a 60-second timeout.

But none of those would have caught this. `du` is on the allowlist. It's a read-only command. It doesn't match any dangerous pattern. And the 60-second timeout? A command like `yes` or `cat /dev/urandom | base64` can write **gigabytes per second** to stdout. In 60 seconds, that's potentially terabytes of data held in memory or written to disk.

The timeout prevents the command from running forever. It does **not** prevent the command from producing unbounded output during its allowed runtime.

## What We Fixed

We identified three categories of unbounded-write risk in ProwlrBot and added safety rails for each.

### 1. Shell Output Cap (1MB per stream)

**The problem:** `execute_shell_command()` calls `proc.communicate()`, which reads the entire stdout and stderr into memory. No size limit. An agent running `yes` for 60 seconds could produce gigabytes of output, potentially OOM-killing the server.

**The fix:**

```python
MAX_OUTPUT_BYTES = 1_000_000  # 1 MB cap per stream

stdout, stderr = await proc.communicate()
stdout_truncated = len(stdout) > MAX_OUTPUT_BYTES
stdout_str = stdout[:MAX_OUTPUT_BYTES].decode(encoding, errors="replace")
if stdout_truncated:
    stdout_str += f"\n\n[output truncated — {len(stdout):,} bytes total, showing first {MAX_OUTPUT_BYTES:,}]"
```

The agent still gets useful output -- 1MB is plenty for any diagnostic command. But a runaway producer can't OOM the process or fill the disk. The truncation notice tells the agent (and the user reviewing the session) that output was capped, so nobody is confused about missing data.

### 2. Audit Log Auto-Cleanup

**The problem:** The `AuditLog` class had a `cleanup()` method that deletes entries older than N days. Good design. Except **nothing ever called it.** The audit database would grow forever on a running system.

**The fix:**

```python
def __init__(self, db_path=None):
    # ... setup ...
    self._create_tables()
    # Auto-cleanup on startup to prevent unbounded growth
    try:
        self.cleanup(older_than_days=90)
    except Exception:
        pass
```

Every time the app starts, it trims entries older than 90 days. Zero configuration, zero maintenance burden. The `try/except` ensures a cleanup failure (maybe the DB is locked by another process) doesn't prevent the app from starting.

### 3. Error Dump Cleanup

**The problem:** When an agent query fails, `write_query_error_dump()` writes a JSON file to the system temp directory with the full error context (traceback, agent state, request data). Great for debugging. But the files are **never cleaned up.** A crash loop -- agent hits the same error repeatedly -- could create thousands of dump files.

**The fix:**

```python
def cleanup_old_error_dumps(max_age_hours=72, max_files=100):
    """Remove stale error dump files."""
    pattern = os.path.join(tempfile.gettempdir(), "prowlrbot_query_error_*.json")
    files = sorted(glob.glob(pattern), key=os.path.getmtime)
    cutoff = time.time() - (max_age_hours * 3600)

    for path in files:
        if os.path.getmtime(path) < cutoff or len(files) - deleted > max_files:
            os.unlink(path)
```

Called automatically on app startup. Files older than 72 hours get cleaned. If there are more than 100 dump files regardless of age, the oldest are removed. Two bounds -- time-based and count-based -- because either one alone has edge cases.

## The Broader Lesson

Every system that writes data needs to answer three questions:

1. **What's the maximum size this can grow to?** If the answer is "unlimited" or "I don't know," you have a bug. It might not manifest for months, but it's there.

2. **What happens when it hits that maximum?** Truncation? Rotation? Error? Silent data loss? Each has different implications. ProwlrBot's shell tool now truncates with a notice. The audit log deletes old data. The error dumps have both a time window and a count cap.

3. **Who or what triggers the cleanup?** If the answer is "someone has to remember to run it manually," it will never happen. Cleanup should be automatic -- on startup, on a schedule, or on a threshold.

This applies everywhere. Log files. Database tables. Cache directories. Upload folders. Message queues. Temp files. Anywhere data accumulates, ask: what bounds it?

## The Meta-Irony

An AI assistant running a diagnostic command to help fix ProwlrBot almost bricked the machine ProwlrBot runs on. And the fix was adding safety rails to ProwlrBot so its own AI agents can't do the same thing to someone else's machine.

We keep building the tools we wish we had when things went wrong. At this point, that's basically the project's design philosophy.

---

*The safety fixes are in commit `324b273`. If you're running ProwlrBot with agents that have shell access, update to get the output cap. If you're building any system that gives AI models write access to a filesystem, please think about output bounds. We learned this one the hard way so you don't have to.*
