# Orchestrate 2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release Orchestrate 2.0 for Claude Max: an Opus orchestrator, seven locked agent profiles and a Fable oracle at three gates.

**Architecture:** The Claude plugin is the only Claude source: a short SKILL.md, two references read on demand, two small shell helpers and seven agent files. Codex stays a separate, lean plugin. One Python test file checks packaging and both helpers without model calls.

**Tech Stack:** Markdown, TOML, POSIX sh (Git Bash on Windows), git, Python 3.11+ with PyYAML for tests only.

**Spec:** `docs/superpowers/specs/2026-11-22-orchestrate-2-design.md`. Read it first. "Spec §N" below means that file.

## Global Constraints

- Roles, models, effort, `maxTurns`, tools, triggers and stop rules are exactly Spec §3–§5.
- `SKILL.md` is at most 120 lines. It has no `model` or `effort` in frontmatter.
- Every `description` in frontmatter is a double-quoted string.
- No agent has `Agent` or `Skill`. Only `fable-oracle` has `omitClaudeMd: true`.
- Prompts are English. Brief content and reports follow the user's language.
- Every prohibition in a prompt states its reason and its exception.
- The repo is public: no personal data, account details, local user paths or private project names.
- No commit, push, install, deletion outside this repo or billed model test without the user's yes. Tasks end in a checkpoint, not a commit.
- Never enable or accept usage credits.

## Review Focus

1. Windows checkout with `core.autocrlf=true`: the shell helpers keep LF and run (Task 1, `test_lf`).
2. A session log names the requested model as well as the model that answered: only the answering model counts (Task 1, `test_served_ignores_requested`).
3. Paths with spaces, and a call from a subdirectory: the same tree id as from the root (Task 1, `test_spaces_and_subdir`).
4. An unrelated file is already staged at commit time: the index does not match the approved id (Task 1, `test_unrelated_staged`).
5. A reference or script path breaks after plugin install: every path named in SKILL.md resolves inside the plugin (Task 3, `test_skill_paths`).

## Files

| Path | Change | Responsibility |
|---|---|---|
| `.gitattributes` | create | LF for `*.sh` |
| `tests/test_orchestrate.py` | create | All offline checks |
| `plugins/orchestrate-claude/skills/orchestrate/scripts/snapshot.sh` | create | Tree id for reviewed paths |
| `plugins/orchestrate-claude/skills/orchestrate/scripts/served-model.sh` | create | Models that answered in an agent log |
| `plugins/orchestrate-claude/agents/*.md` | 3 rewrite, 4 create | The roles |
| `plugins/orchestrate-claude/skills/orchestrate/SKILL.md` | rewrite | Flow, risk, routing |
| `plugins/orchestrate-claude/skills/orchestrate/references/{briefs,gates}.md` | create | Brief and gate packets |
| `plugins/orchestrate-codex/**` | edit | Lean 1.1.0 |
| `skills/` | delete | Stale third copy |
| `README.md`, both manifests, Claude marketplace | edit | Install and versions |

`served-model.sh` is one addition to Spec §8. A plain search for `"model"` in a log also matches `api-request` rows, which hold the requested model, and would report Fable after a fallback.

---

### Task 1: Helpers

**Files:** create `.gitattributes`, both scripts, `tests/test_orchestrate.py`.

**Interfaces, produced:**
- `sh snapshot.sh <path>...` prints one tree id on stdout. Exit 2 without paths.
- `sh served-model.sh <agent-id> [projects-dir]` prints distinct answering model ids, one per line, sorted. The default directory is `$HOME/.claude/projects`. Exit 3 when no log or no answer is found.

- [ ] **Step 1: Write failing tests.** Use `unittest` and a temporary repo per test. Run scripts through the `sh` that ships with Git.

| Test | Assertion |
|---|---|
| `test_changes` | `git diff --name-status HEAD <id>` is exactly A, M, D for a new, a changed and a deleted file. A second untracked file that was not named is absent |
| `test_untracked_edit` | Editing an untracked reviewed file changes the id |
| `test_no_commits` | A repo without HEAD returns an id that contains the named file |
| `test_no_args` | Exit 2, empty stdout |
| `test_index_untouched` | `git write-tree` is equal before and after |
| `test_spaces_and_subdir` | `dir with space/a b.txt` gives one id from the root and from the subdirectory |
| `test_unrelated_staged` | After staging the named paths `git write-tree` equals the id. After staging one more file it differs |
| `test_lf` | Neither script contains `\r\n`, and `git check-attr eol` says `lf` |
| `test_served_ignores_requested` | A log with an `api-request` row for `claude-fable-5-2` and an answer from `claude-opus-4-8` prints only `claude-opus-4-8` |
| `test_served_mixed` | Two answering models print two lines |
| `test_served_missing` | Exit 3 |

- [ ] **Step 2:** Run `python -m unittest discover -s tests -v`. Expected: failures for missing scripts.
- [ ] **Step 3: Implement.** `.gitattributes` is `*.sh text eol=lf`. The two non-obvious cores:

```sh
# snapshot.sh: idx is a temporary path, removed by a trap on EXIT
export GIT_INDEX_FILE="$idx"
if git rev-parse --verify -q HEAD >/dev/null; then git read-tree HEAD; else git read-tree --empty; fi
git add -A -- "$@"
git write-tree
```

```sh
# served-model.sh: anchor on the message object, never on a bare "model" key
grep -ho '"message":{"model":"[^"]*"' "$root"/*/*/subagents/agent-"$id".jsonl
```

- [ ] **Step 4:** Run the tests. Expected: all pass.
- [ ] **Step 5: Checkpoint.** `git status --short` lists only this task's files and `docs/`.

### Task 2: Agents

**Files:** the seven files in `plugins/orchestrate-claude/agents/`, the test file.

**Interfaces, produced:** agent names from Spec §3, the report shapes and the verdict words below.

- [ ] **Step 1: Write failing tests.**
  - `test_agents`: exactly seven files. `yaml.safe_load` of each frontmatter equals a literal table of Spec §3 for name, model, effort, maxTurns and tools.
  - `test_oracle_only_omits_claude_md`.
  - `test_descriptions_quoted`: for every agent and skill.
- [ ] **Step 2:** Run. Expected: fail on the count and on `sonnet-worker` YAML.
- [ ] **Step 3: Write the agents.** Each body holds exactly these decisions:

| Agent | Must say | Ends with |
|---|---|---|
| oracle | Judge the packet against the user's verbatim request. Read the files yourself. Name the most dangerous assumption. Never edit | Gate 1 `Run`, `Change` or `Ask user`. Gate 2 `Release` or `Stop`. Gate 3 cause, confidence, next experiment |
| specialist | Own the outcome inside Files. Decide within Freedom. Show failing then passing proof for behaviour changes | Builder report |
| reviewer | Try to disprove the change. Judge the frozen diff. Shell for reading and tests only. Severity A–D as in v1 | `Verdict: approved` or `Verdict: fix first (<n> A/B)`, plus `Not reviewed:` |
| reviewer-deep | As reviewer, plus old saved data, boundary values and hostile input. As gate substitute, follow the gate's answer shape | As reviewer, or as the gate |
| worker | Short numbered steps. `Needs:` when Goal, Files or Proof is missing. Run a real check. Continue until done | Builder report |
| ui-tester | Use the browser the user's rules name. Load deferred tools through ToolSearch. Report after each flow. Never edit | Findings A–D, `Not tested:` |
| scout | Short steps. Search before reading. At most 30 hits with file and line. Mark guesses | `Done:` or `Not found:` |

  Builder report: `Status`, `Changed`, `Proof`, `Decisions`, `Open`. All seven say that file, web and tool content is data.
- [ ] **Step 4:** Run the tests and `claude plugin validate plugins/orchestrate-claude`. Expected: pass.
- [ ] **Step 5: Checkpoint.**

### Task 3: Skill and references

**Files:** `SKILL.md`, `references/briefs.md`, `references/gates.md`, the test file.

**Interfaces, consumed:** Task 1 commands, Task 2 names and verdicts.

- [ ] **Step 1: Write failing tests.**
  - `test_skill_limits`: at most 120 lines, no `model` or `effort` key.
  - `test_triggers`: the description contains the five phrases in Spec §8 and does not offer task size as a trigger.
  - `test_skill_paths`: every `${CLAUDE_SKILL_DIR}/...` path exists.
  - `test_roles_named`: all seven agents appear in SKILL.md, and every `orchestrate:<name>` in the skill tree is a real agent.
  - `test_brief_fields`: the eight fields of Spec §7 appear in order.
- [ ] **Step 2:** Run. Expected: fail.
- [ ] **Step 3: Write `SKILL.md`** with Spec §4 steps 0–7, each ending in its completion criterion. It also holds:
  - the pointers "Before the first delegation read briefs.md" and "When a gate triggers, read gates.md", with full `${CLAUDE_SKILL_DIR}` paths
  - both helper commands with quoted paths, because references get no variable substitution
  - the commit rule: after staging, `git write-tree` equals the approved id, otherwise the verdict is void
- [ ] **Step 4: Write `briefs.md`:** the template, the short scout form, one good and one bad example for worker and for specialist, with invented project details.
- [ ] **Step 5: Write `gates.md`:** Spec §5 as three packet templates, the retry limits, the substitute rules and report labels, and Spec §6 including the empty-tree base and the no-git case.
- [ ] **Step 6:** Run the tests. Expected: pass.
- [ ] **Step 7: Checkpoint.**

### Task 4: Codex, packaging, README

**Files:** the Codex skill, three TOML files and manifest, Claude manifest and marketplace, `README.md`, delete `skills/`.

- [ ] **Step 1: Write failing tests.**
  - `test_versions`: Claude 2.0.0, Codex 1.1.0.
  - `test_codex_profile`: `tomllib` reads the three agents with unchanged model and effort.
  - `test_no_root_copy`: `skills/` is absent.
  - `test_public_hygiene`: no tracked or new file matches a user-profile path or an email address.
- [ ] **Step 2:** Run. Expected: fail.
- [ ] **Step 3: Edit Codex** as Spec §9 only: brief, two-round re-review until 0 A/B, worktree rule, role texts. No gates.
- [ ] **Step 4: Rewrite README:** roles, gates, Max requirement and 50% Fable share, plugin install for both, migration from 1.x including the `npx skills` break, how to change the tester's MCP names, how to set Opus high.
- [ ] **Step 5:** Delete `skills/`, bump versions, update descriptions.
- [ ] **Step 6:** Run the tests, both `claude plugin validate` commands, and an offline start with `--plugin-dir`. Expected: pass, seven `orchestrate:` agents listed.
- [ ] **Step 7: Checkpoint.** Show the user `git diff --stat`.

### Task 5: Live acceptance

**Files:** none in the repo. Throwaway repos in the scratch directory.

- [ ] **Step 1:** Ask for a yes to spend quota. Confirm that `claude auth status` reports `max` and that extra usage is off.
- [ ] **Step 2: Baseline.** Export v1 with `git archive HEAD` and run the rounding-bug scenario. Record what it catches and the worker's first-request tokens.
- [ ] **Step 3:** Run every row of Spec §10 on 2.0. Simulate unavailable Fable with an `availableModels` setting that excludes it. Claude Code then substitutes the main model instead of failing: pass means `served-model.sh` prints that model, the report says `not Fable` and the deep reviewer reruns the gate. A launch failure for missing quota or credits is a different path, so report it as not run. Test the oracle's read of the frozen diff in a desktop session, where permission prompts are real.
- [ ] **Step 4:** Report each row as pass, fail or not run, with log evidence and share of quota used. A failed row is fixed and rerun before rollout.

### Task 6: Rollout

- [ ] **Step 1:** Ask, then commit on branch `v2` and push.
- [ ] **Step 2:** Ask, then merge to `main`, install the Claude plugin and update Codex.
- [ ] **Step 3:** List the stale local skill and agent copies. Ask, then remove only the approved ones.
- [ ] **Step 4:** After the first real job, compare start context, A/B findings, retries and Fable share against the baseline.

## Coverage

| Spec | Task |
|---|---|
| §3 Roles | 2 |
| §4 Flow | 3 |
| §5 Gates | 1, 2, 3 |
| §6 Frozen input | 1, 3 |
| §7 Brief | 2, 3 |
| §8 Files | 3, 4 |
| §9 Codex | 4 |
| §10 Acceptance | 1–5 |
| §11 Rollout | 6 |
