---
title: Power BI incremental refresh with deletions (the hard version)
layer: semantic-model
status: working
related:
  - Semantic Model/Full Load.md
  - Gold/Incremental Fact Considerations.md
---
Incremental refresh is an option when the volume of data makes a [full refresh](Full%20Load.md) impractical. It saves time by keeping older imported periods and refreshing only part of the model. For ERP reporting, we use it only when that saving is necessary: keeping old periods correct can be much harder than loading them again.

## It works best when old data stays unchanged

Large datasets that mostly accumulate new records are a natural fit. If historical rows stay unchanged, leaving them alone avoids repeatedly importing the same data.

ERP transactions don't always behave that way. Settlements can change old values, documents can reopen, and records can be deleted. A recent-period refresh won't pick up changes outside its window, even when gold is already correct.

## Deletions are the difficult part

Suppose a January transaction is deleted from gold in June. If Power BI only refreshes recent months, its imported January copy still contains that transaction. January needs another refresh before the deletion reaches the report.

**Detect data changes** doesn't solve hard deletions by itself. It uses a maximum timestamp, and a deleted row can't provide a new modification time. See Microsoft's [incremental refresh guidance](https://learn.microsoft.com/en-us/power-bi/connect-data/incremental-refresh-configure).

To keep the model correct, we need either a refresh window covering every period that can change or a process that identifies and refreshes affected older partitions. That includes remembering the period of a deleted row after it's gone. This is extra logic to build and maintain, not something incremental loading in gold automatically handles. Microsoft's [advanced refresh guidance](https://learn.microsoft.com/en-us/power-bi/connect-data/incremental-refresh-xmla) covers the options for refreshing historical partitions.
