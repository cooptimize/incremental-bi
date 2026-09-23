---
title: Partition-based incremental
layer: bronze
status: draft
related:
  - Cross-Cutting/Delete Detection Strategies.md
  - Cross-Cutting/Partition Keys.md
  - Bronze/Full Load.md
---

Partition-based extraction reloads a recent slice of the source on each run, such as records created this month. It reduces the amount pulled without requiring a change feed, but it relies on older slices being stable or checked separately.

An immutable date keeps a record in the same slice. It does not guarantee that the record stops changing. An order created in January can still be amended or deleted in June.

## Choose the window

Use a source field whose behavior you understand, then define the oldest partition each run will revisit. A creation date and an accounting date answer different questions: a transaction entered today can carry an accounting date in a prior period.

If that prior period lies outside the extraction window, the row is missed. Making the date immutable doesn't solve backdated arrivals; the window must cover where new and changed records can actually appear.

Overlap can cover ordinary delays near a boundary. It cannot cover an arbitrarily old correction. Size the window from observed behavior and the reporting requirement, then choose a separate reconciliation cadence for data outside it.

## Replace the selected slice completely

Extract the full contents of the selected partitions into staging and publish them after success. Replacing a complete slice makes deletions within that slice visible by absence. An upsert alone leaves deleted rows behind, even inside the reload window.

Keep the extraction and replacement predicates aligned. If you fetch June but delete May and June from bronze, the load has removed data it never intended to replace.

## Older records need another path

A January order deleted in June remains in bronze if January is never read again. The options are a periodic full reconciliation, a separate key comparison for older partitions, or a reliable deletion signal from the source. A soft-delete flag helps only when the extraction actually retrieves the changed record.

Choose the acceptable delay explicitly. A monthly reconciliation means a deletion may remain visible for most of a month; that can be acceptable for one report and unacceptable for another.

This extraction decision differs from [partition keys in silver and gold](../Cross-Cutting/Partition%20Keys.md). Here the date determines what you can retrieve from the source. Downstream, a stored partition key determines what gets replaced after changes have already arrived.

## Still to validate

This draft needs an entity-specific example with a verified partition field, measured arrival delays, and a restartable replacement operation. It does not establish a default reconciliation interval for F&O.

Use [full extraction](Full%20Load.md) when these assumptions don't hold and no suitable [change feed](CDC%20and%20Change%20Feed.md) is available.
