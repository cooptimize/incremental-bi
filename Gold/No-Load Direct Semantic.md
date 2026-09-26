---
title: No-load direct semantic
layer: gold
related:
  - Gold/Dimension Incremental Load.md
  - Gold/Incremental Fact Considerations.md
  - Gold/Fact Full Load.md
---
Skipping persisted gold tables is cheaper to develop: there are fewer tables, load procedures, and pipeline steps to build. That's a real reason companies do it.

We rarely recommend it. Consider it mainly when a company has one data source, low data volumes, and no practical budget or capacity to build and maintain a fuller warehouse. The report reads the available source or silver data without a separate gold load.

## What the shortcut costs

Gold gives reports stable dimension keys and prepared business results. Without it, the direct design still has to provide reliable relationships, consistent calculations, and acceptable performance. Those responsibilities don't disappear with the load procedure.

A small solution can work this way, but it can also become technical debt immediately. Adding another source or several reports may mean untangling logic that was built for one model before it can be reused.

## Keep the scope small

Use this as a deliberate compromise for a constrained solution. If shared joins and calculations start growing, move them into gold load procedures and keep reporting views focused on presentation. Our SQL standards require an explicit exception for business joins and transformations in views.

Before choosing the shortcut for speed, compare it with a simple [fact full load](Fact%20Full%20Load.md) and [dimension merge](Dimension%20Incremental%20Load.md). Development cost may justify the compromise even when it offers no runtime advantage.
