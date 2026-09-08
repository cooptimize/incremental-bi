---
title: Change tracking partitions
layer: silver
status: working
related:
  - Silver/Incremental with Hard Delete.md
  - Silver/Full Load.md
  - Cross-Cutting/Watermark Strategy.md
---

## What this is

A metadata table that tracks `MAX(SinkModifiedOn)` per source table per `SinkCreatedMonth/SinkCreatedDay` partition. Instead of gold rescanning all source tables to find changes, gold queries one small table to know which partitions changed.

Enables partition-based reloading at gold without expensive change detection queries.

## When to use it

- Multiple source tables feed facts; gold must know which partitions to reload
- Table is large; rescanning to find changes is expensive
- Partitions are by extraction cohort (SinkCreatedOn YYYYMM or YYYYMMDD)

## The metadata table

```sql
CREATE TABLE silver._ChangeTracker (
  SourceTable NVARCHAR(255),
  SinkCreatedMonth INT,           -- YYYYMM of SinkCreatedOn
  SinkCreatedDay INT,             -- YYYYMMDD of SinkCreatedOn (optional, for daily granularity)
  MaxSinkModifiedOn DATETIME,
  RowCount INT,
  LastUpdatedDateTime DATETIME DEFAULT GETDATE(),
  PRIMARY KEY (SourceTable, SinkCreatedMonth, SinkCreatedDay)
);

CREATE INDEX idx_ChangeTracker_Modified 
  ON silver._ChangeTracker(MaxSinkModifiedOn DESC);
```

## Populate after loading each source table

After loading silver.Customer from bronze:

```sql
MERGE INTO silver._ChangeTracker t
USING (
  SELECT 
    'Customer' AS SourceTable,
    YEAR(c.SinkCreatedOn) * 100 + MONTH(c.SinkCreatedOn) AS SinkCreatedMonth,
    YEAR(c.SinkCreatedOn) * 10000 + MONTH(c.SinkCreatedOn) * 100 
      + DAY(c.SinkCreatedOn) AS SinkCreatedDay,
    MAX(c.SinkModifiedOn) AS MaxSinkModifiedOn,
    COUNT(*) AS RowCount
  FROM silver.Customer c
  GROUP BY YEAR(c.SinkCreatedOn) * 100 + MONTH(c.SinkCreatedOn),
           YEAR(c.SinkCreatedOn) * 10000 + MONTH(c.SinkCreatedOn) * 100 
             + DAY(c.SinkCreatedOn)
) s
ON t.SourceTable = s.SourceTable 
  AND t.SinkCreatedMonth = s.SinkCreatedMonth 
  AND t.SinkCreatedDay = s.SinkCreatedDay
WHEN MATCHED THEN
  UPDATE SET MaxSinkModifiedOn = s.MaxSinkModifiedOn, RowCount = s.RowCount, LastUpdatedDateTime = GETDATE()
WHEN NOT MATCHED THEN
  INSERT (SourceTable, SinkCreatedMonth, SinkCreatedDay, MaxSinkModifiedOn, RowCount, LastUpdatedDateTime)
  VALUES (s.SourceTable, s.SinkCreatedMonth, s.SinkCreatedDay, s.MaxSinkModifiedOn, s.RowCount, GETDATE());
```

Do this for every source table in the same pipeline run, immediately after load.

## Gold queries the tracker

Find which partitions changed since last gold load:

```sql
DECLARE @gold_watermark DATETIME = (SELECT MAX(watermark) FROM gold._LoadWatermark);

SELECT DISTINCT SourceTable, SinkCreatedMonth, SinkCreatedDay
FROM silver._ChangeTracker
WHERE MaxSinkModifiedOn > @gold_watermark
ORDER BY SinkCreatedMonth, SinkCreatedDay;
```

Result: list of `(Customer, 202608, 20260815)`, `(SalesLine, 202608, 20260815)`, etc.

Gold then reloads only those partitions.

## The hard parts

### Tracker sync

If source table is updated but tracker is not, gold won't see the change.

**Mitigation:**
- Update tracker immediately after each source load (same pipeline step)
- Validate: tracker row counts match actual silver table counts monthly
- On mismatch, re-run tracker update for that table

### Tracker bloat

Tracker grows one row per (SourceTable, partition_date) combo. Over time:
- 5 source tables × 365 days × 3 years = ~5,475 rows (small, manageable)
- Index scan is still fast

**Mitigation:** Archive old partitions periodically. When you delete old data from silver, delete corresponding tracker rows.

### Partition granularity

If you track daily but reload monthly in gold, tracker has orphaned rows (daily partitions that gold never queries).

**Decision:** Match tracker granularity to gold reload granularity. If gold reloads YYYYMM, tracker tracks YYYYMM only (drop SinkCreatedDay column).

### Multi-table coordination

If only SalesLine changes but SalesTable doesn't, tracker shows asymmetric updates.

Gold sees SalesLine partition changed. Does it reload the fact?

**Answer: Yes.** Gold JOIN statement re-processes the fact with (updated SalesLine, current SalesTable). Safe because JOIN is idempotent.

## F&O patterns

By entity, suggested partition key:
- Sales: `SinkCreatedOn` (order creation month)
- GL: `SinkCreatedOn` (fiscal month of entry)
- Inventory: `SinkCreatedOn` (transaction month)
- Customers/Vendors: `SinkCreatedOn` (reference data, less critical)

Use `SinkCreatedOn` (extraction date), not business date, for partition stability.

## Validation guardrails

1. **Monthly:** Compare tracker row counts vs. actual silver row counts per table
2. **On schema change:** Reset tracker for affected table (delete rows, repopulate)
3. **On manual intervention:** Log changes to tracker with reason (for audit)
4. **On data deletion:** Remove corresponding tracker rows

## Related patterns

- [Incremental with hard delete](Incremental%20with%20Hard%20Delete.md) — Uses this tracker to drive partition reloads
- [Fact partition rebuild](../Gold/Fact%20Patterns/Fact%20Partition%20Rebuild.md) — consumes the tracker to decide which partitions to reload
- [Partition keys](../Cross-Cutting/Partition%20Keys.md) — where SinkCreatedMonth comes from and why it is extraction time
