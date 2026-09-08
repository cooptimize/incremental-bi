---
title: Full load (default)
layer: semantic-model
status: working
related:
  - Semantic Model/Power BI Incremental Refresh with Deletions.md
---

## What this is

Full dataset refresh. Power BI pulls all data from the source tables on every refresh cycle. This is the default and recommended approach for most scenarios.

**Core principle:** Simple, reliable, and correct. The entire semantic model is rebuilt from the gold layer on each run.

## When to use it

- Dataset is under 1-2 GB
- Refresh frequency is 1x daily or less
- Refresh time fits your SLA (typically 30 minutes to 2 hours for large datasets)
- You want simplicity and correctness over optimization
- Delete handling is automatic (deleted rows don't appear on refresh)

**This is the right choice for the vast majority of Power BI semantic models.** Only optimize if full load is actually the bottleneck.

## When NOT to use it

- Dataset is massive (> 5-10 GB) and refresh window is tight (hourly or sub-hourly required)
- Full load time exceeds your SLA repeatedly
- You need incremental refresh for business reasons (e.g., near-real-time dashboard)

If full load is slow, the bottleneck is usually:
1. Gold layer queries are expensive (fix the query, not the refresh strategy)
2. Network latency to Fabric/Synapse (network problem, not refresh problem)
3. Gateway capacity is constrained (add capacity, not incremental refresh)

Incremental refresh adds complexity. Use it only if you've verified full load is actually the constraint.

## How it works

1. Power BI opens a connection to the gold layer (SQL, Synapse, Fabric)
2. Queries run: one per table in the semantic model
3. All data is pulled and loaded into Power BI's memory
4. Relationships are rebuilt, measures recalculate
5. Semantic model is ready

No partition tracking. No watermarks. No deletion complexity. Just pull everything.

## Configuration in Power BI

In Power BI Desktop or Service:
- Go to semantic model settings
- Data source credentials: set connection string to gold layer
- Refresh schedule: set daily or as needed
- No incremental refresh enabled

That's it.

## Performance tuning before considering incremental

1. **Optimize gold layer queries:** Are dimensions and facts queried efficiently? Check execution plans.
2. **Reduce column count:** Only import columns actually used in reports. Remove staging/debugging columns.
3. **Aggregate where possible:** If reports only need summarized data, aggregate in gold instead of pulling detail.
4. **Partition the semantic model by business domain:** Multiple smaller datasets refresh faster and are easier to maintain than one monolithic model.
5. **Use Direct Query for historical data:** If only current period needs to be imported and historical data can be queried on-demand, use hybrid import/DirectQuery.

These changes often cut refresh time in half without the complexity of incremental refresh.

## F&O specific patterns

For most F&O implementations:
- Customer, vendor, item dimensions: < 1 GB, import as-is
- GL balances fact: import monthly snapshot or current period detail + historical summary
- Sales/purchase orders fact: import current year, archive prior years

Full load is sufficient.

## When incremental refresh might be needed

Only if:
- Dataset is genuinely massive (> 10 GB) AND refresh must be hourly or more frequently
- Incremental refresh time savings are measured (at least 50% reduction) compared to full load
- Delete handling is accounted for (see `incremental-period-with-deletes.md`)
- You have capacity to maintain partition tracking and watermark logic

This is rare.

## Related patterns

- [Incremental refresh with deletes](Power%20BI%20Incremental%20Refresh%20with%20Deletions.md) — Advanced: only for very large datasets with tight SLA

## Open questions

- At what dataset size does incremental refresh actually save time vs. full load?
- What's the typical cost (in operational complexity) of maintaining partition tracking?
