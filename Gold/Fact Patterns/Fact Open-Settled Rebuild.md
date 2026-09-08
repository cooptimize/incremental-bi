---
title: Fact open/settled rebuild
layer: gold
related:
  - Gold/Fact Patterns/Fact Partition Rebuild.md
  - Cross-Cutting/Delete Detection Strategies.md
---

For facts whose rows keep changing after they are created. Rebuild every open row on every run, freeze settled rows, and re-check only the settled rows whose watermark moved.

## Use case

Source documents and inventory. `InventTrans` mutates through picking, packing and invoicing, then again at financial settlement years later. `SalesLine` mutates until invoiced. `CustTrans` and `VendTrans` carry settlement state that moves when a payment is matched.

Two prerequisites: a state flag on the source that is close to terminal, and a natural key on the fact.

| Source | Flag | How much to trust it |
|---|---|---|
| `InventTrans` | `InventoryClosedDate` | Strong, and a date rather than a boolean, so the settled side can be range-scanned |
| `CustTrans` / `VendTrans` | settled / closed | Strong, but settlement is reversible |
| `SalesLine` | `SalesStatus` invoiced or cancelled | Weakest — quantity and price freeze, header attributes keep moving |

## The high-water mark

How far the settled side has already been processed:

```sql
DECLARE @MaxSettledModifiedOn DATETIME =
    (SELECT MAX(SinkModifiedOn) FROM gold.FactInventTrans WHERE IsSettled = 1);
```

## Everything that belongs in the fact this run

Every open row, plus any settled row that has moved since. This is the fact-shaped result — joins resolved, measures selected:

```sql
SELECT ... INTO #Incoming
FROM silver.InventTrans it
JOIN gold.DimItem di ON di.DataAreaId = it.DataAreaId AND di.ItemId = it.ItemId
WHERE it.InventoryClosedDate IS NULL
   OR it.SinkModifiedOn > @MaxSettledModifiedOn;
```

The driver is a key list — `InventTransId`, `SalesId`, a `CustTrans` `RecId` — not a partition list. Deleting by key and by state rather than by cohort is why the partition namespace problem doesn't arise here. Cost scales with open volume plus change volume; table size doesn't enter into it.

## Clearing the way

Remove the gold copy of every incoming row, matched on the natural key:

```sql
DELETE f FROM gold.FactInventTrans f
JOIN #Incoming i ON i.InventTransId = f.InventTransId;
```

Then remove whatever is left of the open set. Those are open rows absent from `#Incoming` — they vanished from silver, and a keyed delete cannot see a row that no longer exists to be matched:

```sql
DELETE FROM gold.FactInventTrans WHERE IsSettled = 0;
```

## Reload

```sql
INSERT INTO gold.FactInventTrans (...) SELECT ... FROM #Incoming;
```

One materialized set drives both the delete and the insert. That is what makes duplicates impossible — two separately-written predicates that must agree will eventually disagree.

## Why the transitions handle themselves

**Open to settled:** the gold copy is in the open set, so the blanket delete removes it and `#Incoming` reinserts it carrying its new flag. Nothing has to detect the transition.

**Settled to open,** or any settled row that moves: its watermark advanced, so it is in `#Incoming`, deleted by key and reinserted.

## @ForceUpdate

`0` is the pattern above. `1` compares gold to silver by partition and rebuilds what disagrees — see [audit and repair](../Fact%20Audit%20and%20Repair.md). `2` truncates and reloads.

## Fatal flaws

- **A dropped row is never reconsidered.** `SinkModifiedOn` is stamped at lake write time, so it is the arrival order and genuine out-of-order arrival isn't the worry — ties inside a batch at the boundary are. The real hole is a settled row that reached silver but was dropped by the fact's join, usually a dimension member that didn't exist yet. The load succeeds, `@MaxSettledModifiedOn` advances past it, and no watermark scheme recovers it — a stored watermark fails identically. Counting is the only thing that finds it. Run [audit and repair](../Fact%20Audit%20and%20Repair.md) on a cadence.
- **Settled is not terminal.** Cancelling an inventory close, crediting an invoice, or reopening a period moves a large range at once. The watermark scan detects it correctly — it is usually empty and that is the point — but the resulting rebuild is large. Schedule around close.
- **A settled row hard-deleted in silver** is caught by neither delete. Only reconciliation finds it.
- **Denormalized attributes from mutable tables.** A fact carrying a customer name goes stale when `CustTable` changes while the `InventTrans` watermark never moves. No deterministic detection exists — keep mutable attributes in a dimension, or accept the drift and reconcile.
- **The open set is the cost floor.** If open rows never clear — a backlog of un-invoiced orders, inventory left unclosed for years — you rebuild most of the table every night and have gained nothing.
