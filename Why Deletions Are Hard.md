---
title: Why deletions are hard
status: working
---

# Why deletions are hard

A table has ten million rows, and five hundred changed since yesterday. Loading only those changes is an obvious saving—provided the pipeline can discover every kind of change it needs to apply.

An update leaves a row to retrieve. A hard deletion may leave nothing in the current-state table. If the source exposes no deletion event or retained marker, a query for recently modified rows cannot return the missing record.

## Absence needs a complete comparison

A deleted record is absent from an incremental extract, but so is every unchanged record. That makes absence useless as a delete signal unless you know the extract covers the complete population being compared.

A full extract provides that population. A change feed can instead provide the deleted key explicitly. A partition-based extract gives you a complete comparison only within the partitions it revisits. Each approach can be useful, but they offer different deletion coverage.

The failure is often quiet. The job finishes successfully because every row it received was processed. An obsolete row remains in the target, and its amount continues contributing to reports until another process finds it.

## Follow one deletion through the layers

Suppose an old transaction is removed from the source. Bronze must first expose the removal, either through an event, a flag, or a completed replacement in which the key is absent. If the extraction never observes it, every downstream table can agree with bronze and still be wrong.

Silver then applies its retention policy. A current-state table can remove the row. If it does, the downstream load needs the deleted key, the affected partition, or a comparison that reveals the difference. The row's old timestamp no longer provides a message to gold.

Gold must remove or recompute the corresponding result. For a simple fact, replacing the affected partition can be enough. For an aggregate, the deleted transaction's contribution must also come out of the total. A source deletion does not necessarily correspond to one easily identified output row after joins and aggregation.

Finally, an imported semantic model must reread the affected data. A correct gold table can sit beneath a stale report if the relevant historical partition is never refreshed. See [incremental refresh with deletions](Semantic%20Model/Power%20BI%20Incremental%20Refresh%20with%20Deletions.md) for that boundary.

## Dimensions have a different retention question

Deleting a customer from current source data does not necessarily mean removing its historical dimension member. Facts may still refer to that member's surrogate key and need its attributes to remain interpretable.

A retained member with a deletion flag can preserve that relationship. Hard deletion may be appropriate where no facts depend on it, but it must be an explicit choice. Detection tells you what happened in the source; the reporting requirement tells you what to retain.

## Don't confuse deletion with another business event

Cancellation, reversal, inactivity, and physical deletion can have different representations. A cancellation may update a status. A reversal may add an offsetting transaction while leaving the original intact. Treating either as a hard deletion can produce the wrong historical result.

Check the actual entity and operation, including cleanup and period-close procedures. A business description such as “posted transactions don't change” is not sufficient evidence for how every source operation behaves.

## Make the detection gap explicit

Before choosing an incremental pattern, establish whether the source supplies deleted keys, retains a flag, or requires a complete comparison. Then decide how quickly removals must reach reports and which layers retain history.

If deletion is assumed impossible, document the operation and population that assumption covers. If deletion is possible but only periodic reconciliation will find it, that schedule defines how long stale rows can remain visible.

[Delete detection strategies](Cross-Cutting/Delete%20Detection%20Strategies.md) covers those mechanisms. [Fact audit and repair](Gold/Fact%20Audit%20and%20Repair.md) explains how to check the loaded result independently of the routine change signal.
