---
title: Why deletions are hard
status: working
---

# Why deletions are hard

## The simple version of incremental

The appeal of incremental loading is obvious. A table has ten million rows.
Yesterday you loaded all of them. Today, five hundred changed. Why reload ten
million rows to capture five hundred changes?

If data only ever arrived or updated, incremental loading would be
straightforward. Find what changed since the last run, load it, done. The
watermark pattern — query by modified date, pull the delta — works cleanly.
Performance is good. Complexity is low. Everyone is happy.

Deletions break this entirely.

---

## What a deletion looks like from the pipeline's perspective

When a record is deleted from a source system, nothing arrives in your pipeline.
There is no event, no tombstone, no signal. The record is simply absent from
the next pull. If you're doing incremental loads — pulling only what changed —
you will never pull a record that no longer exists. You won't know it's gone.

This is the fundamental problem. Incremental loading is built around the idea
that you ask "what changed?" and the source tells you. But most source systems
don't answer the question "what was deleted?" They just stop returning the
record. An absence is not a message.

Full loads sidestep this: if you reload everything every time, missing records
are detectable by comparison. But full loads are expensive, and the entire
motivation for incremental design is to avoid them. The moment you commit to
incremental loading, deletion detection becomes a first-class design problem —
not an afterthought.

---

## This is a correctness problem, not a performance problem

It's worth being precise about what kind of problem this is.

Most "big data" engineering problems are performance problems. Data volumes are
large, queries are slow, pipelines take too long. The solutions — partitioning,
parallelism, columnar storage, incremental loads — are engineering solutions to
throughput constraints. They make things faster or cheaper.

Deletion detection is not a performance problem. It is a **correctness**
problem. A pipeline that misses deletions produces wrong answers. And crucially,
it produces wrong answers silently. The reports balance. The numbers look
reasonable. There's no error. No alert fires. The data looks fine.

The only way to discover the problem is to compare your pipeline's output
against the source — which requires either a full reload or a separate
reconciliation process. Neither of which you can do continuously at scale.

This means deletion errors accumulate over time, quietly, until someone notices
that a number doesn't add up and starts investigating. By then the drift can be
months old and affect multiple downstream systems.

No amount of partitioning or parallelism fixes this. The problem isn't
throughput. It's that a class of source events is architecturally invisible to
your pipeline.

---

## Why it's hard at every layer

Deletions don't become someone else's problem once you've solved them at bronze.
Each layer in the pipeline has its own deletion problem.

### Bronze

Bronze is where the source data lands. If the source doesn't signal deletes,
bronze has no way to know a record is gone short of a full reload and
comparison. The options at bronze — full load, CDC feed, partition-based
incremental — have fundamentally different deletion visibility. A CDC feed
(Fabric Link, Synapse Link) will signal deletes explicitly. A partition-based
incremental won't — records deleted outside the reload window are invisible.
Full load makes deletes detectable but at the cost of reloading everything.

The bronze choice constrains everything downstream.

### Silver

Even if bronze correctly captures a delete signal, silver has to propagate it.
This sounds simple but isn't. Silver often maintains history — versioned rows with effective date ranges, snapshots, audit trails. A deletion at the source doesn't necessarily
mean a deletion in silver. Does a deleted source record get hard-deleted from
silver? Soft-deleted? End-dated? The answer depends on business requirements
and affects every downstream consumer. Silver also has to handle the case where
a delete arrives out of order — after subsequent records that assumed the
deleted record still existed.

### Gold

Gold maintains a dimensional model. Dimensions have surrogate keys. Facts
reference those surrogate keys. If a dimension record is deleted — a customer,
a product, a cost center — what happens to the facts that reference it? You
cannot simply delete the dimension row without orphaning fact records. You
cannot leave it in place without misrepresenting the current state of the
business. The options (soft delete, retain with a flag, end-date the historical dimension row)
all have downstream implications for report correctness.

Deleted facts are a different problem. A deleted transaction means historical
aggregates are wrong. Period totals, running balances, aging buckets — anything
calculated over a window of facts needs to be recalculated when a fact is
removed. Incremental aggregate recalculation assumes facts arrive but doesn't
assume they disappear.

### Semantic model

Power BI incremental refresh is designed around the assumption that data within
a closed historical partition is stable. A record deleted from a closed
partition will not be reflected in the semantic model until that partition is
refreshed — which incremental refresh by design avoids doing. This means
deletions in historical data are systematically invisible to Power BI
incremental refresh unless the refresh window is explicitly sized to cover
the at-risk period. There is no native mechanism for deletion propagation into
a historical imported partition.

---

## Where deletions happen that you wouldn't expect

The obvious candidates are operational records: orders get cancelled, customers
get merged, inventory adjustments get reversed. These are expected.

The non-obvious ones are more dangerous precisely because they're unexpected.

**General ledger transactions in F&O** can be deleted under certain conditions.
The general ledger is often treated as an append-only ledger — the accounting
model assumes you correct errors with offsetting entries, not deletions. In
practice, F&O allows deletion posted transactions (opening and closing balances). A pipeline designed on the assumption that GL is
append-only will silently accumulate deleted transactions in bronze indefinitely.

**Dimension records** in reference data — chart of accounts entries, vendor
records, project codes — are deleted more often than people expect, usually
through data cleanup or entity merges. These deletions don't look dramatic in
the source but they corrupt surrogate key relationships in gold silently.

**Backdated corrections** are a related problem. Strictly speaking not a
deletion, but the effect is similar: a transaction that existed in a prior
period is voided or reversed. If your pipeline only looks forward, the original
transaction stays in your pipeline indefinitely while the source has moved on.

---

## Why this is the first constraint on incremental design

When teams start designing for incremental loading, the conversation usually
begins with volume and performance. How big is the table? How often does it
change? What's the watermark field? These are the right questions if additions
and updates are all you're dealing with.

The deletion question needs to come first. Or more precisely: before you
commit to an incremental design, you need an honest answer to "what happens
when a record is deleted from this source?"

The possible answers are:
- The source signals it explicitly (CDC, soft delete flag) — incremental is viable
- The source doesn't signal it, but business rules guarantee it never happens — incremental is viable with documented assumptions
- The source doesn't signal it, and it can happen — you need a reconciliation strategy or you need to reconsider full load

That last case is more common than people expect, and the "business rules
guarantee it never happens" case is more fragile than it looks. Business rules
change. Edge cases exist. The GL example above exists precisely because someone
assumed a ledger was append-only and was wrong.

The pattern of designing incrementally and discovering deletion drift later is
a well-worn path. The discovery usually happens during an audit, a
reconciliation, or a business question that doesn't add up. At that point the
pipeline is in production, downstream systems depend on it, and fixing it
requires either a full historical reload or a careful incremental correction —
neither of which is cheap.

Design for deletions first. Everything else is easier to add later.
