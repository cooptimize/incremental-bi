---
title: Watermark strategy
layer: cross-cutting
status: working
related:
  - Cross-Cutting/Delete Detection Strategies.md
  - Gold/Dimension Patterns/Dimension Incremental Load.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

## What this is

A watermark is a stored timestamp marking the boundary between "already processed" and "not yet processed." On every incremental load: query changes since the watermark, advance it when the load succeeds.

**Always require `SinkModifiedOn`.** If unavailable at record level, use the parquet file's modified timestamp. This is a lake perspective — the file is reloaded, the timestamp advances, and you have a watermark.

## The pattern

**1. Store per-table in a control table (not pipeline state):**
```sql
CREATE TABLE control.watermarks (
  table_name VARCHAR(255),
  last_successful_watermark DATETIME,
  PRIMARY KEY (table_name)
);
```

**2. Record the run start BEFORE querying:**
```sql
SET @run_start = SYSUTCDATETIME();
```

**3. Query using the last watermark:**
```sql
SELECT * FROM silver.Customer
WHERE SinkModifiedOn > (SELECT last_successful_watermark 
                         FROM control.watermarks 
                         WHERE table_name = 'Customer')
```

**4. Advance only on success:**
```sql
IF @pipeline_succeeded = 1
  UPDATE control.watermarks
  SET last_successful_watermark = @run_start
  WHERE table_name = 'Customer';
```

Recording at run start (not run end) ensures you don't skip rows that arrive mid-query.

## The hard parts

**Source timestamp doesn't update on changes you care about.** Cascading updates, status redefinitions, or out-of-band changes (data fixes) can alter a row without bumping `SinkModifiedOn`. No watermark tuning fixes this — you need a different signal (soft-delete flag, audit table, or periodic reconciliation). See [Delete detection](Delete%20Detection%20Strategies.md).

**Clock skew and missed rows.** If source and pipeline clocks drift, naive `> @watermark` can miss rows in flight. Mitigate with small overlap (re-query the last 5-10 minutes, rely on idempotent UPSERT to no-op reprocessed rows).

**Multi-table coordination.** Single watermark across related tables (order + lines) won't keep them perfectly in sync. See gold/fact-patterns/incremental-date-partition.md for partition-based alternative.

## When NOT to use

- Source reliability is uncertain (you need a full reload fallback — use `@ForceUpdate = 2`)
- Financial period close requires certainty (use full reload or reconciliation instead)
- Multiple tables must be perfectly consistent (use partition-based incremental instead)

## F&O specific notes

- `modifiedDateTime` is the business-layer timestamp (what changed in F&O)
- `SinkModifiedOn` is the export timestamp (when it landed in your lake)
- Cascading updates (child changes but parent timestamp doesn't move) are a known F&O limitation
