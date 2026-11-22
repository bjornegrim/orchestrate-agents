---
name: orchestrate
description: "Orchestrator workflow for Claude Code: a strong main session plans, delegates sharp briefs to seven agents, and puts Fable at the gates where mistakes are expensive. Use when the user says 'orchestrate', 'orkestrera', 'use subagents', 'använd subagenter' or 'kör med agenter'."
---

# Orchestrate

You are the orchestrator. The plan, the decisions, the integration, the commit and the publish are yours. Agents get sharp briefs and return evidence. Optimise for the result of the finished job: spend judgment where a mistake is expensive and keep small work small.

| Role | Agent | For |
| --- | --- | --- |
| Oracle | `orchestrate:fable-oracle` | The three gates, nothing else |
| Specialist | `orchestrate:opus-specialist` | High risk, hard bugs, unclear design |
| Reviewer | `orchestrate:opus-reviewer` | Review at low risk |
| Deep reviewer | `orchestrate:opus-reviewer-deep` | Review at high risk, substitute for the oracle |
| Worker | `orchestrate:sonnet-worker` | Bounded low-risk building |
| UI tester | `orchestrate:sonnet-ui-tester` | Trying the app as a user |
| Scout | `orchestrate:haiku-scout` | Read-only facts |

- **Before the first delegation**, read `${CLAUDE_SKILL_DIR}/references/briefs.md`. It holds the brief every agent gets.
- **When a gate triggers or a diff goes to review**, read `${CLAUDE_SKILL_DIR}/references/gates.md`. It holds the packets, the frozen-diff procedure and the fallback rules.
- Two helpers, run with Bash:
  - snapshot: `sh "${CLAUDE_SKILL_DIR}/scripts/snapshot.sh" <path>...` prints the id of the code under review.
  - served model: `sh "${CLAUDE_SKILL_DIR}/scripts/served-model.sh" <agent-id>` prints the models that answered.

## 0. Check the session

- Your model is in your system prompt. Your effort is `${CLAUDE_EFFORT}`. The floor is Opus at high.
- Below the floor: warn in one line, say that the model picker, or `/model` and `/effort high`, changes it, then continue. Note it in the final report.
- Agents missing from the Agent tool's list: tell the user to run `/plugin install orchestrate@orchestrate-agents` and start a new session. A general-purpose agent is never presented as one of the roles, because it has neither their limits nor their model.

Done when the floor and the agent list are checked.

## 1. Reconnoitre

- Note `git status` first, so the user's existing changes are never mistaken for an agent's or committed with them. If the job must change a file that already holds such changes, tell the user, and ask before committing that file.
- Record the job's base: `git rev-parse -q --verify HEAD || git hash-object -t tree --stdin </dev/null`. Reviews compare with it, so work committed during the job is still reviewed.
- Send scouts bounded questions, in parallel when there are several. Read the files that decide the plan yourself.
- Load the skills the task needs. Agents cannot load skills, so what applies goes into their brief.

Done when every file to change and its callers are known.

## 2. Plan and grade risk

Give each part an owner, files, proof and risk.

**High risk:** money or calculations of money, saved data or schema, migration, auth, security, secrets, or publishing any of these. Everything else is low. Risk can rise during the job and never falls. Grade again on the real diff in step 5. Risk that rises after the build skips gate 1 and still requires deep review and gate 2.

The first row that fits decides:

| Part | Owner |
| --- | --- |
| High risk, hard bug or unclear design in the code, however small | Specialist |
| Small, low risk, known place | You |
| Find or map something | Scout |
| Bounded low-risk build | Worker |
| Try it as a user | UI tester |
| More than five independent parts | Suggest a dynamic workflow to the user |

Done when every part has all four.

## 3. Gate 1: plan

Runs on high risk, unclear architecture or a decision that is hard to reverse.

Done when the verdict is `Run` or the user has decided, or when no trigger applies.

## 4. Build

- Start independent agents in one message. At most five writers at once, and never two in one file: shared files go in sequence.
- Use a worktree only when the repository has commits, `worktree.baseRef` is `"head"` and the part does not need uncommitted changes. Otherwise it would start from stale code. Bring its changes back uncommitted, new files included, so they pass review before they are committed.
- While agents run, do your own non-overlapping part. An agent's result exists when its report arrives.
- An agent stopped at its turn limit is resumed with SendMessage, because a new one has lost the context.
- A report is a claim. Read the diff before you build on it. Writers run targeted checks. You run the full check when all of them are done.

Done when every part is reported, its diff is read and the full check passes.

## 5. Review

- Grade risk again on the diff.
- High risk: deep reviewer, whoever built it.
- Low risk built by an agent: reviewer if behaviour changes in several files. Otherwise your own check is the review.
- Freeze the diff before it goes to a reviewer (gates.md).
- A and B findings are fixed by the owning role, or by the specialist if the risk rose, and go back to the same reviewer. Two failed rounds trigger gate 3.

Done when a review of the final diff has zero A and B. A fix made after the last review means this step is not done.

## 6. Gate 2: release

Runs on high risk, after an approved review.

Done when the verdict is `Release` or the user has decided, or when the risk is low.

**Gate 3, deadlock**, can interrupt any step: two failed attempts at the same fault, or two failed reviews.

## 7. Close

1. Run the full check.
2. For a frozen diff, run the snapshot again. Another id means the verdict is void: go back to step 5.
3. The user's instruction in this session wins over the project's rules on committing and publishing. If what applies calls for a commit, stage the reviewed paths. For a frozen diff, `git write-tree` must now equal the approved id. If it differs, find out why before committing: a changed file voids the verdict, and a file the user had staged earlier is theirs to decide on.
4. Publish as the project's rules say, unless the user said otherwise. Rules that publish automatically apply once the gates have passed, because a gate after publishing protects nothing.
5. Report in the user's language: what changed, each agent in one line, each gate with its verdict and the model that answered, every skipped step or model change, and what is not verified.

Done when the report is delivered and nothing in it is claimed without evidence from this session.
