---
title: Incremental with hard delete
layer: silver
status: working
related:
  - Silver/Full Load.md
  - Bronze/CDC and Change Feed.md
  - Gold/Incremental Fact Considerations.md
---
An incremental silver load uses a Copy Data activity to upsert bronze records into the warehouse. We select rows by their modification timestamp, then insert new keys and update existing ones. There's no need to compare every source value with its silver counterpart to decide what changed.

## Read from the last watermark, with an hour of overlap

Keep the last successful watermark for each table. At the start of the next run, capture a new UTC watermark and calculate the read boundary once:

| Pipeline value | Meaning |
|---|---|
| `LastWatermark` | The previous successful run's watermark. |
| `ReadFrom` | `LastWatermark` minus one hour. |
| `RunWatermark` | The current run's UTC timestamp, captured before copying. |

Select bronze rows whose `SinkModifiedOn` is at or after `ReadFrom` and before `RunWatermark`. Copy Data upserts those rows using the source key. The overlap gives delayed records another chance to arrive; rereading a row simply updates its existing silver record. It doesn't guarantee that every delay fits within an hour.

On the first run, omit the lower boundary and use the same upsert to populate the table. This initializes the incremental pattern; use a [full replacement copy](Full%20Load.md) instead when the source lacks reliable change or deletion signals.

Save `RunWatermark` as the next `LastWatermark` only after the upsert and deletion steps succeed. If either fails, keep the previous watermark so the next run retries that window. Run gold after the required silver loads finish.

## Copy recently deleted keys separately

The deletion query reads keys marked deleted within the same window, using the export's deletion or modification timestamp. Exclude those records from the live-row upsert, copy their keys, and remove the matching silver rows. This relies on bronze retaining a deletion signal long enough for the load to read it.

Copy Data's ordinary upsert doesn't delete target rows. The deletion copy needs a sink procedure or a staging table followed by a delete statement to apply those keys. The exact wiring depends on the destination connector; see Microsoft's [SQL Server Copy Data options](https://learn.microsoft.com/en-us/azure/data-factory/connector-sql-server).

We don't compare complete tables to look for missing keys in this pattern. If the export simply removes rows without retaining deleted keys, this deletion query isn't available; use a [full load](Full%20Load.md) to carry those removals into silver.

## SinkSilverModifiedOn

Pass `RunWatermark` into the copy and map it to `SinkSilverModifiedOn` for every inserted or updated row. Use the current run's timestamp—not the previous watermark, the one-hour lookback boundary, or the source row's `SinkModifiedOn`. Rows outside the copied batch keep their existing value.

This gives gold a signal that silver processed the row. A source change dated 09:00 might not reach silver until the 10:00 run. Keeping 09:00 as `SinkModifiedOn` and stamping 10:00 as `SinkSilverModifiedOn` lets gold pick up that newly available row. Repairs and replayed rows also receive the current run's timestamp, even if their business values haven't changed.

A table default alone won't do this: in SQL Server/Azure SQL, a default can populate an insert but doesn't automatically refresh the column on updates. Passing the pipeline value makes the timestamp explicit for both sides of the upsert. See Microsoft's [column-default behavior](https://learn.microsoft.com/en-us/sql/relational-databases/tables/specify-default-values-for-columns).

Define the field through Schema Manager and include it in the copy mapping. For gold results built from several silver tables, their timestamps may need combining into `SinkMaxSilverModifiedOn`. [Incremental fact loads](../Gold/Incremental%20Fact%20Considerations.md) still need to account for related tables arriving at different times and for deleted rows, which cannot carry a new timestamp downstream.
