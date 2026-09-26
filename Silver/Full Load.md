---
title: Full load
layer: silver
status: working
related:
  - Silver/Incremental with Hard Delete.md
  - Bronze/Full Load.md
---
When the source doesn't reliably tell us what changed or was deleted, use Copy Data to replace the entire silver table from bronze. Clear the destination and copy all current rows. Records that disappeared from bronze then disappear from silver too.

This avoids maintaining change detection and a separate deletion process. Copying every row takes more work, but it's often the simpler choice when incremental signals are missing or the table is small enough.

The copy must replace the previous contents, rather than append or upsert into them; an upsert would leave deleted records behind. Use complete bronze data and exclude any rows marked deleted by the export.

Map the current pipeline run's UTC timestamp to [SinkSilverModifiedOn](Incremental%20with%20Hard%20Delete.md#sinksilvermodifiedon) on the copied rows. Gold can then see that silver reloaded them, though this means every copied row gets a new signal. Deletions still need to be handled by the chosen gold strategy.
