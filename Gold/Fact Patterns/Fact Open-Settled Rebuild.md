---
title: Fact open/settled rebuild
layer: gold
related:
  - Gold/Fact Patterns/Fact Partition Rebuild.md
  - Cross-Cutting/Delete Detection Strategies.md
---

An inventory transaction can keep changing while it is open, even if it was created years ago. Once settled, it usually needs less attention. This pattern reloads the open transactions every run and picks up settled ones when their timestamps change.

The example writes `fact.InventoryTransactions`, with one row per source company and record. The procedure prepares `#InventoryState` from `d365fo.inventtrans`, keeping source names and adding `IsSettled` and the stable `SinkCreatedMonth`. The source-specific settlement rule is outside this walkthrough.

## Which transactions need another look?

Find the latest timestamp already loaded for settled transactions:

```sql
SELECT @MaxSettledModifiedOn = MAX(itr.SinkModifiedOn)
FROM fact.InventoryTransactions AS itr
WHERE itr.IsSettled = 1;
```

Then gather transactions that are open now, were open in the fact, or have a newer timestamp. Checking the existing fact catches transactions that have just settled. The item lookup supplies the primary key we'll write as `FKItem`.

```sql
SELECT
      inv.dataareaid
     ,inv.recid
     ,inv.itemid
     ,inv.costamountposted
     ,inv.IsSettled
     ,inv.SinkCreatedMonth
     ,inv.SinkModifiedOn
     ,itm.PKItem
INTO #Incoming
FROM #InventoryState AS inv
LEFT JOIN fact.InventoryTransactions AS itr
    ON inv.dataareaid = itr.DataAreaId
    AND inv.recid = itr.SourceRecId
LEFT JOIN dim.Item AS itm
    ON inv.dataareaid = itm.dataareaid
    AND inv.itemid = itm.itemid
WHERE inv.IsSettled = 0
    OR itr.IsSettled = 0
    OR @MaxSettledModifiedOn IS NULL
    OR inv.SinkModifiedOn IS NULL
    OR inv.SinkModifiedOn >= @MaxSettledModifiedOn;
```

`#Incoming` is kept because the same rows drive the delete and insert. A missing item leaves `FKItem` null; it doesn't remove the transaction.

## Replace those transactions

Remove the old copy of each incoming transaction. Then clear any open rows left behind, including rows that disappeared from the source:

```sql
DELETE itr
FROM fact.InventoryTransactions AS itr
INNER JOIN #Incoming AS inc
    ON itr.DataAreaId = inc.dataareaid
    AND itr.SourceRecId = inc.recid;

DELETE itr
FROM fact.InventoryTransactions AS itr
WHERE itr.IsSettled = 0;
```

Insert the prepared rows:

```sql
INSERT INTO fact.InventoryTransactions
(
      DataAreaId
     ,SourceRecId
     ,FKItem
     ,Item
     ,Amount
     ,IsSettled
     ,SinkCreatedMonth
     ,SinkModifiedOn
)
SELECT
      inc.dataareaid        AS [DataAreaId]
     ,inc.recid             AS [SourceRecId]
     ,inc.PKItem            AS [FKItem]
     ,inc.itemid            AS [Item]
     ,inc.costamountposted  AS [Amount]
     ,inc.IsSettled         AS [IsSettled]
     ,inc.SinkCreatedMonth  AS [SinkCreatedMonth]
     ,inc.SinkModifiedOn    AS [SinkModifiedOn]
FROM #Incoming AS inc;
```

The replacement carries the current `IsSettled` value, so a transaction can settle or reopen without a separate update path.

This is mode `0`. Mode `1` uses [audit and repair](../Fact%20Audit%20and%20Repair.md), and mode `2` rebuilds the whole fact. These SQL Server/Azure SQL excerpts cover all companies.

## Not covered

- **Settlement and partition rules:** prepare these in the procedure using verified source behavior; this article does not define the contents of `#InventoryState` for a specific F&O configuration.
- **Deleted or late settled rows:** they may escape this selection and need a deletion signal or reconciliation.
- **Missing or duplicate matches:** verify one fact row per company/record and one item match; revisit null `FKItem` values when items arrive.
- **Atomic replacement and retries:** coordinate the two deletes and insert when readers must see a complete result.
- **Large open sets and changing lookups:** measure repeated work and account for changes outside the transaction's own timestamp.
