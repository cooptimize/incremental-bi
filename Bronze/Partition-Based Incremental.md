---
title: Partition-based incremental
layer: bronze
status: draft
related:
  - Cross-Cutting/Delete Detection Strategies.md
  - Cross-Cutting/Watermark Strategy.md
---

## What this is

Pull only the records belonging to recent partitions, defined by an immutable
date field on the source. Instead of reloading the whole table, you reload
only the current period (e.g., current month, current year) on each run.

The classic example: sales orders by created date. You only pull orders created
in the current month, because older partitions are assumed stable.

This is not CDC. There is no change signal. You're making an assumption about
data stability to avoid a full reload.

## When to use it

- Source table is too large for full load on every run
- No CDC feed is available
- There is an immutable date field that reliably partitions the data
  (created date, posted date, transaction date that cannot be backdated)
- Deletes of recent records are either acceptable to miss or handled separately

## When NOT to use it

- The date field can be changed retroactively (F&O allows backdating on many
  transaction types — this assumption breaks silently)
- Old records can be deleted (see hard parts below)
- The source has no reliable immutable date field

## How it works

_TODO — cover the basic mechanics: define partition window, pull records where
date field falls in window, upsert to bronze. Overlap window sizing (reload
last N days as buffer)._

## The hard parts

**The delete problem.** This pattern has no delete signal for records outside
the active reload window. If a sales order created in January is deleted in
June, and you're only reloading the current month, you will never see that
deletion. The record stays in bronze indefinitely.

Options:
- Accept the risk (appropriate if deletes are rare and business impact is low)
- Periodic full reconciliation — run a full load on a slower cadence (weekly,
  monthly) to catch accumulated deletions
- Add a separate delete-check job that compares bronze to source for older
  partitions
- Use a watermark on a secondary field to catch soft deletes (if the source
  soft-deletes with a flag or timestamp)

None of these are clean. This is a fundamental limitation of the pattern.

**The backdating problem.** F&O allows financial backdating. A transaction
posted today may carry an effective date in a prior period. If your partition
field is effective date rather than created date, recently-posted old records
will fall outside your reload window and be missed.

**Partition boundary drift.** If the partition window is too narrow, late-
arriving records near the boundary are missed. Overlap (reload last N days
extra) helps but adds cost and doesn't eliminate the problem.

## F&O specific notes

_TODO — which F&O transaction types allow backdating, which date fields are
genuinely immutable, known gotchas with created vs. posted vs. effective date._

## Related patterns

- [Delete detection](../Cross-Cutting/Delete%20Detection%20Strategies.md) — this pattern
  deliberately defers the delete problem; that file covers your options
- [Watermark management](../Cross-Cutting/Watermark%20Strategy.md) — watermarks can
  supplement this pattern but don't solve the delete gap
- [Full load](Full%20Load.md) — the fallback when partition assumptions break
- [My source doesn't signal deletes](../decisions/source-has-no-delete-signal.md)
  — decision tree for handling the delete gap

## Open questions

- What is a reasonable periodic reconciliation cadence for typical F&O
  transaction tables?
- Can the overlap window be sized analytically, or is it always a judgment call?
- Are there F&O entities where no immutable date field exists at all?
