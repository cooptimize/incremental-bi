---
title: Watermark strategy
layer: cross-cutting
status: working
related:
  - Cross-Cutting/Delete Detection Strategies.md
  - Gold/Dimension Patterns/Dimension Incremental Load.md
  - Gold/Fact Patterns/Fact Partition Rebuild.md
---

A watermark records how far a load has processed its change signal. On the next run, the load rereads from that boundary, applies the changes, and advances the watermark only after success.

The boundary is useful only if the timestamp covers the changes you care about. A posting date selects a business period; it does not tell you when a row was last exported or changed.

## Choose the signal before the boundary

For lake-fed loads, use the export's `SinkModifiedOn` where it provides the required change signal. `modifiedDateTime` and export timestamps describe different stages of the pipeline. Verify the behavior of the field in the configured export rather than treating the names as interchangeable.

For joined output, include the contributing tables. A customer name in `DirPartyTable` can change without a matching change to `CustTable`. The [dimension pattern](../Gold/Dimension%20Patterns/Dimension%20Incremental%20Load.md) uses `VALUES` and `MAX` to build `SinkMaxModifiedOn` for each joined row.

A file timestamp can identify a file to reload when no row-level signal exists. Treat that as file-level work: it does not identify which rows changed or disappeared.

## Store progress for the load

Use a control row per independently loaded target and scope. Two targets reading the same source must not advance each other's progress. This SQL Server-style example assumes `Customer` names one complete load scope:

```sql
CREATE TABLE control.watermarks
(
      table_name VARCHAR(255) PRIMARY KEY
     ,last_successful_watermark DATETIME2(7)
);
```

Initialize the control row during the first full load. Subsequent runs read the saved value and capture an upper boundary before querying:

```sql
SELECT @LastWatermark = wm.last_successful_watermark
FROM control.watermarks AS wm
WHERE wm.table_name = 'Customer';

SET @RunStart = SYSUTCDATETIME();
```

The following excerpt uses a five-minute overlap to replay rows near the boundary. That interval is an example, not a guarantee against arbitrary arrival delays:

```sql
SELECT
      ct.DataAreaId
     ,ct.AccountNum
     ,ct.CustGroup
     ,ct.SinkModifiedOn
FROM silver.CustTable AS ct
WHERE ct.SinkModifiedOn >= DATEADD(MINUTE, -5, @LastWatermark)
    AND ct.SinkModifiedOn < @RunStart;
```

Apply these rows idempotently, so replay updates the same keys rather than inserting duplicates. After the target work succeeds, record the upper boundary as part of the same committed load state:

```sql
UPDATE wm
SET last_successful_watermark = @RunStart
FROM control.watermarks AS wm
WHERE wm.table_name = 'Customer';
```

A failed load keeps the previous boundary. If target data and control state cannot commit together, recovery must safely replay the interval. Serialize runs that share the same control row.

## What the boundary cannot prove

Capturing run start avoids advancing past the entire duration of a query, but it doesn't guarantee that all earlier timestamps were visible. Clock differences, delayed exports, and timestamps assigned before commit can still place late rows behind the boundary. Use a source-issued checkpoint when available; otherwise measure delay and reconcile beyond the overlap.

Deletes need an explicit event, a retained flag, or a comparison against complete state. Once a row is gone, its old timestamp cannot return it. See [delete detection](Delete%20Detection%20Strategies.md).

Related tables can also arrive at different times. A watermark or partition rebuild does not make them a consistent snapshot. Coordinate source readiness and check for rows lost through joins. If the timestamp never moves for a relevant change, use [the diagnosis guide](../Decisions/I%20Can%27t%20Trust%20modifiedDateTime.md) and reconcile without relying on that signal.
