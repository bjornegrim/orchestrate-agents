# Orchestrate: one mind in charge, the right model for each job

A workflow for larger coding tasks. A strong main session plans, writes sharp briefs, integrates and commits. Agents on fitting models do the work. The strongest model judges at the few points where a wrong decision is expensive.

There are two editions:

- **Claude Code (2.0)** is built for Claude Max: seven agents and three Fable gates.
- **Codex (1.1)** is lean, for the smaller plans: three agents and no gates.

## Claude Code

### Requirements

- A plan that includes Fable, such as Max. Fable can take up to 50 % of the weekly limit and drains it faster than other models. On a plan where Fable bills to usage credits, the skill does not accept credits for you: if the oracle cannot run, a deep Opus reviewer takes the gate and the report says so. If you have already turned credits on, gate calls are billed to them.
- Claude Code 2.1.321 or later, for Fable 5.2.
- Git, and on Windows Git Bash, for the two helper scripts.
- A main session on **Opus at high effort or above**. Choose it in the model picker, or run `/model opus` and then `/effort high`. Below that the skill warns and continues.

If `claude auth status` still shows your old plan after an upgrade, run `claude auth login`. Restarting is not enough.

### Install

```sh
claude plugin marketplace add bjornegrim/orchestrate-agents
claude plugin install orchestrate@orchestrate-agents
```

Start a new session. Run `/orchestrate:orchestrate`, or say "orchestrate: ...".

### Roles

| Role | Agent | Model | Effort | Does |
| --- | --- | --- | --- | --- |
| Orchestrator | your main session | Opus or better | high or above | Plan, decisions, briefs, integration, commit |
| Oracle | `fable-oracle` | Fable | high | Judges at the gates. Cannot edit |
| Specialist | `opus-specialist` | Opus | high | High risk, hard bugs, unclear design |
| Reviewer | `opus-reviewer` | Opus | high | Tries to disprove a change |
| Deep reviewer | `opus-reviewer-deep` | Opus | xhigh | Reviews high risk, stands in for the oracle |
| Worker | `sonnet-worker` | Sonnet | medium | Bounded low-risk building |
| UI tester | `sonnet-ui-tester` | Sonnet | medium | Tries the app as a user |
| Scout | `haiku-scout` | Haiku | medium | Finds facts with file and line |

The reviewers and the UI tester are read-only by instruction, because they have a shell. The oracle is read-only by its tool list.

### Gates

High risk means money, saved data or schema, migration, auth, security, secrets, or publishing any of these.

| Gate | When | Verdict |
| --- | --- | --- |
| 1. Plan | High risk, unclear architecture, or a decision that is hard to reverse | Run, Change or Ask user |
| 2. Release | High risk, after an approved review and before commit | Release or Stop |
| 3. Deadlock | Two failed attempts at the same fault, or two failed reviews | Root cause and next experiment |

Small and ordinary jobs never reach Fable unless they deadlock or meet a gate 1 trigger.

A verdict is tied to a fingerprint of the reviewed files. A later edit voids it. After each gate the orchestrator reads the agent's log to see which model answered, because a safety fallback or a model restriction can change it.

These rules are instructions to the orchestrator, not hooks. Nothing technically blocks a commit that skips them.

### The brief

```
Goal:     what is true when it is done
Why:      what the user is trying to achieve
Decided:  choices that are not to be reopened
Freedom:  what the agent decides itself, and when it stops
Files:    may change / may only read
Traps:    what can go wrong, and the rules that apply
Proof:    command, and the case that fails before and passes after
Risk:     low | high
```

### Changing the set

- **Model or effort:** edit `model` or `effort` in the agent file.
- **Browser for the UI tester:** its `tools` line names the MCP servers `obscura` and `playwright` (as a plugin). With other browser tools, replace `mcp__obscura__*` and `mcp__plugin_playwright_playwright__*` with `mcp__<your server>__*`.
- **An installed plugin is overwritten on update.** Keep your changes in a fork.

## Codex

```sh
codex plugin marketplace add bjornegrim/orchestrate-agents
```

Or in the Codex app: Plugins, Add plugin marketplace, source `https://github.com/bjornegrim/orchestrate-agents`.

A Codex plugin cannot carry custom agents. Clone the repository and copy the three files, also after an update:

```powershell
Copy-Item plugins\orchestrate-codex\agents\*.toml $HOME\.codex\agents\ -Force
```

```sh
mkdir -p ~/.codex/agents && cp plugins/orchestrate-codex/agents/*.toml ~/.codex/agents/
```

Restart Codex and say "orchestrate: ...".

| Role | Agent | Model | Effort |
| --- | --- | --- | --- |
| Scout | `luna_scout` | GPT-6 Luna | low |
| Worker | `sol_worker` | GPT-6.2 Sol | medium |
| Reviewer | `astra_reviewer` | GPT-6.2 Astra | high |

High-risk changes are reviewed until no A or B finding remains, at most two rounds. After that Codex asks you.

A custom agent inherits the parent's sandbox, approvals and MCP servers. The reviewer is read-only by instruction, so use a read-only or workspace-write sandbox if you need a hard guarantee.

## Upgrading from 1.x

**Breaking: the skill copy in the repository root is gone.**

- If you installed with `npx skills add`: that path now finds the Claude skill only, without its agents, and no longer serves Codex. Remove that copy and install the plugin as above.
- If you copied agents or the skill to `~/.claude/` by hand: remove those copies, or you will have two sets with different rules.
- If you have the Claude plugin:

  ```sh
  claude plugin marketplace update orchestrate-agents
  claude plugin update orchestrate@orchestrate-agents
  ```

- If you run on the smallest Claude plan: 2.0 uses more quota than 1.x. Version 1 is at commit `efcdd9e`.

## Tests

The tests make no model calls. They need Python 3.12 or later, PyYAML and Git.

```sh
python -m unittest discover -s tests
```

## Sources

- Claude Code docs: subagents, model configuration, advisor, worktrees, skills.
- Claude Help Center: Max plan, Claude Fable models on your plan.
- OpenAI Codex docs: Subagents, Build skills, Models.
