---
title: Overview
---

# ERP Analytics Incrementals

"Incremental load" is not a technique. It is one label stretched across a dozen unrelated problems, and most of the pain in ERP analytics comes from answering a different question than the one you actually have.

## The same word means something different at every layer

**Bronze — what can I avoid pulling?** Bounded by what the source is willing to tell you. F&O signals some changes, doesn't signal others, and barely signals deletes at all.

**Silver — what can I avoid rewriting?** Bounded by deletes. Hard-delete and gold has to reload; soft-delete and every query downstream carries a filter forever.

**Gold — what can I avoid recomputing?** Bounded by the join. A fact row's change signal lives on its inputs, never on the row itself, and translating between the two is most of the difficulty in this repository.

**Semantic model — what can I avoid refreshing?** Bounded by what Power BI can address as a partition, which rarely lines up with how gold is partitioned.

Each layer's answer constrains the next. A bronze decision made in week one sets the gold cost in year two, and by then the cheap fix is gone.

## Three questions fork everything

**Does the source signal deletes?** Usually not, or not everywhere. Every pattern here either has a delete story or has a hole where one should be, and it's worth knowing which before you ship.

**Do rows mutate after creation, and for how long?** A posted GL entry never moves. An `InventTrans` row mutates from creation through settlement, which can be years. Same warehouse, same tooling, opposite patterns.

**Is the output one row per source row, or the product of a join?** One-to-one means a changed source row maps to a fact row you can find. A join means the change arrives on a table whose rows aren't the fact's rows, and no amount of watermarking fixes that by itself.

None of these are answered by picking a tool, and nothing else in the design matters as much.

## What incremental actually buys

Freshness. Not correctness.

Every pattern here has holes — a change the watermark can't see, a row a join silently dropped, a partition scheme that a link re-initialization flattens. The honest architecture is an incremental that runs often and a reconciliation that runs on a schedule and **measures** how wrong the incremental was. If you can't state your error rate, you don't have one, you have a belief.

## The layer model

The medal metaphor is a bad one — bronze data isn't worse than gold data, it's earlier. The layers exist for reasons that have nothing to do with ranking.

**Bronze — raw.** Preserve what the source gave you, as it gave it to you. Bronze exists because sources change and pipelines fail: if you transform on the way in, a bad run can't be recovered without re-extracting.

**Silver — usable.** Typing, deduplication, conforming. Persisted, not staging. Silver exists because F&O's internal key structures and naming have to be resolved before anything downstream can use them.

**Gold — shaped for the business.** Facts, dimensions, surrogate keys, readable names. Gold exists because joining five silver tables to answer a basic sales question is the wrong abstraction for a report developer.

**Semantic model — consumption.** Usually a subset of gold. The shape is often nearly identical; what changes is exposure — refresh partitioning, DAX measures, row-level security, and the relationship graph Power BI needs to generate correct queries.

Names vary by organization: bronze is also raw, landing, ingestion; silver is refined, cleansed, conformed; gold is presentation, mart, curated; semantic model is dataset or tabular model. This project uses bronze/silver/gold/semantic throughout.

## What this doesn't cover yet

- **DirectQuery and Direct Lake against gold.** Everything here assumes an import semantic model. Direct Lake changes the question — gold's write pattern becomes a query-performance concern, not just a load-cost one, and partition-level delete-and-reload interacts with framing in ways this repo hasn't worked through.
- **Measured numbers.** The cost arguments are structural, not benchmarked. No amplification ratios have been recorded from a real environment yet.
- **Snapshots.** Exploratory. Check whether the source already keeps date-effective history before building any of it.

## Where to start

- [Pattern index](Pattern%20Index.md)
- [Delete detection](Cross-Cutting/Delete%20Detection%20Strategies.md) — the problem underneath half the patterns here
- [Watermark management](Cross-Cutting/Watermark%20Strategy.md) — why the obvious approach has holes
- [@ForceUpdate](Cross-Cutting/ForceUpdate%20Contract.md) — the calling contract every load procedure shares
