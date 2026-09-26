---
title: Partition-based incremental
layer: bronze
status: draft
related:
  - Bronze/Full Load.md
---
When the source doesn't provide a usable change feed, reliable `CreatedOn` and `ModifiedOn` fields can help us avoid reading the whole table. We can find new or changed records and either copy those rows or use them to identify periods that need reloading.

This can save substantial extraction work. The difficult part is finding deletions, which neither date can tell us about once the row has disappeared.

## Use changed rows to find affected periods

Suppose we group records by their creation month. An order created in January is updated in June. Its `ModifiedOn` tells us it changed, and its `CreatedOn` tells us January needs another load. We aren't limited to reloading the current month.

Once January is selected, read all its current rows and replace January in bronze. That brings across changed values and removes rows no longer in the source. If we instead copy only the changed rows, we need to insert or update them by key and handle deletes separately.

## A deletion may not select its period

Replacing January removes deleted January records—but how do we know January needs replacing? If its only change was a deletion, there may be no remaining row with a new `ModifiedOn` to select it.

We need another way to find those removals, such as a deletion log, a complete key comparison, or checks that identify affected periods. Simply reloading recent months leaves older deletions behind.

For many tables, that extra work makes a [full load](Full%20Load.md) the better choice. Use this approach when the time saved is worth maintaining both change selection and deletion detection.
