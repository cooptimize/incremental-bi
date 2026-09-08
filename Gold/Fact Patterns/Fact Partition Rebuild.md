---
title: Fact partition rebuild
layer: gold
status: working
related:
  - Cross-Cutting/Partition Keys.md
  - Silver/Change Tracking Partitions.md
  - Gold/Fact Patterns/Fact Open-Settled Rebuild.md
---

For facts whose rows are inserted and deleted but never updated. Delete whole partitions, reload them from silver. The partition is an extraction month (`SinkCreatedMonth`).

## Use case

Posted transactions. A posted GL entry isn't edited in normal operation — corrections write new entries, and an opening-balance cleanup removes rows. Both show up at partition level as rows arriving and rows disappearing, which is all this pattern can see and all it needs.

The test: **do an existing fact row's values change?** If yes, this pattern is wrong for that table — use [open/settled rebuild](Fact%20Open-Settled%20Rebuild.md). An update that leaves the row count alone **could be** missed with this approach.

## What the source looks like now

Roll up the change tracker. It is keyed by table, month and day, so the day rows collapse into the month:

```sql
SELECT SinkCreatedMonth,
       MAX(MaxSinkModifiedOn) AS MaxSinkModifiedOn,
       SUM(RowCount)          AS RowCount
FROM silver._ChangeTracker
WHERE SourceTable = 'GeneralJournalAccountEntry'
GROUP BY SinkCreatedMonth;
```

## What each partition was built from

Not an aggregate of the fact table — a small metadata table the load writes at the end of every run, holding the tracker values each partition was built from:

```sql
CREATE TABLE gold._FactLoadState (
    FactTable         NVARCHAR(128),
    SinkCreatedMonth  INT,
    MaxSinkModifiedOn DATETIME,
    RowCount          INT,
    PRIMARY KEY (FactTable, SinkCreatedMonth)
);
```

Recording state instead of aggregating the fact avoids a full scan of gold on every run, and avoids false positives when the fact legitimately holds fewer rows than the source — company filters, excluded transaction types, inner joins that drop rows.

## Building the work list

Filter to the partitions in play, and what to do with each falls out of which side it exists on: only in the source means insert, only in gold means delete, both means delete and reinsert.

```sql
SELECT COALESCE(s.SinkCreatedMonth, l.SinkCreatedMonth) AS SinkCreatedMonth,
       CASE WHEN l.SinkCreatedMonth IS NOT NULL THEN 1 ELSE 0 END AS ToDelete,
       CASE WHEN s.SinkCreatedMonth IS NOT NULL THEN 1 ELSE 0 END AS ToInsert
INTO #PartitionState
FROM SourceState s
FULL OUTER JOIN LoadedState l ON l.SinkCreatedMonth = s.SinkCreatedMonth
WHERE @ForceUpdate = 2
   OR l.SinkCreatedMonth IS NULL
   OR s.SinkCreatedMonth IS NULL
   OR s.MaxSinkModifiedOn > l.MaxSinkModifiedOn
```

`SourceState` and `LoadedState` are the two queries above as CTEs. A temp table rather than a third CTE, because the same list drives two statements.

## The load

Drop the flagged partitions:

```sql
DELETE f
FROM gold.FactGeneralLedger f
JOIN #PartitionState p ON p.SinkCreatedMonth = f.SinkCreatedMonth
WHERE p.ToDelete = 1;
```

Reload them:

```sql
INSERT INTO gold.FactGeneralLedger (AccountKey, ..., SinkCreatedMonth, SinkModifiedOn)
SELECT da.AccountKey, ..., je.SinkCreatedMonth, je.SinkModifiedOn
FROM silver.GeneralJournalAccountEntry je
JOIN #PartitionState p ON p.SinkCreatedMonth = je.SinkCreatedMonth AND p.ToInsert = 1
JOIN gold.DimAccount da ON da.DataAreaId = je.DataAreaId AND da.MainAccountId = je.MainAccountId;
```

Index the fact on `SinkCreatedMonth`, and update `gold._FactLoadState` for every reloaded partition before the procedure ends.

## @ForceUpdate

Levels of trust in the change signal. `0` is the query above — trust the tracker. `1` doesn't: it compares gold to silver by partition and rebuilds what disagrees, which is the only way to catch a row that was offered and silently dropped. See [audit and repair](../Fact%20Audit%20and%20Repair.md). `2` trusts nothing and flags every partition both ways.

## Fatal flaws

- **Denormalized attributes from mutable tables.** An invoice fact carrying a customer group goes stale the moment `CustTable` changes. No GL row moved, so no partition is flagged, and nothing in this pattern can see it. There is no deterministic fix at load time: either keep mutable attributes in a dimension the fact points at, or accept that only reconciliation catches the drift. Decide this when the fact is designed, not when it breaks.
- **Repointing a table collapses the partitioning.** An initial load, a Synapse Link re-init, or moving a table to a new link re-extracts every row with today's `SinkCreatedOn`. Two things happen: every watermark is rewritten, so every partition looks changed once; and the whole table now sits in one partition, so from then on any change to any row reloads all of it. The first is a one-off, the second is permanent. `SinkCreatedDay` doesn't help — the collapse is into a single day as well. Either accept it for that table, or derive the partition key in silver from a field that survives re-extraction (`CreatedDateTime` where the table has it, or a `RecId` bucket). Reset `_FactLoadState` deliberately rather than discovering it at runtime.
- **Partition skew generally.** Partitions are only uniform if extraction was. An oversized one costs a full reload of itself every time it moves.
