---
title: Partition keys
layer: cross-cutting
status: working
related:
  - Silver/Change Tracking Partitions.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

Partition on extraction time, stored as an integer column, computed once in silver. Everything downstream joins on it instead of recomputing it.

## The column

```sql
YEAR(SinkCreatedOn) * 100 + MONTH(SinkCreatedOn) AS SinkCreatedMonth,
YEAR(SinkCreatedOn) * 10000 + MONTH(SinkCreatedOn) * 100
    + DAY(SinkCreatedOn)                                AS SinkCreatedDay
```

Write it at silver load time — or as a persisted computed column where the platform allows one — on every silver table that feeds a partition-reloaded fact, on `silver._ChangeTracker`, and on the fact table itself. Gold never derives it.

Name the interval off the timestamp it came from. `SinkCreatedMonth`, not `SinkMonth`: `SinkModifiedOn` exists too, and a name that doesn't say created or modified doesn't say anything.

## Why extraction time and not a business date

- **Backdating.** F&O posts an order today with an effective date in March. Partition on the business date and the row lands in March, outside any recent reload window, and the change never reaches gold.
- **Extraction time never moves.** A row's partition is fixed the moment it's written, so silver, the change tracker, and gold always agree on what a partition holds.

Effective date, posting date, and transaction date all fail the same way.

This is a different decision from [bronze partition-based incremental](../Bronze/Partition-Based%20Incremental.md), which windows on a business date because at that point extraction time doesn't exist yet. That pattern is choosing what to pull; this one is choosing what to replace.

## Granularity

Month by default. Go to `SinkCreatedDay` when a single month is large enough that reloading it hurts — usually the initial-load partition, which holds the entire history.

Track at the granularity gold reloads at. A tracker keyed by day feeding a fact that reloads by month just accumulates rows nobody reads.
