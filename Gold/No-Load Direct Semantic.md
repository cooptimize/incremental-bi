---
title: No-load direct semantic
layer: gold
status: working
related:
  - Gold/Dimension Patterns/Dimension Incremental Load.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

Skip gold. Point the semantic model at silver views and let Power BI do the modeling.

## When it holds

D365 is the only source, one business process, minimal transformation, and nobody expects it to grow. Development is fast because there is no dimensional model to build. If a slicer needs a column that lives in another table, you have already outgrown it.

## Fatal flaw: you are stuck with string keys

Relationships land on natural keys — `AccountNum`, `ItemId`, `CustAccount`, usually with `DataAreaId` concatenated on. VertiPaq handles those far worse than a dense integer surrogate: larger dictionaries, more expensive relationship joins, more memory. It surfaces as slow slicers and visuals well before the data volume looks big enough to explain it.

The obvious fix isn't available. Getting an integer key onto the fact means joining the fact back to the dimension to fetch `RecId`, and in a view that join runs on every query rather than once at load. Materializing it is the gold layer you skipped. `RecId` is also a sparse `bigint` rather than a dense sequence, so it's second-best even where you can get it.

## Fatal flaw: complexity has no escape hatch

The moment a fact needs a union, a `COALESCE` across sources, or more than a couple of joins, the view has nowhere to go. Nothing to index, nothing to precompute, no incremental load — every refresh re-executes the whole thing, and serverless bills per byte scanned.

From there the options are to materialize, which means building gold and rebuilding the semantic model against different table contracts — new relationships, rewritten measures, no backward compatibility — or to push the complexity into Power Query and DAX, which is worse. Both are rewrites, and neither is incremental.

Plan to stay small, or plan to rebuild.
