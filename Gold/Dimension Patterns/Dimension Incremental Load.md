---
title: Dimension incremental load
layer: gold
related:
  - Cross-Cutting/Watermark Strategy.md
  - Cross-Cutting/ForceUpdate Contract.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

A customer's name or group can change, but you don't want to rebuild the entire customer table every time that happens. You want the same primary key in gold, `PKCustomer`, to stay associated with the customer's natural/business key: `dataareaid` plus `customerid`. Sales facts refer to that primary key through `FKCustomer`.

This pattern updates existing customers and adds new ones. It checks both the customer and party tables because the customer's name comes from the party record. The examples use SQL Server/Azure SQL.

## How do we know a customer changed?

Each source table has a `SinkModifiedOn` timestamp. `VALUES` puts them together and `MAX` picks the latest, giving us one `SinkMaxModifiedOn` to compare with gold.

Join the customer to its party record and keep the result for the merge. The company filter matches the company we replace later:

```sql
SELECT
      ct.dataareaid
     ,ct.accountnum
     ,dpt.name
     ,ct.custgroup
     ,ct.recid
     ,(
          SELECT MAX(ts.SinkModifiedOn)
          FROM (VALUES (ct.SinkModifiedOn), (dpt.SinkModifiedOn)) AS ts(SinkModifiedOn)
      ) AS [SinkMaxModifiedOn]
INTO #SourceData
FROM d365fo.custtable AS ct
INNER JOIN d365fo.dirpartytable AS dpt
    ON ct.party = dpt.recid
WHERE ct.dataareaid = @DataAreaId;
```

The timestamp controls which customers get updated later. Filtering this list to changed customers would make unchanged ones look deleted.

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
     ,SinkMaxModifiedOn DATETIME2(7) NULL
);

CREATE INDEX IX_Customer_dataareaid_customerid
    ON dim.Customer (dataareaid, customerid);
```

The insert leaves out `PKCustomer` so the database assigns it. The matching index helps the lookup; it does not enforce uniqueness.

## What if we need to reload the details?

The procedure's `@ForceUpdate` parameter defaults to `0`:

| Value | What happens |
|---|---|
| `0` | Update customers with a newer timestamp. |
| `1` | Reapply every customer's details, keeping their `PKCustomer` values. |
| `2` | Remove and reload the company's customers, assigning new primary keys. |

Use `1` to bring stale details back in line with the source. With `2`, facts referencing the old primary keys also need rebuilding. After gathering the source, only mode `2` clears the company:

```sql
IF @ForceUpdate IS NULL OR @ForceUpdate NOT IN (0, 1, 2)
    THROW 50001, 'ForceUpdate must be 0, 1, or 2.', 1;

IF @ForceUpdate = 2
    DELETE cust
    FROM dim.Customer AS cust
    WHERE cust.dataareaid = @DataAreaId;
```

## Bringing the changes into gold

The `MERGE` updates matched customers, inserts new ones, and removes customers absent from the complete source list. This example assumes those removals are appropriate; the company condition keeps other companies untouched.

Source fields become the dimension's fields here, including the separate customer number and name. Missing timestamps or mode `1` cause details to be reapplied.

```sql
MERGE INTO dim.Customer AS cust
USING #SourceData AS src
    ON cust.dataareaid = src.dataareaid
    AND cust.customerid = src.accountnum
WHEN MATCHED AND
(
       @ForceUpdate = 1
    OR cust.SinkMaxModifiedOn IS NULL
    OR src.SinkMaxModifiedOn IS NULL
    OR cust.SinkMaxModifiedOn < src.SinkMaxModifiedOn
) THEN UPDATE SET
      cust.Customer = src.accountnum
     ,cust.CustomerName = src.name
     ,cust.CustomerGroup = src.custgroup
     ,cust.SourceRecId = src.recid
     ,cust.SinkMaxModifiedOn = src.SinkMaxModifiedOn
WHEN NOT MATCHED BY TARGET THEN
    INSERT
    (
          dataareaid
         ,customerid
         ,Customer
         ,CustomerName
         ,CustomerGroup
         ,SourceRecId
         ,SinkMaxModifiedOn
    )
    VALUES
    (
          src.dataareaid
         ,src.accountnum
         ,src.accountnum
         ,src.name
         ,src.custgroup
         ,src.recid
         ,src.SinkMaxModifiedOn
    )
WHEN NOT MATCHED BY SOURCE AND cust.dataareaid = @DataAreaId THEN
    DELETE;
```

## Not covered

- **Failed rebuilds:** mode `2` removal and the merge need to commit together when consumers require a complete result.
- **Keeping deleted customers or earlier details:** see [delete detection](../../Cross-Cutting/Delete%20Detection%20Strategies.md) and [snapshots](../../Snapshots/Snapshots%20Overview.md).
- **Missing or late source data:** incomplete joins can resemble deletions, and timestamps can miss changes; use [reconciliation](../../Cross-Cutting/ForceUpdate%20Contract.md).
- **Duplicate, null, or reused matching values:** this example needs one unambiguous match per customer; the non-unique index does not establish that.
- **Other targets and source-read costs:** identity setup is platform-specific, and fewer updates do not necessarily mean fewer source rows read.
