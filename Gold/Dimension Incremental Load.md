---
title: Dimension incremental load
layer: gold
related:
  - Gold/Incremental Fact Considerations.md
---
A customer's name or group can change, but you don't want to rebuild the entire customer table every time that happens. You want the same primary key in gold, `PKCustomer`, to stay associated with the customer's natural/business key: `dataareaid` plus `customerid`. Sales facts refer to that primary key through `FKCustomer`.

The simple approach is a `MERGE` that reapplies every customer's details, adds new customers, and removes those no longer in the source. If it fits the refresh window, there's no need to maintain change detection. The examples use SQL Server/Azure SQL.

## Start with the procedure

Define `@ForceUpdate` with a default of `1`: update every customer's details. A `0` requests selective updates—only members that have changed. Our default strategy implements the full update, leaving selective updates as a possible later optimization.

```sql
CREATE OR ALTER PROCEDURE dim.LoadCustomer
      @ForceUpdate INT = 1
AS
```

This is the header; the source query and load statements in this article form the procedure body.

## How does a customer keep the same primary key?

The load matches the source company and account number to `dataareaid` and `customerid` in `dim.Customer`. A match keeps its existing `PKCustomer`. A new customer gets a new value from the table's identity column.

This is the one-time table setup. `customerid` is the matching field; `Customer` exposes the account number to reports, and `CustomerName` holds the name:

```sql
CREATE TABLE dim.Customer
(
      PKCustomer BIGINT IDENTITY NOT NULL
     ,dataareaid VARCHAR(4) NULL
     ,customerid VARCHAR(20) NULL
     ,Customer VARCHAR(20) NULL
     ,CustomerName VARCHAR(100) NULL
     ,CustomerGroup VARCHAR(20) NULL
     ,SourceRecId BIGINT NULL
);

CREATE INDEX IX_Customer_dataareaid_customerid
    ON dim.Customer (dataareaid, customerid);
```

The insert leaves out `PKCustomer` so the database assigns it. The load needs one unambiguous match per customer; the matching index helps the lookup but does not enforce uniqueness.

## What if we need to reload the details?

| Value | Requested behavior |
|---|---|
| `0` | Update only changed members, keeping their `PKCustomer` values. This optimization isn't implemented below. |
| `1` (default) | Reapply every customer's details, keeping their `PKCustomer` values. |
| `2` | Remove and reload all customers, regenerating their primary keys. |

Until selective updates are implemented, explicitly promote a pipeline request for `0` to `1`. This is a fallback to the full-update strategy, not a selective load. A parameter default alone doesn't override a supplied `0`.

Mode `2` clears the dimension and regenerates its primary keys, so dependent facts also need rebuilding. If readers need a complete result throughout the load, [commit the removal and replacement together](Fact%20Full%20Load.md#when-users-read-during-the-load). Place this before the CTE and merge:

```sql
IF @ForceUpdate IS NULL OR @ForceUpdate NOT IN (0, 1, 2)
    THROW 50001, 'ForceUpdate must be 0, 1, or 2.', 1;

-- Selective updates aren't implemented; use the full-update strategy.
IF @ForceUpdate = 0
    SET @ForceUpdate = 1;

IF @ForceUpdate = 2
    TRUNCATE TABLE dim.Customer;
```

## The simple approach: merge the complete source

The `MERGE` updates matched customers, inserts new ones, and removes customers absent from the complete source list. The joined source must be complete across all companies; a missing party record can otherwise make an existing customer look deleted. This example assumes hard deletion is appropriate. If historical facts still need a removed customer, retain the dimension member and mark it deleted instead.

The customer name comes from the party table, so the source query joins it to the customer table. Every matched row is updated. Don't filter the source to changed customers: that would make unchanged customers look deleted.

```sql
WITH
     SourceData AS
     (
         SELECT
               ct.dataareaid
              ,ct.accountnum
              ,dpt.name
              ,ct.custgroup
              ,ct.recid
         FROM d365fo.custtable AS ct
         INNER JOIN d365fo.dirpartytable AS dpt
             ON ct.party = dpt.recid
     )
MERGE INTO dim.Customer AS cust
USING SourceData AS src
    ON cust.dataareaid = src.dataareaid
    AND cust.customerid = src.accountnum
WHEN MATCHED THEN UPDATE SET
      cust.Customer = src.accountnum
     ,cust.CustomerName = src.name
     ,cust.CustomerGroup = src.custgroup
     ,cust.SourceRecId = src.recid
WHEN NOT MATCHED BY TARGET THEN
    INSERT
    (
          dataareaid
         ,customerid
         ,Customer
         ,CustomerName
         ,CustomerGroup
         ,SourceRecId
    )
    VALUES
    (
          src.dataareaid
         ,src.accountnum
         ,src.accountnum
         ,src.name
         ,src.custgroup
         ,src.recid
    )
WHEN NOT MATCHED BY SOURCE THEN
    DELETE;
```

## Add selective updates only if they're worth it

Our default is `1`: update every matched row. It preserves `PKCustomer` without maintaining change detection.

If selective updates become worthwhile, replace the `0`-to-`1` fallback with change detection using [SinkSilverModifiedOn](../Silver/Incremental%20with%20Hard%20Delete.md#sinksilvermodifiedon), while `1` continues to update all rows. Joined tables, changed relationships, and sometimes hash comparisons add complexity. Make that change only when measured performance gains justify maintaining it. The merge still needs the complete source for deletes.
