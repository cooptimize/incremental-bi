---
title: Delete detection strategies
layer: cross-cutting
status: working
related:
  - Cross-Cutting/Watermark Strategy.md
  - Gold/Dimension Patterns/Dimension Incremental Load.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

## The problem

You cannot detect deletions by comparing record counts or doing full outer joins on large tables. You need a deletion signal from the source.

## Strategies

### 1. Soft delete flag (best case)

Source has `IsDeleted`, `DeletedOn`, or `Status = 'Deleted'`.

**For dimensions:** Can hard-delete when `IsDeleted = 1`
```sql
WHEN NOT MATCHED BY SOURCE OR src.IsDeleted = 1
THEN DELETE
```

**For facts:** Soft-delete only (mark IsDeleted = 1, never hard-delete)
```sql
WHEN MATCHED AND src.IsDeleted = 1
THEN UPDATE SET IsDeleted = 1, DeletedAt = GETDATE()
```

### 2. Audit table or status column

Source has separate deletion log (F&O audit, CDC tables) or change history. Query the log after your watermark, soft-delete matching rows.

```sql
WITH DeletedCustomers AS (
  SELECT customer_id FROM dbo._AuditLog
  WHERE operation = 'DELETE' AND deleted_at > @watermark
)
UPDATE gold.DimCustomer
SET IsDeleted = 1, DeletedAt = GETDATE()
WHERE CustomerID IN (SELECT customer_id FROM DeletedCustomers)
```

### 3. Periodic full reconciliation (fallback)

Source provides no deletion signal. Monthly/quarterly, do a full outer join on natural key to find missing rows.

```sql
WITH DeletedRows AS (
  SELECT tgt.CustomerKey FROM gold.DimCustomer tgt
  LEFT OUTER JOIN silver.Customer src
    ON tgt.CustomerID = src.CustomerID
    AND tgt.DataAreaId = src.DataAreaId
  WHERE src.CustomerID IS NULL
)
UPDATE gold.DimCustomer
SET IsDeleted = 1, DeletedAt = GETDATE()
WHERE CustomerKey IN (SELECT CustomerKey FROM DeletedRows)
```

**Cost:** High (full outer join), run monthly off-hours.

## Dimension vs. fact deletion

**Dimensions:** Can hard-delete if natural key is immutable and won't collide. Safer: soft-delete (IsDeleted = 1), filter in semantic model.

**Facts:** NEVER hard-delete. Always soft-delete. Reasons:
- Breaks reconciliation (historical totals change)
- Loses audit trail
- Silent data loss

## SinkModifiedOn does NOT tell you about deletions

A row with stale `SinkModifiedOn` is not necessarily deleted. Use `SinkModifiedOn > watermark` to catch *updates* (including status changes), not to infer deletion.

**If deletion is a status change:** Include the status column in your WHERE clause:
```sql
WHERE SinkModifiedOn > @watermark OR CustStatus = 'Deleted'
```

## F&O patterns

**GL deletions:** Look for `IsDeleted = 1` flag first, else check `SysTraceTableViewLog` for audit.

**Sales/invoice deletions:** Consume `DocumentStatus` (Deleted, Voided). Soft-delete facts when status = 'Deleted'.

**Natural key reuse:** Use `DataAreaId + business_key`, never just business key alone.

## Safety guardrails

1. Dimensions: soft-delete first, hard-delete after 30+ days (if at all)
2. Facts: only soft-delete, never hard-delete
3. Reconciliation: mandatory monthly for unknown deletion signals
4. Testing: verify soft-deleted rows still join in semantic model
