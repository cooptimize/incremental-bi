---
title: Fact audit and repair
layer: gold
related:
  - Gold/Fact Patterns/Fact Partition Rebuild.md
  - Gold/Fact Patterns/Fact Open-Settled Rebuild.md
---

A successful load can still miss or duplicate transactions. To check it, compare the fact with the source by month, then rebuild the months that disagree.

## Compare the same result on both sides

Count rows and sum the amount in `fact.InventoryTransactions`:

```sql
SELECT
      itr.SinkCreatedMonth          AS [SinkCreatedMonth]
     ,COUNT_BIG(*)                  AS [RowCount]
     ,COALESCE(SUM(itr.Amount), 0)  AS [Amount]
INTO #GoldState
FROM fact.InventoryTransactions AS itr
GROUP BY itr.SinkCreatedMonth;
```

Compare that with `#InventoryState`, the source rows prepared by the [open/settled load](Fact%20Patterns/Fact%20Open-Settled%20Rebuild.md):

```sql
SELECT
      inv.SinkCreatedMonth                      AS [SinkCreatedMonth]
     ,COUNT_BIG(*)                              AS [RowCount]
     ,COALESCE(SUM(inv.costamountposted), 0)    AS [Amount]
INTO #SourceState
FROM #InventoryState AS inv
GROUP BY inv.SinkCreatedMonth;
```

The example expects one fact row per source transaction, with `costamountposted` loaded as `Amount`. Checking the source before dimension joins lets us catch rows those joins dropped or multiplied.

## Find the months that disagree

The combined month list matters: checking only source months would miss an old month that should now be empty in the fact.

```sql
WITH
     ComparedPartitions AS
     (
         SELECT gs.SinkCreatedMonth
         FROM #GoldState AS gs
         UNION
         SELECT ss.SinkCreatedMonth
         FROM #SourceState AS ss
     )
SELECT cp.SinkCreatedMonth AS [SinkCreatedMonth]
INTO #Discrepant
FROM ComparedPartitions AS cp
LEFT JOIN #GoldState AS gs
    ON cp.SinkCreatedMonth = gs.SinkCreatedMonth
LEFT JOIN #SourceState AS ss
    ON cp.SinkCreatedMonth = ss.SinkCreatedMonth
WHERE gs.SinkCreatedMonth IS NULL
    OR ss.SinkCreatedMonth IS NULL
    OR gs.[RowCount] <> ss.[RowCount]
    OR gs.Amount <> ss.Amount;
```

Record the differences, replace those months from the prepared source, and check again. A repeated difference points to a problem the reload itself cannot fix.

This is `@ForceUpdate = 1` for facts. It does not depend on the timestamps used to select the routine incremental work.

## Not covered

- **Equal totals with different contents:** counts and sums can conceal offsetting errors; compare keys or attributes when needed.
- **Aggregated facts and rounding:** compare the expected output grain and use a defined tolerance for measures.
- **Unresolved dimension references:** null `FKItem` values retain transactions without placeholder rows, but need a separate check and later key resolution.
- **Upstream gaps:** the fact and its input can agree while both miss a source change.
- **Repair orchestration:** transaction handling, retries, and retained discrepancy logs are outside these SQL Server/Azure SQL comparison excerpts.
