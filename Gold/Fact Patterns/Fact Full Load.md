---
title: Fact full load
layer: gold
related:
  - Gold/Fact Patterns/Fact Partition Rebuild.md
  - Cross-Cutting/ForceUpdate Contract.md
---

A full load replaces the fact table on every run. If it fits your refresh window, start here: you avoid maintaining incremental state and a separate path for deletions already reflected in silver.

It also works well when changes are spread across most of the table or the source query combines inputs that are difficult to map back to individual fact rows. Measure how much work an incremental would actually avoid before adding that machinery.

## Rebuild from the current inputs

The following SQL Server-style excerpt uses conformed budget lines with account, department, date, and amount fields. The unknown key `0` must already exist in both dimensions:

```sql
TRUNCATE TABLE gold.FactBudget;

INSERT INTO gold.FactBudget
(
      AccountKey
     ,DepartmentKey
     ,DateKey
     ,Amount
)
SELECT
      COALESCE(da.AccountKey, 0)    AS [AccountKey]
     ,COALESCE(dd.DepartmentKey, 0) AS [DepartmentKey]
     ,btl.DateKey                   AS [DateKey]
     ,btl.Amount                    AS [Amount]
FROM silver.BudgetTransactionLine AS btl
LEFT JOIN gold.DimAccount AS da
    ON btl.DataAreaId = da.DataAreaId
    AND btl.MainAccountId = da.MainAccountId
LEFT JOIN gold.DimDepartment AS dd
    ON btl.DepartmentId = dd.DepartmentId;
```

Adapt the joins to the actual dimension grain, including company where needed. Each lookup must return at most one member. The left joins keep a line with an unresolved member in the result rather than silently losing its amount.

Load dimensions first and record unresolved lookups for repair. On the next full fact load, a now-available dimension member can replace the unknown key.

## Publish a complete result

The truncate and insert are the replacement body, not a complete procedure. Use a transaction or build into staging and publish the completed result so consumers cannot read the table halfway through. The available publication mechanism depends on the target platform.

The procedure still accepts `@ForceUpdate`; all three modes perform the same full replacement. See the [shared contract](../../Cross-Cutting/ForceUpdate%20Contract.md).

## Keep the reconciliation check

A full load removes the need to detect individual changes in gold. It does not establish that silver is complete or that the query's joins and filters are correct. Compare the loaded result with the expected grain and measures, especially after changing the transformation.

When runtime no longer fits, compare [partition rebuild](Fact%20Partition%20Rebuild.md) for stable transaction values with [open/settled rebuild](Fact%20Open-Settled%20Rebuild.md) for transactions that continue changing.
