---
title: CDC / change feed
layer: bronze
status: draft
related:
  - Silver/Incremental with Hard Delete.md
---
Some database and integration technologies can keep a lake table updated as source records are inserted, changed, or deleted. Instead of copying the entire table on every run, the service captures and applies the changes. CDC—change data capture—is the underlying idea.

## Let the platform handle the changes

For D365FO, Synapse Link and Link to Fabric provide managed paths for bringing source changes into the lake. Once configured, the service handles ongoing synchronization; we don't have to write our own extraction loop for inserts, updates, and deletions. See Microsoft's [F&O export guidance](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/azure-synapse-link-select-fno-data) and [Link to Fabric overview](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/azure-synapse-link-view-in-fabric).

Deletion handling depends on the export format: a deletion may be represented by a flag rather than immediate physical removal. The useful part is that the service carries that change across. Our downstream loads still need to interpret it correctly.

## Without a managed link, there's more to build

Other databases and APIs may expose change feeds, but consuming them isn't automatically simple. Someone still has to apply the changes, remember where the last successful load stopped, and handle retries.

A reliable `ModifiedOn` field can make finding inserted or updated records fairly straightforward. Deletions are harder: once a row is gone, it can't appear in a query for recently modified records. Without deleted keys or a retained deletion flag, we need a separate comparison to find what disappeared.

That's why a managed link is valuable when available, and why a [full load](Full%20Load.md) is often preferable to building our own incremental extraction. [Timestamp-based loading](Partition-Based%20Incremental.md) is another option when the source provides reliable dates.
