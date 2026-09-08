---
title: Dimension incremental load
layer: gold
status: working
related:
  - Cross-Cutting/Watermark Strategy.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

One MERGE per dimension. Match on the natural key, update when the watermark moved, insert new rows with a fresh surrogate key, delete what left the source. Cost scales with change volume, and surrogate keys never move — which is what keeps every fact that references them valid.

## The source

Shape the source rows first: the natural key, the attributes, and the watermark.

```sql
WITH SourceData AS (
    SELECT ct.DataAreaId, ct.AccountNum, dpt.Name, ct.CustGroup,
           ct.RecId AS SourceRecId, ct.SinkModifiedOn
    FROM silver.CustTable ct
    JOIN silver.DirPartyTable dpt ON dpt.RecId = ct.Party
    WHERE ct.DataAreaId = @DataAreaId
)
```

## Matching

The natural key is the business key plus the company. Never the `RecId` — carry that as an attribute for tracing, but don't match on it, because a company's data can be re-imported with new `RecId` values.

```sql
ON tgt.DataAreaId = src.DataAreaId
   AND tgt.CustomerId = src.AccountNum
```

Usual F&O keys: `AccountNum` for customers and vendors, `ItemId` for products, `MainAccountId` for GL accounts.

## Updating

Only when the source watermark is ahead of what's already in the dimension.

```sql
WHEN MATCHED AND (@ForceUpdate = 1 OR tgt.SinkModifiedOn < src.SinkModifiedOn)
THEN UPDATE SET tgt.Customer = src.Name, ...,
                tgt.SinkModifiedOn = src.SinkModifiedOn
```

## Surrogate keys

The sequence cannot be called inside the MERGE — `NEXT VALUE FOR` is not permitted in a MERGE statement. It has to reach the row through a default constraint on the key column instead:

```sql
CREATE SEQUENCE dbo.seq_CustomerKey START WITH 1 INCREMENT BY 1;

ALTER TABLE gold.DimCustomer ADD CONSTRAINT DF_DimCustomer_CustomerKey
    DEFAULT NEXT VALUE FOR dbo.seq_CustomerKey FOR CustomerKey;
```

Then leave the key out of the insert entirely and let the default fire:

```sql
WHEN NOT MATCHED BY TARGET
THEN INSERT (DataAreaId, CustomerId, Customer, CustomerGroup, SourceRecId, SinkModifiedOn)
     VALUES (src.DataAreaId, src.AccountNum, src.Name, src.CustGroup,
             src.SourceRecId, src.SinkModifiedOn)
```

Keys are append-only and never reused. Gaps left by failed loads are harmless.

## Deleting

```sql
WHEN NOT MATCHED BY SOURCE AND tgt.DataAreaId = @DataAreaId
THEN DELETE;
```

**The company predicate is not optional.** `NOT MATCHED BY SOURCE` is evaluated against the whole target table, not against the rows the source could have matched. Filter the source to one company without filtering the target and the first run deletes every other company's rows — and since those deletes look like ordinary dimension churn, facts start pointing at nothing before anyone notices.

Soft-delete instead where facts still reference the row: `UPDATE SET tgt.IsDeleted = 1`.

## @ForceUpdate

Levels of trust in the change signal, the same ladder the fact patterns use.

`0` trusts the watermark and touches only what moved. `1` ignores it and re-applies every matched row from source — surrogate keys stay put, so facts are unaffected, which is what makes it the right mode for reconciliation. `2` truncates and reloads, which reassigns every key and invalidates every fact that references this dimension; that one is a repair for a broken dimension, not a routine.

## The hard parts

**Natural key reuse.** Customer 1001 is deleted and a different 1001 is created later. MERGE reads that as an update, the surrogate key survives, and every historical fact silently repoints to the new entity. Nothing in the load can detect it. Confirm with the business that keys are never reused before relying on this.

**No row-level watermark.** Some silver tables don't carry `SinkModifiedOn` per row. Use the parquet file's timestamp — see [watermarks](../../Cross-Cutting/Watermark%20Strategy.md). If neither exists, mode `0` degenerates into re-merging every row every run, which for a dimension is usually acceptable; the cost is real for facts, not here.

**Watermark gaps.** Cascading updates and enum redefinitions change meaning without moving `SinkModifiedOn`, and rows go stale silently. Run mode `1` on a cadence rather than adding hash comparison as a first move.

## F&O notes

Effective-dated attributes — prices, exchange rates, worker assignments — are history the source already keeps, not mutations. Loading them here overwrites the history; they belong in a snapshot dimension instead.
