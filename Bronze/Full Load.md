---
title: Full load
layer: bronze
status: draft
related:
  - Cross-Cutting/Delete Detection Strategies.md
  - Bronze/CDC and Change Feed.md
  - Bronze/Partition-Based Incremental.md
---

A full load replaces bronze with a complete extraction of the source table. It's a useful starting point when the table fits the extraction window or the source offers no dependable change signal. Rows that have disappeared from the source also disappear from the replacement.

The approach is simple, but “complete” matters. A failed page of API results must not turn into a batch of apparent deletions downstream.

## Extract first, publish after success

Read the source into a separate staging location. For a database export, that may be one bulk operation; for an API, it may be many pages. Validate that the extraction finished before making it the bronze version that silver reads.

Keep the last successful version available until the replacement is ready. Clearing the live target before a long extraction makes every timeout a recovery problem and exposes incomplete data to downstream jobs.

A full extraction also needs a defined scope. If you pull one company, compare or replace that company only. Missing rows mean something only when the old and new extracts cover the same population.

## What a full load costs

Each run reads the entire source, even if only a few rows changed. Measure the extraction time, source load, and API limits before deciding how frequently to run it. A small reference table may cost less to reload than to maintain incrementally; a large transaction table may not fit the available window.

A paginated extraction can also span hours while the source continues changing. Unless the source provides snapshot consistency, the result reflects a collection interval rather than one instant. That distinction matters when comparing related tables or investigating a missing record.

## How it affects silver

Silver can discover deletions by comparing its keys with the completed bronze extract. It must still choose whether to remove those rows, retain history, or preserve a deletion flag. See [delete detection](../Cross-Cutting/Delete%20Detection%20Strategies.md).

A full bronze load does not require a full silver or gold load. It does require useful change information if those layers are to stay incremental. If the extraction rewrites every timestamp, downstream loads may treat every row as changed even when the business data is identical.

## Still to validate

This draft needs a concrete extraction example, including pagination checkpoints, restart behavior, and how a completed extract becomes visible atomically. It also needs measurements from an F&O workload; there is no established table-size cutoff in this project.

When a full extraction is too expensive, compare [change feeds](CDC%20and%20Change%20Feed.md) with [partition-based extraction](Partition-Based%20Incremental.md). Their deletion coverage is different.
