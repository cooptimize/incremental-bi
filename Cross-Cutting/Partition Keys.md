---
title: Partition keys
layer: cross-cutting
related:
  - Silver/Change Tracking Partitions.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

A stored partition key gives silver, its change tracker, and gold a shared unit of replacement. When gold rebuilds a month, the key identifies exactly which rows belong to that month without deriving the boundary differently in each query.

The patterns here use `SinkCreatedMonth` for extraction cohorts: rows grouped by their extraction timestamp. A cohort is a loading boundary; reports can still use posting or transaction dates for business analysis.

## Derive the key in silver

These expressions show the monthly and daily forms. Store the required key during the silver load, and carry it into the tracker and fact:

```sql
SELECT
      YEAR(ct.SinkCreatedOn) * 100
        + MONTH(ct.SinkCreatedOn)   AS [SinkCreatedMonth]
     ,YEAR(ct.SinkCreatedOn) * 10000
        + MONTH(ct.SinkCreatedOn) * 100
        + DAY(ct.SinkCreatedOn)     AS [SinkCreatedDay]
FROM silver.CustTable AS ct;
```

Keep `Created` in the name so it cannot be confused with a modification period. The fact should retain the driver's stored partition key, rather than derive a new one from another joined table.

## Establish stability

The replacement pattern needs a row to remain in the same partition, or for the load to track both its old and new partitions when it moves. Do not infer that stability from the name `SinkCreatedOn` alone. Microsoft documents export-mode-specific behavior for the sink timestamps in [F&O Synapse Link metadata](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/azure-synapse-link-select-fno-data).

Before adopting extraction cohorts, confirm what happens on updates and reinitialization in your configured export. If the field is rewritten, either preserve an assigned cohort in silver or design explicit handling for partition moves. A full silver reload must preserve or deliberately reset that contract too.

Business dates have a different concern: a new transaction can be posted into an old period. A recent-period-only scan would miss it. Business-date partitioning can work when the tracker identifies changes in every affected period, but a recent-date window alone is insufficient.

## Choose the replacement size

Start with monthly partitions when their rebuild cost fits the load window. Daily partitions help only when rows are actually spread across days. An initial extraction containing years of history may put the whole table into one day, so changing the date format does not distribute that work.

Match tracker and reload granularity where possible. Daily tracker rows can feed a monthly load by summing counts and taking the maximum timestamp, but the extra detail should have a consumer. Don't discard old tracker state merely because the data is old: gold still needs to discover changes and removals there.

See [change tracking partitions](../Silver/Change%20Tracking%20Partitions.md) for maintaining state and [fact partition rebuild](../Gold/Fact%20Patterns/Fact%20Partition%20Rebuild.md) for handling changed or vanished partitions. [Bronze partition-based extraction](../Bronze/Partition-Based%20Incremental.md) is a separate choice about what the source pull includes.
