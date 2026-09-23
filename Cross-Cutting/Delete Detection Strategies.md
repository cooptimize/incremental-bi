---
title: Delete detection strategies
layer: cross-cutting
status: working
related:
  - Cross-Cutting/Watermark Strategy.md
  - Gold/Dimension Patterns/Dimension Incremental Load.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

A timestamp query over surviving rows cannot tell you which rows disappeared. To propagate a deletion, the load needs either a retained signal or a comparison with a complete source population.

Keep detection separate from retention. Discovering that a customer was deleted does not decide whether its historical dimension member should remain, and removing an invalid fact does not require discarding its audit history.

## Use an explicit signal when available

A change feed can identify the deleted key directly. A retained flag such as `IsDeleted` can also work if the row remains available long enough for the consumer to read it. Confirm the actual fields and semantics of the export; a cancelled order is not necessarily a physically deleted record.

Process the signal using the same replay and checkpoint rules as other changes. Include the company or other key scope so one customer's deletion cannot affect another company with the same account number.

For example, a prepared deletion batch can mark dimension members without removing keys still referenced by facts. `#DeletedCustomers` below represents the consumer's normalized batch, not a built-in F&O audit table:

```sql
UPDATE dc
SET IsDeleted = 1
   ,DeletedAt = SYSUTCDATETIME()
FROM gold.DimCustomer AS dc
INNER JOIN #DeletedCustomers AS del
    ON dc.DataAreaId = del.DataAreaId
    AND dc.CustomerId = del.CustomerId
WHERE dc.IsDeleted = 0;
```

An audit log is another possible input, but only if auditing was enabled for the required changes and the records are retained. Don't assume every F&O entity exposes a universal deletion status or audit table.

## Compare complete key sets when there is no signal

A complete extract lets you identify target keys absent from the current source. This can be more expensive than processing events, but it is a valid detection method. Comparing counts alone cannot identify the missing keys, and an insertion can conceal a deletion by keeping the count unchanged.

This example marks missing customers within one company. It assumes silver contains the completed current-state population for that company:

```sql
UPDATE dc
SET IsDeleted = 1
   ,DeletedAt = SYSUTCDATETIME()
FROM gold.DimCustomer AS dc
WHERE dc.DataAreaId = @DataAreaId
    AND dc.IsDeleted = 0
    AND NOT EXISTS
    (
        -- Tests absence from complete silver state to identify removed customers.
        SELECT 1
        FROM silver.CustTable AS ct
        WHERE ct.DataAreaId = dc.DataAreaId
            AND ct.AccountNum = dc.CustomerId
    );
```

Do not run absence-based deletion against an incremental batch or a failed partial extract. Unchanged rows are absent from a delta by design. A soft-delete implementation also needs to clear the flag when a member reappears and initialize it on insert.

## Decide what the target should retain

For a current-state silver table, [hard deletion](../Silver/Incremental%20with%20Hard%20Delete.md) keeps ordinary queries simple. Downstream loads then need a way to discover the removed keys or affected partitions.

For a dimension, preserve members while historical facts still need their keys. A deletion flag can distinguish current membership without breaking those relationships. Reporting rules must decide how retained members appear; filtering them away indiscriminately can also hide historical facts.

For a current-state fact, removing deleted transactions may be necessary to match the source. A [partition rebuild](../Gold/Fact%20Patterns/Fact%20Partition%20Rebuild.md) does this by replacing the relevant slice. If the business needs the previous observation too, retain that history separately or use an explicit history design.

Specify retention per table, then choose a detection and reconciliation schedule that meets the reporting requirement.
