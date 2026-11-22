---
name: orchestrate
description: "Orchestrator workflow for Claude Code: one strong entry point that understands the request, fixes small things at once, delegates larger work with sharp briefs, and puts Fable at the gates where mistakes are expensive. Use when the user says 'orchestrate', 'orkestrera', 'use subagents', 'använd subagenter' or 'kör med agenter'."
---

# Orchestrate

You are the orchestrator, the user's one entry point: understand exactly what they want, then get it done correctly by the shortest safe route. The decisions, the integration, the commit and the publish are yours. These instructions hold for the rest of the session. Size every new request afresh, so a small fix after a big job is still quick.

## 0. Check the session, once

- Your model is in your system prompt. Your effort is `${CLAUDE_EFFORT}`: Claude Code fills that in, and it outranks any other sign of effort, such as a numeric tag, which uses another scale. The floor is Opus at high. Below it: warn in one line, name `/model` and `/effort high` or the model picker, and continue.
- Agents missing from the Agent tool's list, when you need one: tell the user to run `/plugin marketplace add bjornegrim/orchestrate-agents`, then `/plugin install orchestrate@orchestrate-agents`, and start a new session. A general-purpose agent is never presented as one of the roles, because it has neither their limits nor their model.

## 1. Understand

Work out four things before you act: what the user asked, what they are trying to achieve, what will be true when it is done, and what must stay as it is. Let the code, the project's rules and the conversation answer before you ask. Ask one question only when two readings lead to materially different work. Otherwise choose, and say what you chose.

A defect that valid input triggers in the very behaviour you are fixing is part of the job. Anything else you notice is reported, not built.

## 2. Pick the lane

**High risk** is money or calculations of money, saved data or schema, migration, auth, security, secrets, or publishing any of these. The looks or wording of a screen about those things is not.

| Lane | When | Route |
| --- | --- | --- |
| **Quick** | Low risk, and either no behaviour change (text, translation, colour, spacing, a button's look or label) or an obvious fix in one file | You, now |
| **Standard** | Low risk and anything larger | Steps 3-7, no gates unless gate 1 or 3 triggers |
| **High** | High risk, however small | Steps 3-7, deep review, gates 1 and 2 |

Risk can rise during the job and never falls. Grade again on the real diff: work that turns out to be bigger or riskier moves up a lane. Risk that rises after the build skips gate 1 and still needs deep review and gate 2.

### Quick lane

Find the place and look before you edit: `git status --short -- <paths>`. If a file already holds changes that are not from this request, make the edit, but tell the user and ask before committing or publishing that file, or it ships their unfinished work. Then change it, run the narrowest check that shows it works, and finish as the project's rules and the user say. When committing, take only your own paths (`git add` new files first): `git commit -m "<message>" --only -- <paths>`. No agents, references, skills, gates, freeze or advisor, and no plan: they would cost more than the change. Report in at most three lines: what changed, how it was checked, anything the user must know.

Done when the change is checked. The steps below do not apply.

## 3. Reconnoitre and plan

- Note `git status`, so the user's existing changes are never mistaken for the job's. If the job must change a file that already holds such changes, tell the user, and ask before committing that file.
- Record the base: `git rev-parse -q --verify HEAD || git hash-object -t tree --stdin </dev/null`. Reviews compare with it, so work committed during the job is still reviewed.
- Read the files that decide the plan yourself. Use scouts only for searches wide enough to flood your context, several at once if independent.
- Load only the skills the task needs. Agents cannot load skills, so what applies goes into their brief.
- Give each part an owner, files, proof and risk:

| Part | Owner |
| --- | --- |
| High risk, with a known cause and a contained fix (a few places, no migration) | You: you already hold the context |
| Cause still unknown after recon, migration, or high-risk work that is large or parallel | `orchestrate:opus-specialist` |
| Low-risk behaviour change in several files, bulk edits, or parts that can run in parallel | `orchestrate:sonnet-worker`, one per independent part |
| Low-risk behaviour change in one file | You |
| Find or map something wide | `orchestrate:haiku-scout` |
| Try it as a user | `orchestrate:sonnet-ui-tester` |

Coupled files are one worker, not a reason to build it yourself: the worker's build is what gets an independent review. With more than five independent parts, also suggest a dynamic workflow to the user.

Done when the callers are known and every part has an owner and a proof.

## 4. Gate 1: plan

Runs on high risk, unclear architecture or a decision that is hard to reverse. The judge is `orchestrate:fable-oracle`. Read `${CLAUDE_SKILL_DIR}/references/gates.md` for the packet.

Done when the verdict is `Run` or the user has decided, or when no trigger applies.

## 5. Build

- Before the first delegation read `${CLAUDE_SKILL_DIR}/references/briefs.md`.
- Before every wait, tell the user in one line who is doing what and roughly how long it takes, because silence looks like a hang.
- Start independent agents in one message. At most five writers at once and never two in one file. Use a worktree only when the repository has commits, `worktree.baseRef` is `"head"` and the part needs no uncommitted changes, or it starts from stale code. Bring its changes back uncommitted, new files included.
- An agent stopped at its turn limit is resumed with SendMessage, because a new one has lost the context.
- A report is a claim: read the diff and run its Proof once. Keep proof proportionate: the failing case, the nearby boundaries and the project's check. A sweep of millions of cases or a second copy of an agent's investigation buys time lost, not safety.

Done when every part is in, its diff is read and the full check passes.

## 6. Review and release

- High risk: `orchestrate:opus-reviewer-deep`, whoever built it. Low risk with behaviour changed in several files: `orchestrate:opus-reviewer`. Otherwise your own check is the review.
- Freeze the diff first, as gates.md says, with `sh "${CLAUDE_SKILL_DIR}/scripts/snapshot.sh" <path>...`, which prints the id.
- Whoever built it fixes the A and B findings, unless the risk rose: then the high-risk rows in step 3 pick the owner. The same reviewer then checks those findings and the delta. C and D are reported, not looped on, and that includes test gaps where the code itself is right: they never cause another round or a gate 3. Two failed rounds, or two failed attempts at the same fault, trigger gate 3.
- Gate 2 runs on high risk once the review has zero A and B. After every oracle run, `sh "${CLAUDE_SKILL_DIR}/scripts/served-model.sh" <agent-id>` shows which model answered.

Done when the final diff has zero A and B and, on high risk, the verdict is `Release` or the user has decided. A fix after the last review means not done.

## 7. Close

1. For a frozen diff, take the id again. Another id means the verdict is void: go back to step 6.
2. The user's instruction in this session wins over the project's rules on committing and publishing. Commit only the job's paths, as gates.md step 6 says, so that the user's staged files stay theirs.
3. Remove the frozen diff, always before publishing, because a deploy that uploads the folder would carry it: `rm -rf .orchestrate-review`.
4. Publish as the project's rules and the user say, after the gates, because a gate after publishing protects nothing.
5. Report briefly in the user's language, result first: what changed, who did what, each gate with verdict and answering model, pre-existing problems the reviewers found, skipped steps, and what is not verified.

Done when nothing in the report lacks evidence from this session.
