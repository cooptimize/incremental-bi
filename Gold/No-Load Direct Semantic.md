---
title: No-load direct semantic
layer: gold
related:
  - Gold/Dimension Patterns/Dimension Incremental Load.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

Pointing Power BI at silver views avoids building a persisted gold layer. For a small model with straightforward transformations, that can be a reasonable way to get reporting into use quickly.

The decision becomes harder when the model needs shared dimensions, stable surrogate keys, or expensive fact transformations. Views still need to produce those results whenever the import refresh reads them.

## Where it fits

Consider this approach when silver already has the required reporting grain, relationships are simple, and the source queries fit the refresh window. A small number of predictable joins may be entirely adequate.

Keep the view contract deliberate. Business-facing names, selected columns, and a defined grain make the semantic model easier to maintain even when the data isn't persisted in gold.

## Keys still need a design

F&O natural keys often need company scope, such as `DataAreaId` plus `AccountNum`. The model needs a consistent relationship key on both sides. If you want a warehouse surrogate key, its assignment must remain stable between refreshes; generating a fresh row number in a view is not a durable mapping.

A source `RecId` may be useful where its scope and lifecycle meet the requirement, but it is not automatically the business identity the model needs. The [dimension pattern](Dimension%20Patterns/Dimension%20Incremental%20Load.md) describes a persisted mapping that survives ordinary attribute updates.

Key size and cardinality affect the model's cost, but they need measurement. String keys alone do not establish that a small model will perform badly.

## Transformation cost repeats at refresh

As unions, allocations, and multi-table joins accumulate, the import refresh repeats more work to reconstruct the result. A view can benefit from its underlying engine and indexes; it does not itself preserve a previously calculated result for the next load.

A persisted gold table gives you a place to perform and validate that work once per load, potentially rebuilding only part of the output. That benefit matters when repeated computation becomes the refresh bottleneck or several consumers need the same transformed data.

## Leave a route to persistence

Measure source-query time, refresh duration, and model size as the workload grows. If materializing the result becomes worthwhile, preserving the view's columns and grain can reduce disruption to the semantic model. A change in grain or relationship keys requires a more substantial migration.

This article concerns skipping persisted gold for an import model. DirectQuery and Direct Lake have different query and refresh behavior and remain outside the developed coverage here.
