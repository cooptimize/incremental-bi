---
title: Incremental with hard delete
layer: silver
status: working
related:
  - Cross-Cutting/Watermark Strategy.md
  - Cross-Cutting/Delete Detection Strategies.md
---

## What this is

Hard delete at silver: physically remove deleted rows. Silver shows only current state. Data was deleted for a reason — don't keep tombstones.

Uses a change tracking table to record `MAX(SinkModifiedOn)` per source table per `SinkCreatedMonth/SinkCreatedDay`, enabling gold to know which partitions changed without rescanning all source tables.

## When to use it

- Deletions must be reflected in gold immediately
- Storage cost of soft-delete history is unacceptable
- Audit trail is maintained separately (if at all)
- Bronze retains full history (you can always re-extract if needed)

## When NOT to use it

- Gold must support incremental loads without periodic full reloads
- Deletions signal corrections/reversals that downstream must detect
- You cannot afford periodic gold rebuilds to catch deletion cascades

## The pattern

### 1. Change tracking table (metadata)

Track `MAX(SinkModifiedOn)` per table per extraction period:

```sql
CREATE TABLE silver._ChangeTracker (
  SourceTable NVARCHAR(255),
  SinkCreatedMonth INT,          -- YYYYMM of SinkCreatedOn
  SinkCreatedDay INT,            -- YYYYMMDD of SinkCreatedOn (optional, for daily tracking)
  MaxSinkModifiedOn DATETIME,
  RowCount INT,
  LastUpdatedDateTime DATETIME DEFAULT GETDATE(),
  PRIMARY KEY (SourceTable, SinkCreatedMonth, SinkCreatedDay)
);

CREATE INDEX idx_change_tracker_modified 
  ON silver._ChangeTracker(MaxSinkModifiedOn DESC);
```

### 2. After loading each source table, update tracker

```sql
-- After loading silver.Customer from bronze.Customer
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

### 3. Hard delete on ingest

Remove records that no longer exist in source:

```sql
-- Upsert + hard delete
MERGE INTO silver.Customer t
USING bronze.Customer s
  ON t.DataAreaId = s.DataAreaId AND t.CustomerId = s.CustomerId
WHEN MATCHED AND s.SinkModifiedOn > (
  SELECT MAX_SINK_MODIFIED_ON FROM silver._ChangeTracker 
  WHERE SourceTable = 'Customer'
) THEN
  UPDATE SET 
    t.CustomerName = s.CustomerName,
    t.CustomerGroup = s.CustomerGroup,
    t.SinkModifiedOn = s.SinkModifiedOn
WHEN NOT MATCHED BY TARGET THEN
  INSERT (DataAreaId, CustomerId, CustomerName, CustomerGroup, SinkCreatedOn, SinkModifiedOn)
  VALUES (s.DataAreaId, s.CustomerId, s.CustomerName, s.CustomerGroup, s.SinkCreatedOn, s.SinkModifiedOn)
WHEN NOT MATCHED BY SOURCE THEN
  DELETE;  -- Hard delete: records not in source are gone
```

### 4. Gold queries the tracker to find changed partitions

```sql
-- Find which SinkCreatedMonth partitions changed since last load
SELECT DISTINCT SourceTable, SinkCreatedMonth
FROM silver._ChangeTracker
WHERE MaxSinkModifiedOn > (
  SELECT watermark FROM gold._LoadWatermark WHERE target_table = 'SalesFact'
)
ORDER BY SinkCreatedMonth;
```

## The hard parts

### Irreversibility

Once deleted from silver, the row is gone. You cannot reconstruct it without re-extracting from bronze.

**Mitigation:**
- Bronze must retain full history
- Archive old silver data periodically (partition pruning) if storage is constrained
- Document retention policy: "silver keeps X years; older data is archived"

### Gold cascades on dimension deletions

If a customer is deleted from silver, gold facts remain orphaned (orders without a valid customer).

**Solutions:**
1. Gold does periodic full reloads (`@ForceUpdate = 2`) to catch dimension deletions
2. Gold tolerates orphaned facts (LEFT JOINs, filter in reports)
3. Gold soft-deletes facts when dimension deleted (contradicts hard-delete philosophy; use solution 1 or 2)

### Change tracker sync

If a source table is updated but tracker is not, gold won't know about the change.

**Mitigation:**
- Update tracker immediately after loading source table (same pipeline step)
- Validate: tracker row counts match actual table row counts
- Monthly reconciliation: compare tracker against actual tables, fix mismatches

## F&O patterns

**GL deletions:** F&O rarely hard-deletes GL entries. More common: reversal transactions (post an offsetting entry). Treat as appends, not deletes.

**Sales orders:** Cancellations are status changes, not deletes. Check `SalesStatus` column before assuming hard delete.

**Customer/Vendor:** Inactive status is more common than deletion. Use status columns as soft indicators.

**Synapse Link:** Deletions on any entity trigger `SinkModifiedOn` update, so change tracker catches them.

## Safety guardrails

1. Bronze must retain full history (you depend on it for recovery)
2. Update change tracker immediately after each source load
3. Monthly validation: tracker counts vs. actual table counts
4. Document which entities have hard deletes vs. status changes
5. Plan gold reload frequency to handle dimension deletion cascades

## Related patterns

- [Full load (silver)](Full%20Load.md) — Simple truncate/reload fallback
- [Watermark management](../Cross-Cutting/Watermark%20Strategy.md) — How to store/advance gold watermarks based on change tracker
- [Schema drift](silver/schema-drift.md) — Handling schema changes alongside incremental loads

## Schema changes

New fields, type changes, enum redefinitions: trigger a full reload.

```sql
-- On schema change, full reload the table and reset change tracker
TRUNCATE TABLE silver.Customer;

INSERT INTO silver.Customer (...)
SELECT ... FROM bronze.Customer;

-- Reset change tracker for this table
DELETE FROM silver._ChangeTracker WHERE SourceTable = 'Customer';

-- Then repopulate tracker with current state
MERGE INTO silver._ChangeTracker t
USING (
  SELECT 
    'Customer' AS SourceTable,
    YEAR(SinkCreatedOn) * 100 + MONTH(SinkCreatedOn) AS SinkCreatedMonth,
    YEAR(SinkCreatedOn) * 10000 + MONTH(SinkCreatedOn) * 100 + DAY(SinkCreatedOn) AS SinkCreatedDay,
    MAX(SinkModifiedOn) AS MaxSinkModifiedOn,
    COUNT(*) AS RowCount
  FROM silver.Customer
  GROUP BY YEAR(SinkCreatedOn) * 100 + MONTH(SinkCreatedOn),
           YEAR(SinkCreatedOn) * 10000 + MONTH(SinkCreatedOn) * 100 + DAY(SinkCreatedOn)
) s
ON t.SourceTable = s.SourceTable AND t.SinkCreatedMonth = s.SinkCreatedMonth AND t.SinkCreatedDay = s.SinkCreatedDay
WHEN MATCHED THEN UPDATE SET MaxSinkModifiedOn = s.MaxSinkModifiedOn, RowCount = s.RowCount
WHEN NOT MATCHED THEN INSERT VALUES (s.SourceTable, s.SinkCreatedMonth, s.SinkCreatedDay, s.MaxSinkModifiedOn, s.RowCount, GETDATE());
```

Gold will see the reset change tracker and reload affected partitions on next run (`@ForceUpdate = 2` or partition reload of affected months).
