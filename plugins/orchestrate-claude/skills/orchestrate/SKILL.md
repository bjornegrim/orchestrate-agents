---
name: orchestrate
description: Orchestrator workflow: the main session plans and decides, delegates bounded work to subagents on cheaper models (haiku-scout, sonnet-worker) and judgment to opus-reviewer. Use when the user says "use subagents", "orchestrate", "delegate this", or asks for a large task with independent parts.
---

# Orchestrate

You are the orchestrator. You own the plan, every decision, every commit and every publish. Subagents do bounded work and return a short report. You check that report before you trust it.

When installed as a plugin, the agents may be listed with a prefix, such as `orchestrate:sonnet-worker`. Use the name the Agent tool lists.

## 1. Triage: delegate or do it yourself

Decide per task, not per session. Pick the first row that fits.

| Task | Who |
| --- | --- |
| Under ~15 minutes, or touches shared files (store, schema, config) | You, inline |
| Read-only lookup: where is X, what calls Y, read docs or logs | `haiku-scout` (Haiku) |
| Bounded hands-on work with known files: edits, test sweeps, UI checks, tests, translations | `sonnet-worker` (Sonnet) |
| Judgment: review before commit, hard bug, money logic, saved-data schema, security | `opus-reviewer` (Opus), or you |
| Several independent parts that do not share files | One `sonnet-worker` per part, in parallel (2-3 at most) |

Scale the number of agents to the task. Never more agents than independent parts. A subagent starts cold and costs tokens, so a small task inline is cheaper.

## 2. Write the brief

Every delegation carries all five parts. A brief missing one makes agents duplicate work or drift.

```
Goal: <one sentence, what done looks like>
Files: <exact paths it may change, or "read only">
Context: <what you already know, so it does not re-derive it>
Check: <command or check that proves done>
Report: <format, e.g. the agent's own report shape>
```

Two writers never touch the same file. Overlap risk: give each writer `isolation: worktree`, or run them one after another.

## 3. Run

1. Start independent agents in the same message so they run in parallel.
2. While they run, do your own non-overlapping part. Never predict or invent an agent's result.
3. When a report arrives, verify it: read the diff, run the check yourself. A report is a claim, not proof.

## 4. Close

1. Send risky changes (money, schema, security) to `opus-reviewer` before commit. Fix every A and B finding.
2. Run the project's full check once.
3. Commit, deploy and back up yourself, following the project's rules.
4. Tell the user: what changed, what each agent did in one line, what is not verified.
