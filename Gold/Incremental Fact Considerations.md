---
title: Incremental fact considerations
layer: gold
related:
  - Gold/Dimension Incremental Load.md
  - Gold/Fact Full Load.md
---
A fact table might hold ten years of transactions while today's load adds only a few thousand. Rebuilding all ten years is repeated work we'd like to avoid. An incremental load keeps what's already correct and processes the rows that need attention.

The right approach depends on what can happen after a transaction is loaded. If old rows never change, we can just add new ones. If they can change or disappear, we need a way to find and refresh the affected data. The options below explain where each approach saves work and what can make it miss a change. The SQL snippets illustrate the steps; they aren't complete procedures.

For the merge options below, we send only a selected batch of source rows. The merge matches that batch against the fact; it doesn't need every source row because it isn't using absence to detect deletions.

One simple starting point is the maximum `SinkSilverModifiedOn` already stored in the fact: “what has silver written since the latest row we loaded?” Preserve that timestamp when inserting or updating fact rows. A completed silver load for one table does not establish that its related tables have caught up.

# Insert new rows with MERGE

This is the simplest option when loaded transactions stay as they are: insert the missing rows and leave everything else alone.

Posted invoice lines (`CustInvoiceTrans`) and project postings (`ProjTransPosting`) are candidates when the values your fact stores don't change after posting. This example reads from the fact's latest timestamp, then inserts missing keys:

```sql
DECLARE @LastWatermark DATETIME2(7);

SELECT @LastWatermark = MAX(ci.SinkSilverModifiedOn)
FROM fact.CustomerInvoices AS ci;

WITH
     InvoiceChanges AS
     (
         SELECT
               cit.dataareaid
              ,cit.recid
              ,cit.lineamount
              ,cit.SinkSilverModifiedOn
         FROM d365fo.custinvoicetrans AS cit
         WHERE @LastWatermark IS NULL
             OR cit.SinkSilverModifiedOn >= @LastWatermark
     )
MERGE INTO fact.CustomerInvoices AS ci
USING InvoiceChanges AS ic
    ON ci.DataAreaId = ic.dataareaid
        AND ci.SourceRecId = ic.recid
WHEN NOT MATCHED BY TARGET THEN
    INSERT (DataAreaId, SourceRecId, Amount, SinkSilverModifiedOn)
    VALUES (ic.dataareaid, ic.recid, ic.lineamount, ic.SinkSilverModifiedOn);
```

An empty fact has no maximum, so the first run reads all rows. `>=` replays rows at the boundary so records sharing a timestamp aren't excluded; matching on the source key prevents duplicate inserts.

## Related rows may arrive at different times

Don't assume Synapse Link/Fabric has made every part of a transaction available together. An invoice line (`CustInvoiceTrans`) may arrive before its header (`CustInvoiceJour`). If the header is required to build a correct fact row, use an `INNER JOIN` on the full relationship key so the incomplete row isn't loaded.

That join prevents an incomplete result, but it doesn't schedule a retry. Other rows can advance the fact's maximum timestamp while the line waits for its header. The load must revisit that line after the header arrives.

One practical approach is to read back an hour or two before the latest loaded timestamp. This gives delayed relationships another chance to resolve. If an earlier run could already have inserted a row with incomplete details—for example, an inventory transaction missing an optional source-document reference—use an upsert so the next pass can correct it. An insert-only merge would leave that existing row alone.

The upsert example below shows a configurable lookback. Choose the interval from observed delays; two hours is an example, not a freshness guarantee. Longer delays need retained pending keys, selection driven by changes in related tables, or broader checks.

Filtering reduces the batch sent to the merge. How much source data the database scans to find it still depends on storage and indexing.

## Dimension value changes after the transaction is posted

The transaction can stay the same while something the report shows about it changes. For example, a project gets a new manager, and its old postings should now report under **Current Project Manager**. Copying that person's foreign key into each fact row would leave the insert-only load with stale assignments.

Instead, keep `FKProject` on the fact and let a view look up the project's current manager. The old transactions then appear under the new manager without changing the stored fact rows. If you also need the manager at posting, keep that as a separate field.

# Upsert rows with MERGE

Use an upsert when existing rows can change but you can identify which ones need attention. It adds new rows and updates selected fields on existing rows, so you don't have to rebuild a whole period for a handful of changes.

For example, settling a customer transaction can change its closing date. We can update that date while leaving the other stored values alone.

Calculate `@ReadFrom` once by subtracting `@LookbackMinutes` from the fact's maximum timestamp. This example rereads two hours of source changes and updates matched rows as well as inserting new ones.

The example reads `CustTrans.Closed` into the fact's `ClosedDate` field. [CustTrans field reference](https://learn.microsoft.com/en-us/common-data-model/schema/core/operationscommon/tables/finance/accountsreceivable/transaction/custtrans#closed).

```sql
DECLARE @ReadFrom DATETIME2(7);
DECLARE @LookbackMinutes INT = 120;

SELECT @ReadFrom = DATEADD(MINUTE, -@LookbackMinutes, MAX(ct.SinkSilverModifiedOn))
FROM fact.CustomerTransactions AS ct;

WITH
     CustomerChanges AS
     (
         SELECT
               ct.dataareaid
              ,ct.recid
              ,ct.amountmst
              ,ct.closed
              ,ct.SinkSilverModifiedOn
         FROM d365fo.custtrans AS ct
         WHERE @ReadFrom IS NULL
             OR ct.SinkSilverModifiedOn >= @ReadFrom
     )
MERGE INTO fact.CustomerTransactions AS ct
USING CustomerChanges AS cc
    ON ct.DataAreaId = cc.dataareaid
        AND ct.SourceRecId = cc.recid
WHEN MATCHED THEN UPDATE SET
      ct.ClosedDate = cc.closed
     ,ct.SinkSilverModifiedOn = cc.SinkSilverModifiedOn
WHEN NOT MATCHED BY TARGET THEN
    INSERT (DataAreaId, SourceRecId, Amount, ClosedDate, SinkSilverModifiedOn)
    VALUES (cc.dataareaid, cc.recid, cc.amountmst, cc.closed, cc.SinkSilverModifiedOn);
```

The lookback rereads recent rows; it does not delay processing the newest ones. Store the actual source timestamp in the fact, not the adjusted boundary.

Existing rows keep their amount; only the closing date and tracking timestamp are updated. If the purpose of replay is to repair a late relationship, its foreign key or derived fields must be included in the update too. Use the same idea for `VendTrans`, choosing the fields your fact needs to keep current. This example assumes silver records changes to the closing date, including when settlement is undone.

## Danger of MERGE with Deletions

**A merge that detects deletions needs more than the changed rows.** Adding `WHEN NOT MATCHED BY SOURCE THEN DELETE` to the example above would delete unchanged transactions too, because they aren't in the batch.

Finding missing transactions requires a complete comparison of the area you're loading. Across a large fact, that can erase the runtime saving you were trying to achieve.

Replacing affected partitions is one way to keep that comparison smaller. If the source supplies deleted keys, you can delete those rows directly and keep the upsert. [MERGE guidance](https://learn.microsoft.com/en-us/sql/t-sql/statements/merge-transact-sql).

# Replace affected partitions

Replacing a whole period can be simpler than working out every row-level change, especially when deleted records leave no signal behind. Once we know a period needs attention, we remove its old rows and load its complete current contents. Missing transactions disappear as part of that replacement.

Choose a group that keeps replacement affordable: a creation period, a fiscal period, or a whole document. Use the same grouping in the prepared source, saved state, and target replacement. Old groups still need checking when their contents can change.

Ledger transactions (`GeneralJournalAccountEntry`) are a useful example: rerunning year-end close can replace opening entries when its deletion option is enabled, and settlement can change reported details. [Year-end close](https://learn.microsoft.com/en-us/dynamics365/finance/general-ledger/year-end-close).

For this example, use fiscal periods rather than calendar months. Group by `FiscalPeriodRecId` and ledger, then compare each group's latest `SinkSilverModifiedOn` and record count with the last successful load. A period's record ID can be shared across ledgers, so keep the ledger in the comparison and replacement keys.

The snippets use `#LedgerSource`, the complete prepared ledger result with `LedgerRecId`, `FiscalPeriodRecId`, `recid`, `Amount`, and `SinkSilverModifiedOn`. These are the load's prepared fields, not a claim that they all exist on the transaction table. Resolve the ledger and fiscal period through the journal entry, and include relevant joined changes in the silver timestamp.

```sql
SELECT
      ls.LedgerRecId
     ,ls.FiscalPeriodRecId
     ,MAX(ls.SinkSilverModifiedOn) AS MaxSinkSilverModifiedOn
     ,COUNT_BIG(*)                AS RecordCount
INTO #CurrentPeriodState
FROM #LedgerSource AS ls
GROUP BY
      ls.LedgerRecId
     ,ls.FiscalPeriodRecId;
```

`#LoadedPeriodState` holds the same fields saved after this fact's previous successful load. Include periods from both lists so a period that has been emptied still gets cleared:

```sql
WITH
     Periods AS
     (
         SELECT cs.LedgerRecId, cs.FiscalPeriodRecId
         FROM #CurrentPeriodState AS cs
         UNION
         SELECT ps.LedgerRecId, ps.FiscalPeriodRecId
         FROM #LoadedPeriodState AS ps
     )
SELECT
      pr.LedgerRecId
     ,pr.FiscalPeriodRecId
INTO #PeriodsToReload
FROM Periods AS pr
LEFT JOIN #CurrentPeriodState AS cs
    ON pr.LedgerRecId = cs.LedgerRecId
        AND pr.FiscalPeriodRecId = cs.FiscalPeriodRecId
LEFT JOIN #LoadedPeriodState AS ps
    ON pr.LedgerRecId = ps.LedgerRecId
        AND pr.FiscalPeriodRecId = ps.FiscalPeriodRecId
WHERE cs.FiscalPeriodRecId IS NULL
    OR ps.FiscalPeriodRecId IS NULL
    OR cs.MaxSinkSilverModifiedOn IS NULL
    OR ps.MaxSinkSilverModifiedOn IS NULL
    OR cs.MaxSinkSilverModifiedOn <> ps.MaxSinkSilverModifiedOn
    OR cs.RecordCount <> ps.RecordCount;
```

Replace those periods from the prepared rows. An empty period has nothing to reinsert:

```sql
DELETE gl
FROM fact.GeneralLedger AS gl
INNER JOIN #PeriodsToReload AS pr
    ON gl.LedgerRecId = pr.LedgerRecId
        AND gl.FiscalPeriodRecId = pr.FiscalPeriodRecId;

INSERT INTO fact.GeneralLedger
    (SourceRecId, LedgerRecId, FiscalPeriodRecId, Amount)
SELECT
      ls.recid              AS SourceRecId
     ,ls.LedgerRecId         AS LedgerRecId
     ,ls.FiscalPeriodRecId   AS FiscalPeriodRecId
     ,ls.Amount              AS Amount
FROM #LedgerSource AS ls
INNER JOIN #PeriodsToReload AS pr
    ON ls.LedgerRecId = pr.LedgerRecId
        AND ls.FiscalPeriodRecId = pr.FiscalPeriodRecId;
```

Commit the period replacement and its saved state together so a failed run cannot record progress it never finished. Remove saved state for emptied periods; the saved values must describe the rows this run loaded.

## A matching count can hide a change

A deletion and an insertion can cancel each other out in the count. The timestamp helps, but it must advance for the changes that affect the result. Keep independent data checks rather than treating these two values as proof that the fact is correct.

# Skip completed transactions only when safe

When most historical transactions are finished and only a smaller group is still active, reloading that active group can save a lot of work. The difficult part is proving what 'finished' means for the values in your fact.

Inventory transactions illustrate the tradeoff. You might reload unsettled transactions and leave fully settled ones alone, using `InventTrans` and `InventSettlement` to determine which qualify. Finding a settlement record isn't enough by itself; the rule needs to reflect how inventory closing works.

## Settlement can be reversed

An inventory close can be reversed, so “older than the last settlement date” doesn't mean “safe to ignore forever.” When a settlement changes or is reversed, the affected transactions need another load. [Inventory close](https://learn.microsoft.com/en-us/dynamics365/supply-chain/cost-management/inventory-close).

Consider a September 30 close:

| What happens | What the fact load needs to do |
|---|---|
| September 30 is closed | Reload the affected transactions to capture their final costs before excluding them from routine work. |
| That close is reversed | Bring the affected transactions back into the load, including ones previously treated as finished. |
| September 30 is closed again | Reload them again, even though the closing date is still September 30. |

The signal is a change to the closing run, not a later closing date. Retain the closing records and state used by the last successful load, then compare them with the current state. New or changed records, reversals, and removed records must identify the transactions to revisit. A silver modification timestamp can help with writes, but can't describe a deleted closing record by itself.

The likely closing table to investigate is `InventClosing`, alongside `InventSettlement`. Its exact status fields and links to the affected transactions still need verification in the configured export. Avoid substituting an invented `IsFullySettled` flag for that work.

Once the affected transactions are known, replace their old fact rows with the current result, including rows previously excluded as settled. If that affected set can't be identified reliably, broaden the reload scope. Simply ignoring everything before September 30 would miss the reversal and second close.

# Combine status and change detection

If completion usually means a record stops changing, but exceptions are allowed, combine the two approaches: routinely reload active records and use change detection to revisit completed ones. This avoids rereading all completed history without assuming it can never change.

Sales and purchase orders illustrate this approach (`SalesTable`/`SalesLine` and `PurchTable`/`PurchLine`). Reload active orders and completed orders whose headers or lines changed. Include orders that were active at the previous load so their final state reaches gold, and pick up reopened orders again.

## Reopened documents can touch many partitions

Combining order status with monthly partitions can save work, but a few reopened orders spread across several years could trigger a lot of rebuilding. Replacing just those orders and all their lines may be cheaper. Loading each order's complete current line set also removes lines that were deleted.

Try the options on an ordinary day and on a run with closures or reopened orders. Compare their runtime and results with a full load. The best choice depends on how much data those operations actually touch.

# Check that incremental loads stay correct

An incremental load should keep the fact correct. Data checks help prove that the design is doing its job; a regular rebuild shouldn't be needed to hide a known selection bug.

ERP users can take unexpected paths, and administrative scripts or direct database updates may bypass the signals the load relies on. Compare independently prepared source results with gold, rather than checking only the rows selected by the incremental load:

- Compare record counts and amounts by ledger and fiscal period. Include periods present on only one side.
- Check missing or duplicate keys, unresolved dimension references, and attributes that matter to reporting. Equal totals can still hide incorrect assignments.
- Record discrepancies before correcting them. Trace repeated differences back to extraction, joins, or change selection and fix the cause.

Use a [full load](Fact%20Full%20Load.md) or a targeted replacement to recover affected data when needed, then check again. Agreement with silver doesn't prove the ERP was captured correctly; investigate upstream when the source copy is the problem.
