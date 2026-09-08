---
title: Power BI incremental refresh with deletions (the hard version)
layer: semantic-model
status: working
related:
  - Cross-Cutting/Delete Detection Strategies.md
  - semantic-model/incremental-period.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

## What this is

How to make Power BI incremental refresh work when the source fact table has deletions. Spoiler: it's hard, requires a separate change-tracking metadata layer, and probably not worth doing unless your refresh window is severely constrained.

**TL;DR:** Power BI's incremental refresh is designed for append-only tables. It has no native delete handling. To support deletes, you must:
1. Build a change-tracking layer in gold that combines inserted, updated, and deleted rows
2. Feed Power BI that metadata layer instead of the raw fact table
3. Maintain this metadata layer in sync with your gold incremental load

---

## The fundamental problem

Power BI's incremental refresh works like this:

```
IF date_column >= @RangeStart AND date_column < @RangeEnd
  THEN refresh that partition
  ELSE leave it alone
```

This assumes:
- **Rows are only added, never removed** — a partition, once loaded, stays complete
- **The date partition key is immutable** — a row's partition doesn't change
- **Schema is stable** — no column drops, renames, or type changes

When deletions occur, Power BI still thinks the partition is current (it was loaded before), so it doesn't refresh. Deleted rows stay in the semantic model forever.

---

## Why you can't just use SinkCreatedOn

If you partition Power BI by `SinkCreatedOn` from gold:

1. Gold layer reloads a partition when it has changes
2. Deleted rows disappear from gold
3. Power BI still thinks that partition is loaded and current
4. Power BI never reloads it
5. Deleted rows remain in Power BI indefinitely

The Synapse Link reset problem makes this worse: if SinkCreatedOn is rebuilt at the source, Power BI's partition metadata becomes invalid, and you've orphaned partitions you can't reach.

**Solution:** Don't partition Power BI by SinkCreatedOn. Build a metadata layer instead.

---

## The pattern: Change-tracking metadata layer

Instead of pointing Power BI at the fact table directly, create a change-tracking table that tracks:
- Rows inserted in each load cycle
- Rows updated in each load cycle
- Rows deleted in each load cycle
- A load date or version identifier

Power BI increments on the load date, not the business date.

### 1. Build the metadata table in gold

```sql
CREATE TABLE gold.FactSalesChanges (
  LoadDateKey INT,              -- 20260831
  ChangeType VARCHAR(10),        -- 'INSERT', 'UPDATE', 'DELETE'
  
  -- Business key columns
  salesid VARCHAR(20),
  lineno INT,
  
  -- Factual data (NULL for deletes)
  itemid VARCHAR(50),
  qty DECIMAL(18,6),
  amount MONEY,
  unitprice MONEY,
  
  -- Lineage
  SinkCreatedOn DATETIME,
  SinkModifiedOn DATETIME,
  
  PRIMARY KEY (LoadDateKey, ChangeType, salesid, lineno)
);
```

### 2. Populate on each load cycle

After your gold incremental load completes:

```sql
DECLARE @LoadDateKey INT = CAST(FORMAT(GETDATE(), 'yyyyMMdd') AS INT);

-- Track inserted rows (new to fact table in this cycle)
INSERT INTO gold.FactSalesChanges
SELECT 
  @LoadDateKey as LoadDateKey,
  'INSERT' as ChangeType,
  f.salesid, f.lineno, f.itemid, f.qty, f.amount, f.unitprice,
  f.SinkCreatedOn, f.SinkModifiedOn
FROM gold.FactSales f
WHERE f.SinkModifiedOn >= DATEADD(MINUTE, -5, GETDATE()) -- This load's window
  AND NOT EXISTS (
    SELECT 1 FROM gold.FactSalesChanges fsc
    WHERE fsc.salesid = f.salesid 
      AND fsc.lineno = f.lineno
      AND fsc.LoadDateKey = @LoadDateKey
  );

-- Track updated rows (modified in silver, reloaded)
INSERT INTO gold.FactSalesChanges
SELECT 
  @LoadDateKey as LoadDateKey,
  'UPDATE' as ChangeType,
  f.salesid, f.lineno, f.itemid, f.qty, f.amount, f.unitprice,
  f.SinkCreatedOn, f.SinkModifiedOn
FROM gold.FactSales f
INNER JOIN (
  SELECT salesid, lineno FROM gold.FactSales_prev
  EXCEPT
  SELECT salesid, lineno FROM gold.FactSales
) deleted ON f.salesid = deleted.salesid AND f.lineno = deleted.lineno
WHERE f.SinkModifiedOn >= DATEADD(MINUTE, -5, GETDATE());

-- Track deleted rows (existed before, don't now)
INSERT INTO gold.FactSalesChanges
SELECT 
  @LoadDateKey as LoadDateKey,
  'DELETE' as ChangeType,
  fp.salesid, fp.lineno, NULL, NULL, NULL, NULL,
  fp.SinkCreatedOn, GETDATE() as SinkModifiedOn
FROM gold.FactSales_prev fp
WHERE NOT EXISTS (
  SELECT 1 FROM gold.FactSales f
  WHERE f.salesid = fp.salesid AND f.lineno = fp.lineno
);
```

### 3. Point Power BI at the metadata table

In Power BI, create an incremental refresh policy on `FactSalesChanges`:

```
Range Start: LoadDateKey >= MINPRICE
Range End: LoadDateKey < MAXPRICE
Partition: LoadDateKey
```

Power BI now refreshes by load date, not business date. Every load cycle is a partition.

### 4. Power BI model handles changes

In your fact table definition, you need logic to:

```DAX
FactSales =
VAR InsertRows = FILTER(
  FactSalesChanges,
  [ChangeType] = "INSERT"
)
VAR UpdateRows = FILTER(
  FactSalesChanges,
  [ChangeType] = "UPDATE"
)
VAR DeleteRows = FILTER(
  FactSalesChanges,
  [ChangeType] = "DELETE"
)
RETURN
UNION(InsertRows, UpdateRows) -- Deletes are excluded
```

Deleted rows never appear in reports.

---

## The complexity tax

**What you just added:**
- A second table in gold (`FactSalesChanges`)
- Change-type tracking logic in every load
- Comparison logic to detect inserts/updates/deletes
- A DAX model that knows about change types
- Maintenance of that tracking table over time

**What you got:**
- Power BI incremental refresh that actually handles deletes
- Partitions that refresh when deletions occur
- Observable change history (if you want it)

**The math:**
- If your fact table refreshes in < 20 minutes full: **don't do this**
- If your fact table refreshes in 1-2 hours full: consider it
- If your fact table refreshes in > 2 hours: probably necessary

---

## The harder problem: Synapse Link resets

Synapse Link periodically resets tables. When it does:
- All `SinkCreatedOn` values are rebuilt from scratch
- Partitions that existed before no longer exist
- Your change-tracking metadata becomes invalid

You'd need to:
1. Detect that a reset occurred (old SinkCreatedOn values no longer appear)
2. Mark all existing partitions in the metadata as invalid
3. Force a full Power BI refresh (via API)
4. Resume incremental loading

This requires external monitoring and the Power BI REST API. See [[Fact Partition Rebuild]] for reset detection in gold.

---

## Alternative: Just do full refreshes

Seriously consider this.

```
IF your_fact_table_refresh_time <= 30 minutes:
  DO full refresh every night
  DONE
ELSE:
  Look at the change-tracking layer above
ENDIF
```

Full refresh is:
- Simple to understand and maintain
- Observable (you see if it succeeds or fails)
- Correctness-guaranteed (no orphaned partitions)
- Not that expensive if your table isn't enormous

The metadata layer exists to optimize for the case where full refresh is legitimately expensive. If it isn't, the optimzation is wasted complexity.

---

## F&O specific notes

Sales orders and lines are frequently deleted (cancellations, voids). If you need those deletions visible in Power BI the instant they happen, the change-tracking layer is required.

But: most F&O reporting doesn't care about same-day deletion visibility. A nightly full refresh is fine. Check your actual SLA before building this.


---

## Safety guardrails

1. **Test deletion detection** — Verify your change-type detection correctly identifies inserts/updates/deletes
2. **Validate metadata freshness** — Check that change-tracking table is in sync with fact table after each load
3. **Monitor for resets** — If using Synapse Link, watch for SinkCreatedOn anomalies
4. **Document the model** — Anyone reading your Power BI model must understand change-type logic
5. **Schedule reconciliation** — Monthly check that no deletions were missed

---

## Related patterns

- [Fact partition rebuild](../Gold/Fact%20Patterns/Fact%20Partition%20Rebuild.md) — The gold layer strategy
- [Delete detection](../Cross-Cutting/Delete%20Detection%20Strategies.md) — Detecting deletions generally
- [Incremental refresh without deletes](semantic-model/incremental-period.md) — Simpler pattern for append-only tables

---

## Open questions

- At what table size does full refresh become infeasible?
- Can you detect a Synapse Link reset automatically and trigger a Power BI full refresh via REST API?
- Is there a simpler way to track changes than a separate metadata table?
