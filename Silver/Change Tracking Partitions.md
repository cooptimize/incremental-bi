---
title: Change tracking partitions
layer: silver
status: working
related:
  - Silver/Incremental with Hard Delete.md
  - Silver/Full Load.md
  - Cross-Cutting/Partition Keys.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

A partition tracker summarizes silver so gold can find likely changes without rescanning every source table. It records the maximum modification timestamp and row count for each source partition; gold keeps its own copy of the state it last loaded.

The maximum identifies many arrivals and updates. The count identifies many removals. Neither is a complete record of changes, so the tracker selects routine work while reconciliation checks the result.

## Store one row per source partition

This SQL Server-style example tracks months. Choose days instead when gold needs daily replacement, or roll daily state up explicitly when a consumer needs months:

```sql
CREATE TABLE silver._ChangeTracker
(
      SourceTable NVARCHAR(255) NOT NULL
     ,SinkCreatedMonth INT NOT NULL
     ,MaxSinkModifiedOn DATETIME2(7) NULL
     ,[RowCount] BIGINT NOT NULL
     ,LastUpdatedDateTime DATETIME2(7) NOT NULL
     ,PRIMARY KEY (SourceTable, SinkCreatedMonth)
);
```

`SinkCreatedMonth` must follow the [stable partition-key contract](../Cross-Cutting/Partition%20Keys.md). The example covers the whole source table across companies. A company-specific tracker needs that scope in both its key and every consumer's comparison.

## Publish state after the source load

For a simple implementation, replace this table's tracker rows from the completed silver state. The following excerpt assumes `SinkCreatedMonth` is already stored on the conformed transaction table:

```sql
DELETE ctr
FROM silver._ChangeTracker AS ctr
WHERE ctr.SourceTable = 'GeneralJournalAccountEntry';

INSERT INTO silver._ChangeTracker
(
      SourceTable
     ,SinkCreatedMonth
     ,MaxSinkModifiedOn
     ,[RowCount]
     ,LastUpdatedDateTime
)
SELECT
      'GeneralJournalAccountEntry'  AS [SourceTable]
     ,gjae.SinkCreatedMonth         AS [SinkCreatedMonth]
     ,MAX(gjae.SinkModifiedOn)      AS [MaxSinkModifiedOn]
     ,COUNT_BIG(*)                  AS [RowCount]
     ,SYSUTCDATETIME()              AS [LastUpdatedDateTime]
FROM silver.GeneralJournalAccountEntry AS gjae
GROUP BY gjae.SinkCreatedMonth;
```

Publish the delete and insert with the silver load as one consistent operation. Gold must not observe the tracker between those statements. This baseline scans the source once to summarize it; an optimized affected-partition update needs the old partition membership of deleted or moved rows too.

Replacing the summary removes partitions that are now empty. Gold still has those partitions in its loaded-state table and can therefore discover their removal. A merge that only updates and inserts tracker rows would leave stale entries for empty partitions.

## Compare against what gold loaded

Gold compares current tracker state with `gold._FactLoadState`, rather than asking only for timestamps newer than one global watermark. It needs to consider changed counts, new partitions, and partitions present only in loaded state. See [fact partition rebuild](../Gold/Fact%20Patterns/Fact%20Partition%20Rebuild.md) for the work list.

Don't advance gold's state until the corresponding replacement succeeds. Recording a fresh tracker value against an old fact would hide the remaining work from the next run.

## Know what the summary misses

A removed row can be offset by an inserted row, leaving the count unchanged. An update can also leave the partition maximum unchanged. Both can pass the routine comparison, which is why [audit and repair](../Gold/Fact%20Audit%20and%20Repair.md) remains separate.

A changed source partition also isn't automatically a changed fact partition. Two tables can have different extraction cohorts even when their rows join. The load must translate changes through the relationship, or use a pattern that selects affected keys directly.

Retain tracker coverage for data that gold still serves. Verify tracker totals against silver after recovery or manual changes, and coordinate related table publication so gold does not combine incompatible source states.
