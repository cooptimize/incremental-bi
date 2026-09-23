---
title: Incremental with hard delete
layer: silver
status: working
related:
  - Cross-Cutting/Watermark Strategy.md
  - Cross-Cutting/Delete Detection Strategies.md
  - Silver/Change Tracking Partitions.md
  - Silver/Full Load.md
---

This pattern keeps silver as current state: update changed records, insert new ones, and physically remove confirmed deletions. Consumers can query the table without adding a deletion filter to every join.

The tradeoff is that a removed row no longer carries its own change signal. Silver must publish enough information for gold to remove or rebuild the affected output. A partition tracker helps, but a maximum timestamp by itself cannot describe every deletion.

## Establish what bronze contains

There are two different inputs:

- A complete current-state population lets silver infer deletion from absence.
- A change batch requires explicit deleted keys or retained deletion flags. Absence from that batch means nothing about whether a record still exists.

The example below uses the first contract. `bronze.CustTable` is already a completed, deduplicated current-state table. If your export retains deletion markers, normalize those before using this example; do not point it directly at a raw event batch.

## Merge the company being loaded

This SQL Server-style example compares each customer's timestamp with its stored silver timestamp. It preserves the source keys and fields needed by the dimension load:

```sql
WITH
     CompanyCustomers AS
     (
         SELECT
               ct.DataAreaId
              ,ct.AccountNum
              ,ct.CustGroup
              ,ct.RecId
              ,ct.Party
              ,ct.SinkCreatedOn
              ,ct.SinkModifiedOn
         FROM bronze.CustTable AS ct
         WHERE ct.DataAreaId = @DataAreaId
     )
MERGE INTO silver.CustTable AS tgt
USING CompanyCustomers AS src
    ON tgt.DataAreaId = src.DataAreaId
    AND tgt.AccountNum = src.AccountNum
WHEN MATCHED AND
(
       @ForceUpdate = 1
    OR tgt.SinkModifiedOn IS NULL
    OR src.SinkModifiedOn IS NULL
    OR tgt.SinkModifiedOn < src.SinkModifiedOn
) THEN UPDATE SET
      tgt.CustGroup = src.CustGroup
     ,tgt.RecId = src.RecId
     ,tgt.Party = src.Party
     ,tgt.SinkModifiedOn = src.SinkModifiedOn
WHEN NOT MATCHED BY TARGET THEN
    INSERT
    (
          DataAreaId
         ,AccountNum
         ,CustGroup
         ,RecId
         ,Party
         ,SinkCreatedOn
         ,SinkModifiedOn
    )
    VALUES
    (
          src.DataAreaId
         ,src.AccountNum
         ,src.CustGroup
         ,src.RecId
         ,src.Party
         ,src.SinkCreatedOn
         ,src.SinkModifiedOn
    )
WHEN NOT MATCHED BY SOURCE AND tgt.DataAreaId = @DataAreaId THEN
    DELETE;
```

Keep the source complete for the company. Filtering it by watermark would cause the deletion clause to remove unchanged rows. The target-side company condition prevents the same clause from deleting every other company's customers.

This is the merge body, not the whole procedure. Validate `@ForceUpdate` before running it; mode `2` uses the [full-load path](Full%20Load.md) for the requested scope. Commit the target changes and tracker state together, or prevent gold from reading until both are published.

## Tell gold what changed

Refresh [change tracking partitions](Change%20Tracking%20Partitions.md) after the merge. The tracker records both maximum timestamps and counts. Gold compares those values with the state used for its previous load, including partitions that have disappeared entirely.

A deletion does not necessarily advance the maximum timestamp of the surviving rows. Counts catch many such changes, but a delete and insert can offset each other. Periodic reconciliation is still required for gaps in the signal.

If only one source table in a fact changes, gold must map that change to the affected fact keys or partitions. The extraction month of a header or lookup row is not automatically the extraction month of its dependent transactions.

## Keep recovery and history explicit

Hard deletion is suitable for a current-state table, not a substitute for a retention policy. Recovery requires retained inputs, snapshots, or backups. A bronze table that also represents only current state cannot reconstruct a deleted historical row.

Deleting a customer from silver also does not decide what gold should do with its historical dimension member. Preserve referenced keys or coordinate fact recovery according to the reporting requirement. See [dimension incremental load](../Gold/Dimension%20Patterns/Dimension%20Incremental%20Load.md).

Schema changes and changed transformations need a deliberate reload and downstream reconciliation. Resetting a tracker without changing the values gold compares will not, by itself, force gold to rebuild.
