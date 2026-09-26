---
title: Fact full load
layer: gold
related:
  - Gold/Incremental Fact Considerations.md
  - Gold/Dimension Incremental Load.md
---
A full load replaces the fact with its complete current result. You don't need to work out which rows changed or disappeared; you calculate the result again. When that fits the refresh window, it is often the simplest load to maintain.

Our default for dimensions is to use [MERGE from the start](Dimension%20Incremental%20Load.md). It's simple enough to build in, and it preserves the primary keys that facts already reference.

# Always run as mode 2

Keep `@ForceUpdate` so the pipeline can call every load the same way, but set it to `2` inside a full-load procedure. A parameter default only applies when the caller leaves it out; the assignment overrides an explicit `0` or `1` too.

This SQL Server/Azure SQL example assumes the target exists and the source is complete. Run it when readers can wait until the load finishes:

```sql
CREATE OR ALTER PROCEDURE fact.LoadCustomerInvoices
      @ForceUpdate INT = 2
AS
BEGIN
    SET @ForceUpdate = 2;

    TRUNCATE TABLE fact.CustomerInvoices;

    INSERT INTO fact.CustomerInvoices (DataAreaId, SourceRecId, Amount)
    SELECT
          cit.dataareaid AS DataAreaId
         ,cit.recid      AS SourceRecId
         ,cit.lineamount AS Amount
    FROM d365fo.custinvoicetrans AS cit;
END;
```

## When users read during the load

A scheduled Power BI import can wait for the load to finish. DirectQuery reports, integrations, and other users querying live data may arrive between the truncate and insert. They must not see the temporary empty table as the finished result.

In that case, put the removal and insertion inside one transaction. `COMMIT` makes the replacement available together; on failure, roll it back. Prepare expensive joins and calculations before opening the transaction to keep the write period short.

This is the wrapper around the replacement statements, not another complete procedure:

```sql
SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    -- Place the TRUNCATE and INSERT here so readers cannot see an intermediate result.

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;
    THROW;
END CATCH;
```

The same principle applies when dimension changes and fact replacement must become visible together. A standalone dimension `MERGE` is already one atomic statement; use an outer transaction when several statements must commit together. Readers may wait for the commit, and must not bypass isolation with dirty reads such as `NOLOCK`.
