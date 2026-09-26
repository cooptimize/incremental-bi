---
title: Full load (default)
layer: semantic-model
status: working
related:
  - Semantic Model/Power BI Incremental Refresh with Deletions.md
---
Full refresh is our default for Power BI. It rereads all imported data from gold, so new rows, corrections, and deletions reach the model without having to work out which historical periods changed.

Use it unless the model is too large or the refresh takes too long to meet the requirement. An incremental gold load doesn't require incremental refresh in Power BI; we can save work building the facts and still refresh the complete model afterward.

[Incremental refresh](Power%20BI%20Incremental%20Refresh%20with%20Deletions.md) adds significant complexity when old ERP transactions can change or disappear. Before taking that on, check whether improving the source queries or reducing unnecessary model data makes a full refresh practical.

Here, full refresh means reloading the complete imported tables without an incremental refresh policy. Schedule it after the required gold loads finish.
