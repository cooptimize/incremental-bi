---
title: Period snapshot
layer: snapshots
status: draft
related:
  - Snapshots/Snapshots Overview.md
  - Snapshots/Full History Snapshot.md
---

A period snapshot records a dataset at a regular interval: daily inventory, month-end AR aging, or balances at close. Each capture carries a snapshot date so reports can compare positions over time without trying to reconstruct them from today's source state.

Use it when those intervals answer the business question. If the source already preserves the required period-end position, load that result instead of rebuilding it.

## Define one capture

Choose the snapshot grain first. For inventory, that might be one row per company, item, and warehouse on each snapshot date. Store the measures and attributes needed to interpret that position, along with the date identifying the capture.

The load must distinguish a retry from a new snapshot. Running the same capture twice should not double the period's balance. The implementation needs a way to replace an incomplete capture or recognize a completed one before publishing it.

A snapshot date also needs a clear meaning: source business date, close date, and pipeline execution time are not interchangeable. If the job runs after midnight, readers still need to know which position it represents.

## Corrections and deletions

A record deleted between captures is absent from the next snapshot and remains in the earlier one. That is useful when preserving what was observed, but comparisons must account for records appearing and disappearing.

Backdated data requires a separate decision. If a late transaction changes March after the March snapshot was published, you can retain the original observation, restate March, or retain both versions. Choose based on the reporting requirement and make the result distinguishable to consumers.

## Size the history you need

A daily copy of ten million rows adds about 3.65 billion rows in a year. Measure the required grain, capture frequency, and retention before choosing daily detail by default. Partitioning helps manage the result but does not remove the cost of creating and retaining it.

A [full history snapshot](Full%20History%20Snapshot.md) may use less space when few records change, but it introduces different detection and as-of query requirements. It is not automatically the cheaper choice.

## Still to validate

This draft needs a worked F&O example covering the table structure, snapshot date, retry behavior, publication of a completed capture, and correction policy. Period-close timing and late source data must be part of that example.
