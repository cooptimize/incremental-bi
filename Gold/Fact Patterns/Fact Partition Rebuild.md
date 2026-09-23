---
title: Fact partition rebuild
layer: gold
related:
  - Cross-Cutting/Partition Keys.md
  - Silver/Change Tracking Partitions.md
  - Gold/Fact Patterns/Fact Open-Settled Rebuild.md
---

A ledger fact may contain years of transactions while only a few months need rebuilding. This pattern finds those months, prepares their current rows, and replaces them. Transactions removed from the source disappear when their month is replaced.

It works best when existing transaction values are stable and most changes are arrivals or removals. The example uses a stored extraction month, `SinkCreatedMonth`, as the replacement boundary.

## What changed since the last load?

The [source tracker](../../Silver/Change%20Tracking%20Partitions.md) supplies each month's count and latest timestamp. `control.FactLoadState` stores the same values from the last successful load, identified by `FactTable` and `SinkCreatedMonth`.

Capture the source values now so we can record exactly what this run used:

```sql
SELECT
      ctr.SinkCreatedMonth
     ,MAX(ctr.MaxSinkModifiedOn) AS [MaxSinkModifiedOn]
     ,SUM(ctr.[RowCount])        AS [RowCount]
INTO #SourceState
FROM silver._ChangeTracker AS ctr
WHERE ctr.SourceTable = 'GeneralJournalAccountEntry'
GROUP BY ctr.SinkCreatedMonth;
```

## Which months need replacing?

Compare with the saved state for `fact.GeneralLedger`. Include months from both sides so a month that disappeared from the source still gets removed from the fact:

```sql
WITH
     LoadedState AS
     (
         SELECT
               fls.SinkCreatedMonth
              ,fls.MaxSinkModifiedOn
              ,fls.[RowCount]
         FROM control.FactLoadState AS fls
         WHERE fls.FactTable = 'fact.GeneralLedger'
     )
    ,ComparedPartitions AS
     (
         SELECT ss.SinkCreatedMonth
         FROM #SourceState AS ss
         UNION
         SELECT ls.SinkCreatedMonth
         FROM LoadedState AS ls
     )
SELECT cp.SinkCreatedMonth AS [SinkCreatedMonth]
INTO #PartitionState
FROM ComparedPartitions AS cp
LEFT JOIN #SourceState AS ss
    ON cp.SinkCreatedMonth = ss.SinkCreatedMonth
LEFT JOIN LoadedState AS ls
    ON cp.SinkCreatedMonth = ls.SinkCreatedMonth
WHERE @ForceUpdate = 2
    OR ss.SinkCreatedMonth IS NULL
    OR ls.SinkCreatedMonth IS NULL
    OR ss.MaxSinkModifiedOn IS NULL
    OR ls.MaxSinkModifiedOn IS NULL
    OR ss.MaxSinkModifiedOn <> ls.MaxSinkModifiedOn
    OR ss.[RowCount] <> ls.[RowCount];
```

Mode `0` uses that comparison. Mode `2` selects every known month. Mode `1` instead uses [audit and repair](../Fact%20Audit%20and%20Repair.md) to compare the actual result.

## Prepare the replacement rows

Gather the selected transactions before removing their old copies. The source is assumed to supply a stable `SinkCreatedMonth`:

```sql
SELECT
      gjae.recid
     ,gjae.accountingcurrencyamount
     ,gjae.SinkCreatedMonth
     ,gjae.SinkModifiedOn
INTO #FinalLedger
FROM d365fo.generaljournalaccountentry AS gjae
INNER JOIN #PartitionState AS ps
    ON gjae.SinkCreatedMonth = ps.SinkCreatedMonth;
```

Replace those months with the prepared rows. An empty source month leaves no rows to reinsert:

```sql
DELETE gl
FROM fact.GeneralLedger AS gl
INNER JOIN #PartitionState AS ps
    ON gl.SinkCreatedMonth = ps.SinkCreatedMonth;

INSERT INTO fact.GeneralLedger
(
      SourceRecId
     ,Amount
     ,SinkCreatedMonth
     ,SinkModifiedOn
)
SELECT
      fl.recid                      AS [SourceRecId]
     ,fl.accountingcurrencyamount   AS [Amount]
     ,fl.SinkCreatedMonth           AS [SinkCreatedMonth]
     ,fl.SinkModifiedOn             AS [SinkModifiedOn]
FROM #FinalLedger AS fl;
```

Save the captured `#SourceState` values for the replaced months and remove state for vanished months. Commit those changes with the fact replacement so the next run knows what was loaded.

## Not covered

- **Missed changes:** offsetting inserts and deletes or unchanged maximum timestamps still need reconciliation.
- **Changed joined tables:** map their changes to the affected fact months; a source table's extraction month may be different.
- **Reinitialization and large partitions:** see [partition keys](../../Cross-Cutting/Partition%20Keys.md) for stability and distribution requirements.
- **Setup and recovery:** these SQL Server/Azure SQL excerpts omit control-table creation, state-writing SQL, mode validation, transaction handling, and retries.
- **Lost control state:** a full recovery must also include months present in the fact but missing from the control table.
