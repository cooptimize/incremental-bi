---
title: Fact partition rebuild
layer: gold
related:
  - Cross-Cutting/Partition Keys.md
  - Silver/Change Tracking Partitions.md
  - Gold/Fact Patterns/Fact Open-Settled Rebuild.md
---

A partition rebuild replaces a complete slice of a fact whenever its source state changes. Replacing the slice also removes transactions that have disappeared from silver, without requiring a separate list of their deleted keys.

This pattern is intended for facts whose transaction values are stable after creation, with later arrivals and removals still possible. It compares partition counts and maximum timestamps; it is not a complete detector of arbitrary updates. Use [open/settled rebuild](Fact%20Open-Settled%20Rebuild.md) when continuing changes are part of the transaction lifecycle.

## Compare current and previously loaded state

Silver publishes the current summary in its [change tracker](../../Silver/Change%20Tracking%20Partitions.md). Gold records the summary it used after successfully replacing each partition:

```sql
CREATE TABLE gold._FactLoadState
(
      FactTable NVARCHAR(128) NOT NULL
     ,SinkCreatedMonth INT NOT NULL
     ,MaxSinkModifiedOn DATETIME2(7) NULL
     ,[RowCount] BIGINT NOT NULL
     ,PRIMARY KEY (FactTable, SinkCreatedMonth)
);
```

These are source counts, not counts of the fact. The source and fact may have different grains or filters. Comparing their actual results is the separate job of [audit and repair](../Fact%20Audit%20and%20Repair.md).

The following SQL Server-style excerpts cover one whole-table fact load. Capture the completed silver state and gold's last loaded state before selecting work:

```sql
SELECT
      ctr.SinkCreatedMonth
     ,MAX(ctr.MaxSinkModifiedOn)    AS [MaxSinkModifiedOn]
     ,SUM(ctr.[RowCount])           AS [RowCount]
INTO #SourceState
FROM silver._ChangeTracker AS ctr
WHERE ctr.SourceTable = 'GeneralJournalAccountEntry'
GROUP BY ctr.SinkCreatedMonth;

SELECT
      fls.SinkCreatedMonth
     ,fls.MaxSinkModifiedOn
     ,fls.[RowCount]
INTO #LoadedState
FROM gold._FactLoadState AS fls
WHERE fls.FactTable = 'FactGeneralLedger';
```

The rollup also works if the tracker holds daily entries within each month. It must contain one consistent granularity, not overlapping monthly and daily totals.

## Build one replacement list

Include partitions from both states. A new source partition needs inserting; a partition that has vanished from silver needs removing from gold. For a partition present on both sides, a changed maximum or count triggers replacement. A missing timestamp is treated conservatively as work to repeat.

```sql
WITH
     ComparedPartitions AS
     (
         SELECT ss.SinkCreatedMonth
         FROM #SourceState AS ss
         UNION
         SELECT ls.SinkCreatedMonth
         FROM #LoadedState AS ls
     )
SELECT cp.SinkCreatedMonth AS [SinkCreatedMonth]
INTO #PartitionState
FROM ComparedPartitions AS cp
LEFT JOIN #SourceState AS ss
    ON cp.SinkCreatedMonth = ss.SinkCreatedMonth
LEFT JOIN #LoadedState AS ls
    ON cp.SinkCreatedMonth = ls.SinkCreatedMonth
WHERE @ForceUpdate = 2
    OR ss.SinkCreatedMonth IS NULL
    OR ls.SinkCreatedMonth IS NULL
    OR ss.MaxSinkModifiedOn IS NULL
    OR ls.MaxSinkModifiedOn IS NULL
    OR ss.MaxSinkModifiedOn <> ls.MaxSinkModifiedOn
    OR ss.[RowCount] <> ls.[RowCount];
```

Validate `@ForceUpdate` before this step. Mode `0` uses the comparison above; mode `2` selects every known partition. Mode `1` uses the audit comparison instead, because a successful earlier load may still have produced the wrong result.

## Replace the selected partitions

Use the same list for deletion and insertion. If a selected partition is now empty in silver, the insert naturally returns no rows for it:

```sql
DELETE fgl
FROM gold.FactGeneralLedger AS fgl
INNER JOIN #PartitionState AS ps
    ON fgl.SinkCreatedMonth = ps.SinkCreatedMonth;
```

The insert below is a minimal projection to show the replacement boundary. It assumes conformed silver fields, including company and the stored cohort; a production fact adds its business attributes and dimension lookups at the intended grain.

```sql
INSERT INTO gold.FactGeneralLedger
(
      DataAreaId
     ,SourceRecId
     ,Amount
     ,SinkCreatedMonth
     ,SinkModifiedOn
)
SELECT
      gjae.DataAreaId               AS [DataAreaId]
     ,gjae.RecId                    AS [SourceRecId]
     ,gjae.AccountingCurrencyAmount AS [Amount]
     ,gjae.SinkCreatedMonth         AS [SinkCreatedMonth]
     ,gjae.SinkModifiedOn           AS [SinkModifiedOn]
FROM silver.GeneralJournalAccountEntry AS gjae
INNER JOIN #PartitionState AS ps
    ON gjae.SinkCreatedMonth = ps.SinkCreatedMonth;
```

After success, replace the loaded-state entries for the selected partitions with the captured `#SourceState` values. Remove entries for vanished partitions. Commit fact data and loaded state together; don't record state from a newer silver version than the one actually used to build the fact.

This is the load body, not a complete transaction wrapper. Coordinate source publication, concurrent loads, and reader access before using it in production. A mode `2` recovery also needs to include partitions present in the fact if its loaded-state table has been lost or corrupted.

## Limits of the partition signal

Counts can remain unchanged when an insertion offsets a deletion. An update can also leave the maximum timestamp unchanged. Reconciliation must check the output independently of these two summary values.

Changes in joined tables require a mapping to the affected driver partitions. A changed customer attribute cannot be found by monitoring ledger rows alone, and the customer's extraction month is not necessarily the month of its transactions. Keep mutable descriptive attributes in dimensions where appropriate, or explicitly track those dependencies.

The [partition key](../../Cross-Cutting/Partition%20Keys.md) must remain stable or moves must be handled on both sides. Re-extraction can also concentrate history into a large cohort, making every replacement expensive. Daily keys don't help if all rows were extracted on the same day; measure the distribution before relying on small rebuilds.
