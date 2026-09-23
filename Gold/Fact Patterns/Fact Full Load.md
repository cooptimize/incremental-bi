---
title: Fact full load
layer: gold
related:
  - Gold/Fact Patterns/Fact Partition Rebuild.md
  - Cross-Cutting/ForceUpdate Contract.md
---

If rebuilding the sales table fits the refresh window, you may not need an incremental load. Prepare the current sales rows and replace the fact. Deleted lines disappear because they are no longer in the source.

This SQL Server/Azure SQL example prepares the rows before clearing `fact.Sales`.

## Prepare the sales rows

The order header supplies the customer account. Matching that account and company to `dim.Customer` gives us `PKCustomer`, which the fact will store as `FKCustomer`:

```sql
SELECT
      st.custaccount
     ,sl.salesid
     ,sl.lineamount
     ,cust.PKCustomer
INTO #FinalSales
FROM d365fo.salesline AS sl
INNER JOIN d365fo.salestable AS st
    ON sl.dataareaid = st.dataareaid
    AND sl.salesid = st.salesid
LEFT JOIN dim.Customer AS cust
    ON sl.dataareaid = cust.dataareaid
    AND st.custaccount = cust.customerid;
```

The left join keeps sales with a missing customer match. Their `FKCustomer` is null until a later load resolves it.

## Replace the fact

Clear the old result and insert the prepared rows, naming the fact columns here:

```sql
TRUNCATE TABLE fact.Sales;

INSERT INTO fact.Sales
(
      FKCustomer
     ,Customer
     ,SalesOrder
     ,SalesAmount
)
SELECT
      fs.PKCustomer     AS [FKCustomer]
     ,fs.custaccount    AS [Customer]
     ,fs.salesid        AS [SalesOrder]
     ,fs.lineamount     AS [SalesAmount]
FROM #FinalSales AS fs;
```

All three `@ForceUpdate` modes perform this same replacement. If rereading the whole table becomes too expensive, compare [partition rebuild](Fact%20Partition%20Rebuild.md) and [open/settled rebuild](Fact%20Open-Settled%20Rebuild.md).

## Not covered

- **Live readers and failed writes:** wrap removal and insertion in a transaction when they must become visible together.
- **Source completeness and duplicate matches:** missing headers can drop lines, and multiple customer matches can multiply them; validate the intended row count.
- **Unresolved customers:** track null `FKCustomer` values and confirm they resolve after the dimension load.
- **Business transformations:** add currency, allocation, and reporting rules when preparing the rows.
- **Reconciliation:** a full load can repeat a source or join error; see [audit and repair](../Fact%20Audit%20and%20Repair.md).
