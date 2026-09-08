---
title: Full load
layer: bronze
status: draft
related:
  - Cross-Cutting/Delete Detection Strategies.md
  - cross-cutting/layer-strategy-mismatch.md
  - Bronze/Partition-Based Incremental.md
---

## What this is

Truncate the bronze target and reload the entire source table on every run.
No change tracking, no watermarks, no assumptions about what changed.

The source can be a database (direct query, bulk export to parquet) or an API
(paginated pull). The core pattern is the same either way. Operational
differences are minor — APIs add pagination, rate limits, and timeout handling,
but the load logic is identical.

## When to use it

- Table is small enough that full reload is cheap
- No CDC feed is available and partition-based incremental isn't safe
  (date fields aren't reliably immutable, or deletes matter)
- After a schema change that requires a clean reload
- As a periodic reconciliation pass on top of a partition-based incremental

## When NOT to use it

- Table is large and reload time exceeds your SLA
- Source API has rate limits that make full extraction infeasible
- You have CDC available — full load is unnecessary cost

## How it works

_TODO — cover the basic mechanics: truncate/overwrite target, pull source in
bulk or pages, write to bronze. For APIs: pagination pattern, handling
timeouts and restarts mid-pull, idempotency (write to staging location first,
swap on completion)._

## The hard parts

**Delete detection is free but implicit.** Records absent from the current
pull are gone. This is the one bronze pattern where deletes are trivially
detectable — but only because you pulled everything. Downstream layers need
to handle this correctly (a record missing from bronze this run may have been
deleted, or may be a load failure).

**Cost at scale.** Full load cost scales with table size, not change volume.
For large F&O transaction tables (GL journal lines, inventory transactions)
this can be prohibitive.

**API operational quirks.** For API sources: pagination state is lost on
failure, so restarts re-pull from the beginning unless you checkpoint.
Rate limits may force the run to span multiple hours, during which the source
is changing. The "full load" is actually a snapshot over a window of time,
not a single consistent point.

## F&O specific notes

_TODO — which F&O entities are large enough that full load is impractical,
Fabric Link as an alternative to direct API extraction for large tables._

## Related patterns

- [Delete detection](../Cross-Cutting/Delete%20Detection%20Strategies.md) — full load makes
  delete detection simple; downstream patterns still need to handle it
- [Bronze-full / gold-incremental mismatch](../cross-cutting/layer-strategy-mismatch.md)
  — common pattern where bronze full-loads but gold tries to stay incremental
- [Partition-based incremental](Partition-Based%20Incremental.md) — the
  alternative when full load is too expensive

## Open questions

- For API sources: what's the right checkpointing strategy for a multi-hour
  paginated pull?
- At what table size does full load become impractical in typical Fabric
  pipeline configurations?
