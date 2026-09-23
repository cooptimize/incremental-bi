---
title: Full load
layer: silver
status: working
related:
  - Silver/Incremental with Hard Delete.md
  - Silver/Change Tracking Partitions.md
  - Bronze/Full Load.md
---

A full silver load replaces the conformed table from a completed bronze input. It is useful for small tables, initial loads, and schema changes that require every row to be transformed again.

The load does not need a delta to decide which silver rows to replace. If gold consumes a change tracker, silver must still publish tracker state after the replacement.

## Replace the table and its state together

This SQL Server-style excerpt assumes bronze exposes the complete current customer population and silver preserves the listed source fields. Apply any required typing and deduplication before publishing that population:

```sql
TRUNCATE TABLE silver.CustTable;

INSERT INTO silver.CustTable
(
      DataAreaId
     ,AccountNum
     ,CustGroup
     ,RecId
     ,Party
     ,SinkCreatedOn
     ,SinkModifiedOn
)
SELECT
      ct.DataAreaId     AS [DataAreaId]
     ,ct.AccountNum     AS [AccountNum]
     ,ct.CustGroup      AS [CustGroup]
     ,ct.RecId          AS [RecId]
     ,ct.Party          AS [Party]
     ,ct.SinkCreatedOn  AS [SinkCreatedOn]
     ,ct.SinkModifiedOn AS [SinkModifiedOn]
FROM bronze.CustTable AS ct;
```

The excerpt shows the replacement, not a complete production procedure. Use a transaction where supported or publish a completed staging table so readers cannot see an empty or partially loaded target. A company-scoped load must replace only that company; truncation applies to the whole table.

After loading, refresh the table's [partition tracker](Change%20Tracking%20Partitions.md). Publish the data and tracker as one consistent state. Remove obsolete tracker partitions as well as updating surviving ones, while retaining gold's previously loaded state so it can discover vanished partitions.

## A rebuild can change more than the rows

A changed schema or transformation may alter values without changing source timestamps or counts. Rebuilding silver alone does not guarantee that gold will select those rows again. Coordinate a downstream reconciliation or rebuild for affected targets.

If the load assigns partition keys, preserve their stability or deliberately reset the downstream partition state. Re-deriving an extraction cohort from rewritten source metadata can move rows between partitions. See [partition keys](../Cross-Cutting/Partition%20Keys.md).

Use [incremental with hard delete](Incremental%20with%20Hard%20Delete.md) when a complete replacement no longer fits the window and bronze provides enough information to maintain current state reliably.
