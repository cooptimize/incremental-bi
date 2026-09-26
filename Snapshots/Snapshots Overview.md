---
title: Snapshots — overview
layer: snapshots
status: draft
related:
---
Sometimes the report needs an answer the current data can no longer provide: what was our inventory at month end, or who was assigned to a project before its manager changed? Keeping only the latest values loses those answers.

Before capturing more data, check whether the source already keeps the history you need. If it does, use that history. Otherwise, decide whether the report needs a position at regular intervals or a record of changes as we observe them.

# Capture a position at an interval

A daily inventory or month-end aging snapshot stores the result alongside the date it represents. For an inventory report, that might mean one row per company, item, and warehouse each day. Store the detail the report needs rather than copying every source field.

If the same capture runs twice, replace or recognize the existing snapshot so a retry doesn't double the reported balance. Be clear about the date it represents: a month-end job running after midnight may still be capturing the previous month's position.

## What should happen when last month is corrected?

Suppose a correction changes March after you've saved its snapshot. Should the report show March as originally reported, March with the correction, or both? That reporting choice determines whether to keep, replace, or version the snapshot.

A transaction deleted today can still belong in an earlier snapshot if the purpose is to preserve what was reported then.

# Retain observed versions

If the report needs to follow changes between snapshot dates, keep a new version when the load notices a relevant change. For example, when a project's manager changes, end the previous version's date range and start a new version with the new manager. Keep the record key so the versions can be connected, and save both changes together.

## When it changed and when we noticed may differ

A manager correction received today might apply from the start of last month. Recording today's load time tells us when we saw it, not when it took effect. Use the source's effective dates and history when they answer the reporting question; don't treat observation time as the business date.

A daily read also can't see every change made during the day. If a value changes twice and returns to its original value before the next read, both changes are invisible. A reliable event feed can provide more detail, but saving versions can't recover changes the input never supplied.

# Keep the history the report needs

Copying ten million rows every day adds about 3.65 billion rows a year. Choose how often to capture, what detail to retain, and how long to keep it based on the report's needs. Saving only changed versions may use less space, but adds change detection and date-range logic to the queries.
