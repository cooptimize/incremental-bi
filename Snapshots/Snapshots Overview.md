---
title: Snapshots — overview
layer: snapshots
status: draft
related:
  - Snapshots/Period Snapshot.md
  - Snapshots/Full History Snapshot.md
  - Cross-Cutting/Delete Detection Strategies.md
---

## What this is

A snapshot is a preserved copy of data state at a point in time. Instead of
overwriting records when they change, you keep the prior state alongside the
new one. The result is a table you can query as-of any point in time.

Snapshots are a legitimate and sometimes necessary pattern. They are also
frequently reached for when the right answer is simpler.

## Before building a snapshot: check the source

F&O and most ERP systems already maintain date-effective history for data that
changes over time: prices, exchange rates, worker assignments, organizational
hierarchies, tax configurations. This history exists in the source because the
business needs it there — transactions are posted against the rates and
assignments that were in effect at the time.

If you need "what was the exchange rate on this date," the answer is in F&O's
date-effective exchange rate table. Building a snapshot in the BI layer to
reconstruct that history is duplicating complexity the source already solved.

Before designing a snapshot pattern, ask: does the source already track this
history? If yes, consume it. Don't rebuild it.

Snapshots belong in the BI layer when:
- The source doesn't maintain history for data that changes (overwrite in place)
- You need a point-in-time view of an aggregate or calculated state, not a
  single record
- You need period-end reporting where the state at close is distinct from
  current state (inventory positions, account balances, AR aging)
- Audit requirements demand a preserved record of what the pipeline saw,
  regardless of source changes

## What snapshots are not

Snapshots are not a general solution for tracking change. Applying snapshot
logic to every dimension in a data model because "things change" is
over-engineering that adds storage cost, query complexity, and pipeline
fragility without a clear business requirement driving it.

If a report needs current state, use current state. If a report needs
historical state, find out whether the source already provides it before
building a layer to manufacture it.

## Approaches

- [Period snapshot](Period%20Snapshot.md) — capture state at regular intervals
  (daily, monthly, period-end). Common for balances and positions.
- [Full history](Full%20History%20Snapshot.md) — append every change as it arrives.
  Higher storage cost, richer query capability.

## Open questions

_TODO_
