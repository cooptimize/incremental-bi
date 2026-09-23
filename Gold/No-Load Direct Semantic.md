---
title: No-load direct semantic
layer: gold
related:
  - Gold/Dimension Patterns/Dimension Incremental Load.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

When the source tables already look close to what a report needs, skipping a persisted gold layer can seem attractive. Power BI reads the data directly, and there is one less load to maintain.

This is an alternative to the standard gold design, not the default for this library. The SQL standards put business joins and calculations in stored procedures and keep reporting views focused on presentation.

## What the gold layer provides

A customer dimension keeps the same `PKCustomer` associated with its `dataareaid` and `customerid`. Facts store that reference as `FKCustomer`. A source record number or a fresh row number generated during refresh is not automatically a substitute for that persistent association.

Gold also prepares shared business results before reports read them. When several reports need the same joins or calculations, the stored procedure is where that work is performed and checked.

The reporting view then selects the prepared columns. Under the standards, shared views use `common`, while a model-specific view uses its model's schema, such as `sales.Customer`. Joins and other business transformations in those views require an explicit exception.

## When to reconsider the extra load

If the source already supplies the required shape, stable keys, and acceptable query performance, a direct approach may avoid unnecessary copying. Measure the actual refresh work before deciding that persistence is needed for speed alone.

If the direct approach starts accumulating business joins and calculations, move that work into the gold procedure and publish a simple view over the result. Keeping the reporting columns consistent can reduce the impact on the semantic model.

## Not covered

- **Exceptions to the view standards:** any required joins or transformations need an explicit decision and a comment explaining the exception.
- **Measured performance:** this article provides no benchmark for deciding when persistence pays for itself.
- **DirectQuery and Direct Lake:** their query and refresh behavior needs separate treatment.
