---
name: orchestrate
description: "Lean orchestrator workflow for Codex: the main session plans, luna_scout finds, sol_worker builds, astra_reviewer judges until no blocking findings remain. Use when the user says 'orchestrate', 'orkestrera', 'spawn subagents', 'use subagents' or 'delegate this'."
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

A brief can be carried out by someone who never saw this conversation. `sol_worker` gets all eight fields. `luna_scout` needs only Goal, Why, Files and Proof. `astra_reviewer` gets Goal, Why, the changed files and Proof.

```
Goal:     what is true when it is done, in one sentence
Why:      what the user is trying to achieve
Decided:  choices that are not to be reopened, each with its reason
Freedom:  what the agent decides itself, and when it stops to report
Files:    may change / may only read
Traps:    what can go wrong here, plus the project rules that apply
Proof:    command, and for a behaviour change the case that fails before and passes after
Risk:     low | high
```

Keep the field names in English and write the content in the user's language. High risk means money, saved data or schema, migration, auth, security, secrets, or publishing any of these.

Two writers never touch the same file: run them one after another. Use a git worktree only when the repository has commits, the worktree starts from the current HEAD and the part does not need uncommitted changes. Otherwise it starts from stale code.

## 3. Run

1. Spawn independent agents in the same turn so they run in parallel.
2. While they run, do your own non-overlapping part. Never predict or invent an agent's result.
3. When a report arrives, verify it: read the diff, run the check yourself. A report is a claim, not proof.

## 4. Close

1. Send high-risk changes to `astra_reviewer` before commit. Fix every A and B finding and send the new diff back to the same reviewer. Done means zero A and B on the final diff: a fix made after the last review is not done. After two failed rounds, stop before commit and ask the user.
2. Run the project's full check once.
3. Commit, deploy and back up yourself, following the project's rules. The user's instruction in this session wins over those rules.
4. Tell the user: what changed, what each agent did in one line, what is not verified.
