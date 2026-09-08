---
title: Fact full load
layer: gold
status: working
related:
  - Gold/Fact Patterns/Fact Partition Rebuild.md
  - Cross-Cutting/ForceUpdate Contract.md
---

Truncate and reload. The right answer more often than it looks.

## When

- The fact fits the load window. Most F&O facts that aren't sales, inventory or GL do.
- Change is diffuse enough that an incremental would reload most of the table anyway. Measure that before assuming otherwise — rows reloaded divided by rows actually changed.
- The source query is complex enough — unions, `COALESCE` across sources, several tables — that no change signal maps cleanly onto the fact's output rows.

Reloading has no delete problem, no watermark, no change tracker, no partition state and nothing to reconcile against. Every incremental pattern here is machinery bought to avoid this one, and the machinery carries a maintenance cost that nightly runtime never shows you.

## The pattern

```sql
TRUNCATE TABLE gold.FactBudget;

INSERT INTO gold.FactBudget (AccountKey, DepartmentKey, DateKey, Amount)
SELECT da.AccountKey, dd.DepartmentKey, bl.DateKey, bl.Amount
FROM silver.BudgetTransactionLine bl
JOIN gold.DimAccount da ON da.DataAreaId = bl.DataAreaId AND da.MainAccountId = bl.MainAccountId
JOIN gold.DimDepartment dd ON dd.DepartmentId = bl.DepartmentId;
```

The procedure still declares `@ForceUpdate INT = 2` and ignores it, so the orchestrator can call every load the same way. See [@ForceUpdate](../../Cross-Cutting/ForceUpdate%20Contract.md).

## The hard parts

- **The table is empty while it loads.** Wrap it in a transaction, or build into a staging table and swap, if anything can query gold during the window.
- **Dimensions must load first.** Every surrogate key is resolved at load time, so a dimension row that doesn't exist yet silently drops the fact row that needed it. Route those to an unknown member instead of letting an inner join eat them.
