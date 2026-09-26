---
title: Overview
---
# ERP Analytics Incrementals

How much data do we really need to reload, and how do we know we didn't miss a change? This library works through those decisions using D365FO examples. The examples illustrate the choices; they aren't prescriptions for every ERP table.

## What do we mean by incremental?

“Incremental” says we're doing less work than a full load. It doesn't say which work we're skipping—or how we know the skipped data is still correct. That's why calling a pipeline incremental can hide more than it explains.

The strategy changes at each layer:

| Where | What we're trying to avoid | What still needs solving |
|---|---|---|
| Bronze | Extracting the entire source again | Can the source expose every change, including deletions? |
| Silver | Replacing the whole warehouse copy | Can we apply a batch, retry it safely, and retain confirmed deletions long enough to consume them? |
| Gold | Recomputing and rewriting the entire result | Which output rows are affected, including changes in joined tables? |
| Semantic model | Refreshing all imported history | Which stored partitions need another read, including older ones? |

These choices don't have to match. Incremental silver can feed a full fact load. A gold load can read complete source data but replace only affected periods. Measure the work saved across selection, joins, and writes—not just the number of rows sent to the final statement.

## Choose by what can change

If loaded values never change, inserting missing rows may be enough. If they change, the load needs a way to select and update them. If records disappear, a modified timestamp can't return them: use deleted keys or compare a complete population, possibly within affected partitions.

Related data matters too. A transaction can stay unchanged while its reported manager or settlement details change. The [fact considerations](Gold/Incremental%20Fact%20Considerations.md) work through these choices and their tradeoffs.

The [dimension merge](Gold/Dimension%20Incremental%20Load.md) solves a different problem: keeping the primary keys that facts reference. Its default reads the complete source and updates every match. Preserving keys doesn't require selective updates.

Start with a [full fact load](Gold/Fact%20Full%20Load.md) if it fits the window. Add selection where the saving justifies maintaining it.

## A change has to reach the report

A correct silver load doesn't mean gold selected every affected row, and correcting gold doesn't refresh an older imported partition. Check each handoff. When something is missing, find the first layer where it diverges rather than assuming the whole pipeline shares one watermark or reload rule.

## Find a strategy

### Bronze

- [Full load](Bronze/Full%20Load.md): copy the entire source table again.
- [CDC and change feeds](Bronze/CDC%20and%20Change%20Feed.md): let managed synchronization carry source changes into the lake.
- [Partition-based incremental](Bronze/Partition-Based%20Incremental.md): use source timestamps to select rows or periods, with separate deletion detection.

### Silver

- [Full load](Silver/Full%20Load.md): replace the warehouse copy when change or deletion signals are unreliable.
- [Incremental with hard delete](Silver/Incremental%20with%20Hard%20Delete.md): upsert with Copy Data using a watermark and one-hour overlap; apply deleted keys separately.

### Gold

- [Fact full load](Gold/Fact%20Full%20Load.md): replace the complete result when it fits the refresh window.
- [Dimension load](Gold/Dimension%20Incremental%20Load.md): update attributes while preserving the primary keys facts reference.
- [Incremental fact considerations](Gold/Incremental%20Fact%20Considerations.md): choose between inserts, upserts, period replacement, and selecting unfinished transactions.
- [No-load direct semantic](Gold/No-Load%20Direct%20Semantic.md): the limited compromise of skipping persisted gold tables.

### Semantic model

- [Full refresh](Semantic%20Model/Full%20Load.md): our default for Power BI.
- [Incremental refresh with deletions](Semantic%20Model/Power%20BI%20Incremental%20Refresh%20with%20Deletions.md): when full refresh is impractical, account for changes to older imported periods.

### Snapshots

- [Snapshot choices](Snapshots/Snapshots%20Overview.md): preserve earlier positions or observed versions when the source doesn't already keep the history you need.

## Using and editing this library

Article metadata describes readiness: `draft` means incomplete, `working` needs implementation validation, and `stable` means validated against a real implementation. An unlabelled article makes no validation claim. Examples explain the patterns; they aren't complete production implementations unless stated otherwise.

[AGENTS.md](AGENTS.md) holds the writing guide and editing instructions. SQL follows [Cooptimize Standards](https://github.com/cooptimize/coop-standards), read from a sibling `../coop-standards/` checkout rather than copied here.

The library includes an [Obsidian Publish theme](publish.css) and is licensed under [MIT](LICENSE).
