# Gates and frozen diffs

The oracle has fresh eyes. It sees only the packet and what it reads itself, so the packet decides the quality of the verdict. Normally a job uses at most two gates.

Remove secret values from every packet. The oracle does not read CLAUDE.md, so quote the project rules that apply. Do not consult the advisor on the same decision as a gate: that pays twice for one judgment.

## Gate 1: plan

Trigger: high risk, unclear architecture or a decision that is hard to reverse. Runs before the build.

```
Gate: 1, plan
Request: <the user's words, verbatim>
Plan: <parts, owners, files, proof>
Chosen and rejected: <each route and the reason>
Project rules: <quoted, or "none">
Read: <file paths>
Answer:
Verdict: Run | Change | Ask user
Most dangerous assumption: <and how to test it>
Changes: <what and why, or "none">
Question: <only with Ask user>
```

Leave out the outcome you hope for.

- `Change`: revise and resume the same oracle once. Still not `Run`: the user decides.
- `Ask user`: put the question to the user.

## Gate 2: release

Trigger: high risk, after a review with zero A and B. Runs before commit.

```
Gate: 2, release
Request: <the user's words, verbatim>
Frozen diff: <file path> (id <tree id>)
Proof: <commands and decisive output>
Project rules: <quoted, or "none">
Read: <file paths>
Answer:
Verdict: Release | Stop
Findings: <path:line, effect on the user, evidence, or "none">
Not judged: <what could not be checked>
```

Leave out the reviewer's findings and verdict, which would anchor the oracle.

- `Stop`: fix, have the same reviewer approve the new diff, then resume the same oracle once. A second `Stop` is always decided by the user.

## Gate 3: deadlock

Trigger: two failed attempts at the same fault, or two failed reviews.

```
Gate: 3, deadlock
Request: <the user's words, verbatim>
Symptom: <what happens, and what should happen>
Attempts: <what was tried and what each produced>
Raw errors: <verbatim>
Project rules: <quoted, or "none">
Read: <file paths>
Answer:
Root cause: <cause, with evidence>
Confidence: high | medium | low
Next experiment: <one step and what its result proves>
```

Leave out your theory of the cause, or mark it as a guess.

- No retry of the gate. Make one new build attempt and have it checked as usual. If that fails, the user decides.

## Rejecting advice

You may reject the oracle's advice only with evidence: a file and line, or command output. Report the rejection. Without evidence the user decides.

## Who answered

An agent's statement about its own model is not proof. After every run of the oracle, run the served-model helper from SKILL.md on the agent id, then follow this table. It applies to the oracle only, and the label goes in the report in the user's language:

| Result | Label | Then |
| --- | --- | --- |
| Only Fable models | `Gate: Fable` | Use the verdict |
| Any other model, for example after a safety fallback or a substitution | `Gate: <model>, not Fable` | Run the gate again on a new deep reviewer |
| The oracle cannot start, has no quota or needs credits | `Gate: Opus, not Fable` | Run the gate on a new deep reviewer |
| The helper finds no log or no answer | `Gate: model not verified` | Use the verdict and show the label |

- The substitute is a new instance, never the one that reviewed the diff, and gets the same packet.
- The substitute's verdict is used and is never substituted again, although it is not Fable. Run the helper on it only to name its model in the report, beside the label and the reason.
- A retry of a gate that a substitute answered resumes that substitute.
- Never turn on or accept usage credits. That is the user's money and their decision.
- If the substitute cannot run either, stop before commit and ask the user.

## Frozen diff

A verdict covers exactly the code that was judged.

1. From the repository root, list what is uncommitted:

   ```sh
   head=$(git rev-parse -q --verify HEAD || git hash-object -t tree --stdin </dev/null)
   git -c core.quotepath=off diff --name-only --no-renames "$head"
   git -c core.quotepath=off ls-files --others --exclude-standard
   ```

   Keep this job's paths and drop the user's untouched changes. Name files, not `.`, so unrelated files and secrets stay out. A file that holds secret values is never named. List it as not judged.
2. Run the snapshot helper from SKILL.md on those paths. The result is the id. If the list is empty because the work is already committed, the id is `git rev-parse 'HEAD^{tree}'`.
3. Write the diff from the base recorded in step 1 of SKILL.md to a file in the session's scratch directory, or a temporary directory if there is none. From the base it also covers work committed during the job:

   ```sh
   git diff <base> <id> > "<file>"
   ```

4. Give reviewer and oracle the file path and the id.
5. After each review and before commit, make the list again and take the id again, because files appear and disappear with fixes. A different id voids the verdict.
6. At commit, once the reviewed paths are staged, `git write-tree` equals the id. Any other staged path makes it differ.

Without git, give the files themselves and report `Input: not frozen`.
