---
title: Fact open/settled rebuild
layer: gold
related:
  - Gold/Fact Patterns/Fact Partition Rebuild.md
  - Cross-Cutting/Delete Detection Strategies.md
---

Some transactions keep changing long after they were created. This pattern rebuilds every open row on each run and revisits settled rows when their change signal moves. It avoids using age alone to decide which records can be left untouched.

It suits a fact with a defined open/settled state and a stable key at its output grain. Inventory transactions, order lines, and customer or vendor settlement are candidates, but each needs an explicit definition of “settled.” Reopening and cancellation must be included in that definition.

## Select the rows that need reconsideration

Capture the keys currently marked open in gold. They need reconsideration even if they have just settled in silver and their timestamp falls behind the settled boundary.

The SQL Server-style excerpts below assume a conformed `InventTrans` with `IsSettled`, a stable `SinkCreatedMonth`, and one fact row per `(DataAreaId, RecId)`. `IsSettled` is a derived contract, not a claim that every F&O source exposes that column. Define it from the source's verified close or settlement fields before using this load.

```sql
SELECT
      fit.DataAreaId
     ,fit.SourceRecId
INTO #PreviouslyOpen
FROM gold.FactInventTrans AS fit
WHERE fit.IsSettled = 0;

SELECT @MaxSettledModifiedOn = MAX(fit.SinkModifiedOn)
FROM gold.FactInventTrans AS fit
WHERE fit.IsSettled = 1;
```

Build one incoming set containing current open rows, previously open rows still present in silver, and settled rows at or beyond the boundary. Including equality replays ties; a null boundary causes the initial load to consider all rows.

```sql
SELECT
      it.DataAreaId             AS [DataAreaId]
     ,it.RecId                  AS [SourceRecId]
     ,COALESCE(di.ItemKey, 0)   AS [ItemKey]
     ,it.CostAmountPosted       AS [Amount]
     ,it.IsSettled              AS [IsSettled]
     ,it.SinkCreatedMonth       AS [SinkCreatedMonth]
     ,it.SinkModifiedOn         AS [SinkModifiedOn]
INTO #Incoming
FROM silver.InventTrans AS it
LEFT JOIN #PreviouslyOpen AS po
    ON it.DataAreaId = po.DataAreaId
    AND it.RecId = po.SourceRecId
LEFT JOIN gold.DimItem AS di
    ON it.DataAreaId = di.DataAreaId
    AND it.ItemId = di.ItemId
WHERE it.IsSettled = 0
    OR po.SourceRecId IS NOT NULL
    OR @MaxSettledModifiedOn IS NULL
    OR it.SinkModifiedOn IS NULL
    OR it.SinkModifiedOn >= @MaxSettledModifiedOn;
```

The unknown item key `0` must exist. Each item lookup must return at most one member, and `#Incoming` must be unique at the fact grain. Materializing a set does not remove duplicates introduced by a join.

## Replace by key, then clear the old open set

Remove existing copies of the incoming keys. Then remove remaining open rows, including ones that have disappeared from silver and therefore could not enter `#Incoming`:

```sql
DELETE fit
FROM gold.FactInventTrans AS fit
INNER JOIN #Incoming AS inc
    ON fit.DataAreaId = inc.DataAreaId
    AND fit.SourceRecId = inc.SourceRecId;

DELETE fit
FROM gold.FactInventTrans AS fit
WHERE fit.IsSettled = 0;
```

Insert the materialized result:

```sql
INSERT INTO gold.FactInventTrans
(
      DataAreaId
     ,SourceRecId
     ,ItemKey
     ,Amount
     ,IsSettled
     ,SinkCreatedMonth
     ,SinkModifiedOn
)
SELECT
      inc.DataAreaId        AS [DataAreaId]
     ,inc.SourceRecId       AS [SourceRecId]
     ,inc.ItemKey           AS [ItemKey]
     ,inc.Amount            AS [Amount]
     ,inc.IsSettled         AS [IsSettled]
     ,inc.SinkCreatedMonth  AS [SinkCreatedMonth]
     ,inc.SinkModifiedOn    AS [SinkModifiedOn]
FROM #Incoming AS inc;
```

Commit the replacement as one operation and prevent concurrent runs from selecting incompatible states. These excerpts cover a whole-table load. A company-scoped version must apply the same company scope to every capture, boundary, deletion, and insertion.

## How transitions and deletions behave

An open row that settles is selected through its previously open key and reinserted with the new state. A settled row that reopens is selected through its current open state. Both transitions retain one current fact row.

An open row deleted from silver is removed by clearing the open set. A settled row deleted from silver is selected by neither path. It needs a deletion signal or reconciliation; this routine alone will leave that row in gold.

## Reconcile the settled side

Mode `0` runs the routine load above. Mode `1` performs [audit and repair](../Fact%20Audit%20and%20Repair.md) independently of that selection. Mode `2` rebuilds the complete scope. See the [shared contract](../../Cross-Cutting/ForceUpdate%20Contract.md).

A delayed settled row can still arrive behind the maximum timestamp, and mutable attributes on other tables can change without moving the transaction's signal. Reconciliation and explicit dependency handling remain necessary. Unknown keys also need revisiting after their dimension members arrive.

Measure the size of the open set. If transactions remain open for years, the load keeps rebuilding them; if most rows are open, a full load may be simpler. Finding changed settled rows can still require substantial source work, so the query's read cost does not automatically shrink to the number of changed rows.
