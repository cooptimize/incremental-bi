---
title: Period snapshot
layer: snapshots
status: draft
related:
  - Snapshots/Snapshots Overview.md
  - Snapshots/Full History Snapshot.md
---

## What this is

Capture the full state of a dataset at regular intervals — daily, weekly,
monthly, or at period close. Each snapshot is a row or partition stamped with
the snapshot date. You don't track individual changes between snapshots; you
track what things looked like at each interval.

Common examples: inventory positions at end of day, account balances at period
close, AR aging as of month end.

## When to use it

- The business asks "what did X look like at period close" and the source
  doesn't retain that state
- Reporting needs are interval-based, not continuous (month-end, quarter-end)
- The unit of interest is an aggregate or position, not an individual record's
  change history

## When NOT to use it

- The source already maintains period-end history — consume that instead
- You need finer granularity than the snapshot interval (daily snapshot misses
  intra-day changes)
- The dataset is large and daily snapshots would create unmanageable storage
  growth — evaluate whether full history or a calculated approach is cheaper

## How it works

_TODO — cover: snapshot table structure (all columns + snapshot_date),
partitioning by snapshot date, insert pattern (never update, only insert),
how to query as-of a specific date._

## The hard parts

**Deletions.** If a record is deleted from the source between snapshots, it
will be absent from the next snapshot but present in all prior ones. Depending
on the use case this is correct behavior (you're preserving history) or a
problem (queries that compare snapshots need to account for records that appear
and disappear).

**Storage growth.** A period snapshot of a large table grows linearly with
time. A daily snapshot of a 10M row table is 3.65B rows per year. This is
manageable with partitioning and retention policies but requires deliberate
design.

**Late-arriving source data.** If the source is backdated after the snapshot
is taken, the snapshot is wrong and you have no record of what changed. Decide
upfront whether snapshots are immutable or whether corrections are applied.

## F&O specific notes

_TODO — F&O period close behavior, which entities make sense as period
snapshots, interaction with F&O ledger periods._

## Related patterns

- [Snapshots overview](Snapshots%20Overview.md)
- [Full history](Full%20History%20Snapshot.md) — alternative when you need change
  granularity between intervals
- [Incremental aggregate recalculation](../gold/incremental-aggregate-recalc.md)
  — related problem when aggregates need to be recalculated over time

## Open questions

_TODO_
