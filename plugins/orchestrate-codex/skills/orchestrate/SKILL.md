---
name: orchestrate
description: Orchestrator workflow: the main session plans and decides, delegates bounded work to custom subagents on cheaper models (luna_scout, sol_worker) and judgment to astra_reviewer. Use when the user says "spawn subagents", "orchestrate", "delegate this", or asks for a large task with independent parts.
---

# Orchestrate

You are the orchestrator. You own the plan, every decision, every commit and every publish. Subagents do bounded work and return a short report. You check that report before you trust it.

Subagents run only when you ask for them by name. Spawn the custom agents below explicitly; the built-in `explorer` and `worker` do not carry these rules.

If `luna_scout`, `sol_worker` and `astra_reviewer` are not available, tell the user to copy the `.toml` files from this plugin's `agents/` folder to `~/.codex/agents/` and restart Codex. A plugin cannot install custom agents by itself.

## 1. Triage: delegate or do it yourself

Decide per task, not per session. Pick the first row that fits.

| Task | Who |
| --- | --- |
| Under ~15 minutes, or touches shared files (store, schema, config) | You, inline |
| Read-only lookup: where is X, what calls Y, read docs or logs | `luna_scout` (GPT-6 Luna) |
| Bounded hands-on work with known files: edits, test sweeps, UI checks, tests, translations | `sol_worker` (GPT-6.2 Sol) |
| Judgment: review before commit, hard bug, money logic, saved-data schema, security | `astra_reviewer` (GPT-6.2 Astra), or you |
| Several independent parts that do not share files | One `sol_worker` per part, in parallel (2-3 at most) |

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

Two writers never touch the same file. Overlap risk: give each writer its own git worktree, or run them one after another.

## 3. Run

1. Spawn independent agents in the same turn so they run in parallel.
2. While they run, do your own non-overlapping part. Never predict or invent an agent's result.
3. When a report arrives, verify it: read the diff, run the check yourself. A report is a claim, not proof.

## 4. Close

1. Send risky changes (money, schema, security) to `astra_reviewer` before commit. Fix every A and B finding.
2. Run the project's full check once.
3. Commit, deploy and back up yourself, following the project's rules.
4. Tell the user: what changed, what each agent did in one line, what is not verified.
