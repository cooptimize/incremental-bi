---
title: Power BI incremental refresh with deletions (the hard version)
layer: semantic-model
status: working
related:
  - Cross-Cutting/Delete Detection Strategies.md
  - Semantic Model/Full Load.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

Incremental refresh can reflect deletions when it reloads the partition containing them. The difficult case is a deletion in a partition the refresh no longer visits, or one that change detection decides to skip.

Start by identifying how an affected gold row maps to an imported partition. Updating gold and refreshing Power BI are separate operations; completing the first does not establish that the second revisited the right data.

## Separate the partition boundary from change detection

Power BI uses date/time `RangeStart` and `RangeEnd` parameters to filter a table, then manages stored and refreshed periods through its policy. Older partitions outside the refresh period normally remain untouched. See Microsoft's [incremental refresh overview](https://learn.microsoft.com/en-us/power-bi/connect-data/incremental-refresh-overview).

Optional **Detect data changes** compares a period's maximum change timestamp to decide whether to refresh it. A hard deletion may leave that maximum unchanged. Microsoft explicitly documents that this detection does not identify hard-deleted rows; a retained deletion marker with an updated timestamp is a different case. See [Configure incremental refresh](https://learn.microsoft.com/en-us/power-bi/connect-data/incremental-refresh-configure).

For example, deleting one March transaction from gold does not remove its imported copy if March is skipped. Reprocessing March against the completed current-state source removes it because the replacement result no longer contains that transaction.

## Choose how affected periods will be refreshed

| Approach | Suitable when | What it needs |
|---|---|---|
| Refresh the complete at-risk window | Changes and deletions are bounded to a manageable period | A window that covers the actual risk and does not skip required periods |
| Refresh selected historical partitions | Old corrections are sparse and affected periods are known | A mapping from gold changes to model partitions and refresh orchestration |
| Full refresh | Selective refresh costs more to maintain than it saves | A refresh window and capacity that can reload the retained data |

Power BI supports selective partition processing and custom change-detection queries through its advanced XMLA capabilities. Check the workspace's support and read/write configuration before choosing that route. Microsoft describes both in [Advanced incremental refresh](https://learn.microsoft.com/en-us/power-bi/connect-data/incremental-refresh-xmla).

## Track work for the model's partitions

A metadata layer can record which imported periods need refreshing. It should drive refresh selection; it does not have to replace the fact table as the model's data source.

Gold and Power BI may use different partitions. One `SinkCreatedMonth` rebuilt in gold can contain transactions from several posting months. If Power BI partitions by posting date, the refresh work list needs those months, including the old dates of deleted or moved rows. Capture that information before removing the gold rows.

Keep pending work until the model refresh succeeds. A failed refresh must not erase the only record that an old partition needs attention. An empty partition still needs processing to remove its last imported rows.

Extraction-time partitioning is not inherently invalid, but its stability and distribution must suit the model. If an upstream reinitialization changes that mapping, reconcile or rebuild the affected imported partitions deliberately.

## A change log needs state reconstruction

Appending `INSERT`, `UPDATE`, and `DELETE` rows and then unioning only inserts and updates does not produce current state. The earlier inserted copy remains, updates can duplicate it, and excluding the delete event does not remove the prior record.

An event-log model would need explicit version ordering and a latest-state or delta-aggregation design. That is a separate pattern and is not implemented here. The fact-refresh approach above continues to read current gold data.

## Implementation still to validate

This article does not provide a tested refresh controller. The remaining work is to implement the gold-to-model partition mapping, durable refresh work list, retry behavior, historical processing, and reinitialization recovery in a real model. Validate a deletion of the last row in a partition as well as an ordinary update before treating the design as complete.
