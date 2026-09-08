---
title: Full load
layer: silver
status: working
related:
  - Silver/Incremental with Hard Delete.md
  - Bronze/Full Load.md
---

## What this is

Truncate silver and reload entire table from bronze on every run. No change tracking, no assumptions about what changed.

## When to use it

- Table is small enough that full reload is faster than tracking changes
- After schema changes that require clean reload
- As periodic reconciliation (monthly/quarterly) on top of incremental
- Change tracking table has become unreliable

## How it works

```sql
TRUNCATE TABLE silver.Customer;

INSERT INTO silver.Customer (DataAreaId, CustomerId, CustomerName, CustomerGroup, SinkCreatedOn, SinkModifiedOn)
SELECT DataAreaId, CustomerId, CustomerName, CustomerGroup, SinkCreatedOn, SinkModifiedOn
FROM bronze.Customer;

-- Update change tracker after load
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

## When NOT to use it

- Table is large and load time exceeds SLA
- You need to track deletions incrementally (use hard-delete incremental instead)
