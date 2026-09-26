---
title: Full load
layer: bronze
status: draft
related:
  - Bronze/CDC and Change Feed.md
  - Bronze/Partition-Based Incremental.md
---
A full load copies the entire source table into bronze, replacing the previous copy. Every run reads all rows, whether they've changed or not. New records appear, changed values come across, and records deleted from the source disappear from bronze.

This is often the simplest choice. We don't need to identify changes or build a separate process to find deletions. If copying the whole table is fast enough, there may be little reason to make it more complicated.

The tradeoff is reading and transferring the same unchanged data every time. When that becomes too expensive, a [managed change feed](CDC%20and%20Change%20Feed.md) can handle changes for us. Without one, [timestamp-based selection and period replacement](Partition-Based%20Incremental.md) may reduce the work, but deletions need more thought.

A full bronze load doesn't require full loads in silver or gold. Each layer can choose its own strategy.
