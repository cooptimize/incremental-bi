---
title: Dimension incremental load
layer: gold
related:
  - Cross-Cutting/Watermark Strategy.md
  - Cross-Cutting/ForceUpdate Contract.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

A customer's name or group can change, but you don't want to rebuild the entire customer table every time that happens. You want to bring in the changes while keeping the same primary key in gold, `PKCustomer`, associated with that customer's natural/business key: `DataAreaId` plus `CustomerId`. The sales facts already reference that `PKCustomer`.

This pattern updates existing customers and adds new ones. It checks both the customer and party tables for changes, since the customer's name comes from the party record.

## How do we know a customer changed?

`d365fo.custtable` and `d365fo.dirpartytable` each have a `SinkModifiedOn` timestamp. We take the later of the two and call it `SinkMaxModifiedOn`. That gives us one value to compare with the last version loaded into gold.

Here, `VALUES` puts the two timestamps together and `MAX` picks the latest. The query collects customers for one company, identified by `@DataAreaId`:

```sql
WITH
     CompanyCustomers AS
     (
         SELECT
               ct.DataAreaId
              ,ct.AccountNum
              ,ct.CustGroup
              ,ct.RecId
              ,ct.Party
              ,ct.SinkModifiedOn
         FROM d365fo.custtable AS ct
         WHERE ct.DataAreaId = @DataAreaId
     )
SELECT
      cc.DataAreaId         AS [DataAreaId]
     ,cc.AccountNum         AS [CustomerId]
     ,dpt.Name              AS [Customer]
     ,cc.CustGroup          AS [CustomerGroup]
     ,cc.RecId              AS [SourceRecId]
     ,wm.SinkMaxModifiedOn  AS [SinkMaxModifiedOn]
INTO #SourceData
FROM CompanyCustomers AS cc
INNER JOIN d365fo.dirpartytable AS dpt
    ON cc.Party = dpt.RecId
CROSS APPLY
(
    SELECT MAX(ts.SinkModifiedOn) AS [SinkMaxModifiedOn]
    FROM
    (
        VALUES
              (cc.SinkModifiedOn)
             ,(dpt.SinkModifiedOn)
    ) AS ts(SinkModifiedOn)
) AS wm;
```

We keep the full customer list here and decide which rows need updating later. Otherwise, an unchanged customer would be missing from the list and could be mistaken for a deleted one.

## How does a customer keep the same primary key?

The load matches on the natural/business key: `DataAreaId` and `CustomerId`. When it finds a match, it updates the customer's details and leaves the existing primary key, `PKCustomer`, unchanged.

A natural/business key that isn't already in gold gets a new `PKCustomer`. This one-time setup gives the existing dimension table a sequence that supplies the next number automatically:

```sql
CREATE SEQUENCE dim.seq_PKCustomer START WITH 1 INCREMENT BY 1;

ALTER TABLE dim.Customer ADD CONSTRAINT DF_Customer_PKCustomer
    DEFAULT NEXT VALUE FOR dim.seq_PKCustomer FOR PKCustomer;
```

The insert below leaves out `PKCustomer`, letting the default fill it in. That's also how SQL Server supports [using a sequence with MERGE](https://learn.microsoft.com/en-us/sql/t-sql/functions/next-value-for-transact-sql).

## What if we need to reload the details?

Usually, we trust the timestamps to tell us what changed. Sometimes we want to reapply the customer details anyway, or start the company's customer table over. The procedure's `@ForceUpdate` parameter selects the behavior and defaults to `0`:

| Value | What happens |
|---|---|
| `0` | Update customers with a newer timestamp. |
| `1` | Reapply every customer's details, keeping their existing `PKCustomer` values. |
| `2` | Remove and reload the company's customers, assigning new `PKCustomer` values. |

Use `1` to bring stale details back in line with the source. With `2`, those primary keys are reassigned, so the facts that reference them also need rebuilding.

After collecting the source rows, only mode `2` clears the company's existing customers:

```sql
IF @ForceUpdate IS NULL OR @ForceUpdate NOT IN (0, 1, 2)
    THROW 50001, 'ForceUpdate must be 0, 1, or 2.', 1;

IF @ForceUpdate = 2
    DELETE dc
    FROM dim.Customer AS dc
    WHERE dc.DataAreaId = @DataAreaId;
```

## Bringing the changes into gold

The `MERGE` puts those decisions together. An existing customer gets updated when its timestamp is newer, when a timestamp is missing, or when mode `1` requests it. A new customer gets inserted and receives its `PKCustomer` from the sequence.

This example also removes customers missing from the complete source list. The delete condition limits that removal to the company we're loading.

```sql
MERGE INTO dim.Customer AS tgt
USING #SourceData AS src
    ON tgt.DataAreaId = src.DataAreaId
   AND tgt.CustomerId = src.CustomerId
WHEN MATCHED AND (
       @ForceUpdate = 1
    OR tgt.SinkMaxModifiedOn IS NULL
    OR src.SinkMaxModifiedOn IS NULL
    OR tgt.SinkMaxModifiedOn < src.SinkMaxModifiedOn
) THEN UPDATE SET
      tgt.Customer = src.Customer
     ,tgt.CustomerGroup = src.CustomerGroup
     ,tgt.SourceRecId = src.SourceRecId
     ,tgt.SinkMaxModifiedOn = src.SinkMaxModifiedOn
WHEN NOT MATCHED BY TARGET THEN
    INSERT
    (
          DataAreaId
         ,CustomerId
         ,Customer
         ,CustomerGroup
         ,SourceRecId
         ,SinkMaxModifiedOn
    )
    VALUES
    (
          src.DataAreaId
         ,src.CustomerId
         ,src.Customer
         ,src.CustomerGroup
         ,src.SourceRecId
         ,src.SinkMaxModifiedOn
    )
WHEN NOT MATCHED BY SOURCE AND tgt.DataAreaId = @DataAreaId THEN
    DELETE;
```

## Not covered

- **Procedure setup and failed runs:** these SQL Server/Azure SQL snippets assume the tables exist; transaction and retry handling must keep a failed load from leaving partial changes.
- **Keeping deleted customers for old sales:** use a deletion flag when historical facts still need the customer; see [delete detection](../../Cross-Cutting/Delete%20Detection%20Strategies.md).
- **Missing or late source data:** incomplete joins can look like deletions, and timestamps can miss changes; see [reconciliation](../../Cross-Cutting/ForceUpdate%20Contract.md).
- **Reused customer numbers:** the match assumes a customer number continues to identify the same customer within its company.
- **Keeping earlier names or groups:** this example overwrites details; see [snapshots](../../Snapshots/Snapshots%20Overview.md) when reports need their history.
- **Reducing source reads:** updating fewer customers doesn't necessarily mean reading fewer source rows.
