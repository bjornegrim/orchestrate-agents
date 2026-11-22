# Briefs

An agent starts with nothing from your conversation. The brief is its whole understanding of the job, and the place where your judgment reaches it. A good brief can be carried out by someone who never saw the conversation.

## Template

```
Goal:     what is true when it is done, in one sentence
Why:      what the user is trying to achieve
Decided:  choices that are not to be reopened, each with its reason
Freedom:  what the agent decides itself, and when it stops to report
Files:    may change / may only read
Traps:    what can go wrong here, plus the project rules and skill guidance that apply
Proof:    command, and for a behaviour change the case that fails before and passes after
Risk:     low | high
```

- Keep the field names in English. Write the content in the user's language. The agent reports in that language.
- A scout needs only Goal, Why, Files and Proof (what counts as a complete answer).
- A UI tester also needs the address, the persona and data to enter, the widths, and a report file outside the published folders: `.orchestrate-review/` after the frozen-diff step has made it self-ignoring, or otherwise a temporary file.
- A reviewer gets the user's goal and reason, the path to the frozen diff and the proof command. It does not get your opinion of the change.
- Specialists get the outcome, the limits and the reasons. Leave the method to them. Workers and scouts get narrower scope and concrete cases.
- If the project commits or publishes automatically, say in Traps that you do it after review. Agents read those project rules too and would otherwise follow them.
- Give each prohibition its reason and its exception. A bare "never" is followed past the point where it makes sense.

## Worker

Bad:

```
Fix the date format in the order list. Run the tests.
```

It must guess the format, the files, whether exports change and what proof means.

Good:

```
Goal:     The order list shows dates as "22 Nov 2026" in all three columns.
Why:      Customers in two countries read 11/12 as different days.
Decided:  Use the existing formatDay() in src/lib/dates.ts, so there is one format in the app.
Freedom:  Test names and placement. Stop if a column gets a timestamp without a time zone.
Files:    Change src/orders/OrderList.tsx and its test. Read src/lib/dates.ts.
Traps:    The CSV export shares the row type and must keep ISO dates, because an importer parses them.
Proof:    npm test -- OrderList. A case with 2026-11-22 fails before and shows "22 Nov 2026" after.
Risk:     low
```

## Specialist

Bad:

```
Refunds are sometimes one cent wrong. Add Math.round on line 40 of refund.ts and check it.
```

It prescribes a fix before the cause is known, and gives no figure that would prove it.

Good:

```
Goal:     A partial refund never differs from the captured amount by rounding, and parts always sum to the whole.
Why:      Finance corrects about ten refunds a week by hand.
Decided:  Amounts stay integer cents in storage, because old rows and the payment provider use them.
Freedom:  Root cause, algorithm and test design. Stop if stored rows would need a migration.
Files:    Change src/payments/ and its tests. Read src/ledger/.
Traps:    Discounts are applied per line before tax. Refunds can be repeated until the order is used up.
Proof:    npm test -- payments. 10.00 split over three equal lines refunds 3.34 + 3.33 + 3.33: fails before, passes after.
Risk:     high
```

## Before you send

- Could the agent finish without asking you anything?
- Does Proof fail if the work is not done?
- Is everything you learned that could trap it in Traps?
- Does any other running agent own one of these files?
