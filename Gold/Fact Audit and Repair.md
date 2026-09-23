---
title: Fact audit and repair
layer: gold
related:
  - Gold/Fact Patterns/Fact Partition Rebuild.md
  - Gold/Fact Patterns/Fact Open-Settled Rebuild.md
---

Fact reconciliation compares the loaded result with what silver says should be there. It runs independently of the normal change signal, so it can find an omission even when the incremental job succeeded and advanced its state.

A common example is a transaction dropped by a join before its dimension member existed. Rebuilding only rows with newer timestamps may never revisit it. A comparison of expected and loaded rows gives the repair process another way to find the gap.

## Compare at the same grain

Start with counts and additive measures by partition. The source calculation must use the fact's intended filters and grain without repeating the faulty join you are trying to detect. The example assumes one fact row per eligible `InventTrans` row, with `Amount` representing `CostAmountPosted`.

Materialize the two small summaries. These are SQL Server-style examples over conformed tables:

```sql
SELECT
      fit.SinkCreatedMonth          AS [SinkCreatedMonth]
     ,COUNT_BIG(*)                  AS [RowCount]
     ,COALESCE(SUM(fit.Amount), 0)  AS [Amount]
INTO #GoldState
FROM gold.FactInventTrans AS fit
GROUP BY fit.SinkCreatedMonth;
```

```sql
SELECT
      it.SinkCreatedMonth                   AS [SinkCreatedMonth]
     ,COUNT_BIG(*)                          AS [RowCount]
     ,COALESCE(SUM(it.CostAmountPosted), 0) AS [Amount]
INTO #SourceState
FROM silver.InventTrans AS it
GROUP BY it.SinkCreatedMonth;
```

For an aggregate fact, count the expected output groups rather than comparing raw source rows with aggregated rows. Use compatible numeric types and define any required rounding tolerance for measures.

## Find the differences

Build the partition list from both sides so an entirely missing or extra partition is included:

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

Equal counts and sums are useful evidence, not proof of row-level equality. Different keys can have the same count and amount, and offsetting value errors can cancel out. Add comparisons for attributes or keys whose correctness matters to the report.

## Repair and record the result

Log the discrepant partitions, counts, and measure differences before replacing them. Rebuild those partitions from a consistent source state, then repeat the check. If the same difference remains, investigate the transformation rather than scheduling the same ineffective repair indefinitely.

This is `@ForceUpdate = 1` for facts. It can use partition replacement even when the routine [open/settled load](Fact%20Patterns/Fact%20Open-Settled%20Rebuild.md) selects rows by key, provided the fact carries the stable partition key needed by the repair.

Unknown dimension members help preserve transaction counts when a lookup is late. They don't prove the lookup is correct, so track unresolved keys separately and reconsider them during repair.

## Know the comparison's boundary

If silver and gold both missed the same source deletion, they can agree while both are wrong. Reconcile silver with its own input too; rebuilding gold from unchanged silver will not fix that gap.

Large or collapsed partitions make repair expensive even when detection is cheap. Keep the discrepancy log so you can measure how often repairs occur, how much data they replace, and whether a different routine load would cost less.
