---
title: Full load (default)
layer: semantic-model
status: working
related:
  - Semantic Model/Power BI Incremental Refresh with Deletions.md
---

A full refresh reloads the imported tables from gold. Start here when the refresh fits the available window: the next completed refresh reflects rows that were added, changed, or removed from the queried source population.

Use measured refresh time and resource use to decide when that stops being practical. Dataset size alone does not establish a useful cutoff; source queries, model shape, capacity, and refresh frequency all affect the result.

## Refresh from a completed gold load

Schedule the import after the required gold tables have been published. Refreshing while facts or dimensions are being replaced can expose inconsistent inputs even when the refresh itself succeeds.

Keep the model queries focused on the required columns and reporting grain. A full data refresh does not require recreating the model definition, relationships, or measures from scratch. It reloads the data those objects use.

For setup and connection requirements, use Microsoft's [scheduled refresh documentation](https://learn.microsoft.com/en-us/power-bi/connect-data/refresh-scheduled-refresh). This article concerns import tables without an incremental policy; a routine refresh of a table with such a policy can still leave historical partitions untouched.

## Find the expensive part

Before changing the refresh strategy, establish where time is spent:

- **Source work:** expensive views, repeated joins, or scans that could be handled in the gold load.
- **Data transfer:** more columns or detail than the report needs, or a constrained connection or gateway.
- **Model processing:** a large imported result or transformations that add significant work after retrieval.

Change the part that is limiting the load and measure again. Aggregating data or dividing a model may help, but each changes what consumers can query and should follow the reporting requirements.

## What full refresh does not fix

If gold missed a deletion, the refreshed model will still contain it. If a source query drops transactions, reloading the same query repeats the omission. Refresh completion establishes that processing finished, not that the warehouse is correct.

Keep source-to-gold reconciliation and a report-level check for the measures that matter. A full refresh simplifies the propagation of gold changes; it does not replace those checks.

When rereading unchanged history is the measured bottleneck, consider [incremental refresh with deletions](Power%20BI%20Incremental%20Refresh%20with%20Deletions.md). Include historical corrections and deletions in that design before narrowing the refresh window.
