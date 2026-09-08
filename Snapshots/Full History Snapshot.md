---
title: Full history snapshot
layer: snapshots
status: draft
related:
  - Snapshots/Snapshots Overview.md
  - Snapshots/Period Snapshot.md
  - Cross-Cutting/Delete Detection Strategies.md
---

## What this is

Append every observed state of a record as it changes. The table grows with
each change event — every version of a record exists as its own row, with
effective dates marking when that version was current.

Unlike period snapshots, you're not capturing state at intervals. You're
capturing state at every change. The result is a complete audit trail.

## When to use it

- Audit requirements demand a preserved record of every state a record passed
  through
- The source overwrites in place and you need to reconstruct history the source
  discards
- Query patterns require "what did this record look like at any arbitrary point
  in time," not just at regular intervals

## When NOT to use it

- The source already tracks this history with date-effective rows — consume
  that instead, don't rebuild it
- The business requirement is period-end reporting — a period snapshot is
  cheaper and simpler
- Change frequency is high — a record that changes daily produces 365 rows per
  year per record; at scale this becomes expensive fast

## How it works

_TODO — cover: table structure (all columns + valid_from, valid_to, is_current),
how rows are inserted on change detection, how valid_to is set on the prior
row, querying as-of a date._

## The hard parts

**Requires a reliable change signal.** Full history only works if you know when
something changed. If your bronze is a full load, you need to diff against the
prior state to detect changes — which is expensive on large tables. If your
bronze is CDC, you get changes directly but need to handle ordering carefully.

**Deletions are philosophically ambiguous.** When a source record is deleted,
do you end-date the last version and keep it? Hard-delete it from history? Keep
it with a deleted flag? The right answer depends on why records get deleted in
the source and what the business needs from the history.

**Storage and query cost.** High-churn tables generate large history tables
fast. Queries against them require filtering on effective dates, which can be
expensive without careful partitioning and indexing.

## F&O specific notes

_TODO — which F&O entities change frequently enough to make full history
expensive, interaction with F&O's own audit log features._

## Related patterns

- [Snapshots overview](Snapshots%20Overview.md) — including when to check the source
  before building this
- [Period snapshot](Period%20Snapshot.md) — cheaper alternative when
  interval-based history is sufficient
- [Delete detection](../Cross-Cutting/Delete%20Detection%20Strategies.md) — the deletion
  question is particularly sharp here

## Open questions

_TODO_
