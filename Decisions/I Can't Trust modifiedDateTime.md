---
title: I can't trust modifiedDateTime. What do I do?
layer: cross-cutting
status: working
related:
  - Cross-Cutting/Watermark Strategy.md
  - Cross-Cutting/Delete Detection Strategies.md
  - Gold/Dimension Patterns/Dimension Incremental Load.md
  - Gold/Fact Audit and Repair.md
---

Start with one missed change and follow it through the pipeline. A successful job and an advanced watermark tell you that the load ran; they don't establish that the timestamp changed, the row was selected, or the joins kept it.

This guide is for updates that should have reached gold. If the record disappeared, use [delete detection](../Cross-Cutting/Delete%20Detection%20Strategies.md). If the job failed or never advanced its state, fix that operational problem first.

## Find where the row stopped

Record the business key, company, changed attribute, and expected value. Compare the source, bronze, silver, and gold versions, including the timestamps used by each load. That narrows the investigation to an observable gap instead of a general suspicion about `modifiedDateTime`.

Then check the load boundary. A timezone mismatch, a strict comparison at a tied timestamp, or a delayed row arriving behind the saved watermark can all look like a timestamp that failed to move. See [watermark strategy](../Cross-Cutting/Watermark%20Strategy.md) for overlap and checkpoint behavior.

Use the timestamp that describes the event you're detecting. A posting date is useful for selecting a business period; it isn't a replacement for a modification or export signal when finding changed rows.

## Check every contributing table

If the customer name comes from `DirPartyTable`, a watermark on `CustTable` alone cannot detect every name change. The [dimension pattern](../Gold/Dimension%20Patterns/Dimension%20Incremental%20Load.md) combines contributing timestamps into `SinkMaxModifiedOn` using `VALUES` and `MAX`.

For a fact, establish how changed source keys map to output rows or partitions. A header change does not necessarily share the extraction month of every affected line. Detecting a changed input is only the first step; the load still needs to identify what to recompute.

Also check whether the row reached the query and was then excluded. A missing dimension member or an unintended filter can drop it without causing a pipeline error. Replacing the watermark mechanism will not fix that join.

## Choose a fallback for the actual gap

| Finding | Next step |
|---|---|
| Boundary or clock problem | Correct the comparison and replay the affected interval. |
| Related table changed | Include its signal and map the affected output keys. |
| No usable signal for the relevant change | Compare current values or reapply the source on a reconciliation schedule. |
| Large source with a suitable change feed | Evaluate the feed at bronze rather than compensating only in gold. |
| Small table | Measure whether a full reload or unconditional merge is simpler. |

For dimensions, `@ForceUpdate = 1` reapplies matched attributes without replacing their surrogate keys. For facts, [audit and repair](../Gold/Fact%20Audit%20and%20Repair.md) compares expected and loaded results. Neither fixes an upstream omission unless the comparison reaches an input that contains the correct data.

## Use hashes for a defined comparison

A row hash can reduce the cost of comparing many attributes, but the hashed-column list becomes part of the load contract. Adding a business attribute without adding it to the comparison creates another invisible change. Hash collisions also mean equality is not proof that every value matches.

Reach for that mechanism when the missed change demonstrates a need for it. This project does not yet have a validated row-hash implementation or a catalogue of F&O entities with confirmed timestamp gaps. Record reproducible cases and measured repair costs before setting a general fallback policy.
