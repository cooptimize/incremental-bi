# Pattern index

Choose a pattern by the behavior of the source and the result you need to maintain. [Overview](Overview.md) explains how the layers connect; [why deletions are hard](Why%20Deletions%20Are%20Hard.md) follows one of the main failure cases through them.

Status reflects article metadata: `draft` is incomplete, `working` needs implementation validation, and `stable` has been validated. **Unlabelled** means no status is recorded; it does not imply readiness.

## Cross-cutting decisions

| Article | Use it to understand | Status |
|---|---|---|
| [Delete detection](Cross-Cutting/Delete%20Detection%20Strategies.md) | Explicit signals, complete key comparisons, and retention choices. | working |
| [Watermark strategy](Cross-Cutting/Watermark%20Strategy.md) | Load boundaries, overlap, and successful checkpointing. | working |
| [Partition keys](Cross-Cutting/Partition%20Keys.md) | Stable replacement boundaries and extraction-cohort limits. | Unlabelled |
| [@ForceUpdate](Cross-Cutting/ForceUpdate%20Contract.md) | The shared interface for routine loads, reconciliation, and rebuilds. | Unlabelled |
| [I can't trust modifiedDateTime](Decisions/I%20Can%27t%20Trust%20modifiedDateTime.md) | Where to investigate a missed update before adding another mechanism. | working |

## Bronze: extraction

The key choice is what the source can reliably expose.

| Article | Approach | Status |
|---|---|---|
| [Full load](Bronze/Full%20Load.md) | Publish a complete extraction after it succeeds. | draft |
| [CDC and change feed](Bronze/CDC%20and%20Change%20Feed.md) | Consume explicit change events with checkpoint and replay handling. | draft |
| [Partition-based incremental](Bronze/Partition-Based%20Incremental.md) | Replace selected date slices and reconcile outside the window. | draft |

## Silver: conformed current state

| Article | Approach | Status |
|---|---|---|
| [Full load](Silver/Full%20Load.md) | Replace the conformed table and publish matching tracker state. | working |
| [Incremental with hard delete](Silver/Incremental%20with%20Hard%20Delete.md) | Maintain current rows while removing confirmed deletions. | working |
| [Change tracking partitions](Silver/Change%20Tracking%20Partitions.md) | Summarize counts and timestamps for downstream load selection. | working |

## Gold: dimensions and facts

Start with a full fact load when it fits the window. If it doesn't, choose a replacement strategy based on how transactions continue to change.

| Article | Approach | Status |
|---|---|---|
| [Dimension incremental load](Gold/Dimension%20Patterns/Dimension%20Incremental%20Load.md) | Preserve surrogate keys and combine source timestamps into `SinkMaxModifiedOn`. | Unlabelled |
| [Fact full load](Gold/Fact%20Patterns/Fact%20Full%20Load.md) | Recompute the complete result from current inputs. | Unlabelled |
| [Fact partition rebuild](Gold/Fact%20Patterns/Fact%20Partition%20Rebuild.md) | Replace partitions selected by changed source state or reconciliation. | Unlabelled |
| [Fact open/settled rebuild](Gold/Fact%20Patterns/Fact%20Open-Settled%20Rebuild.md) | Rebuild open transactions and reconsider changed settled ones. | Unlabelled |
| [Fact audit and repair](Gold/Fact%20Audit%20and%20Repair.md) | Compare expected and loaded results independently of routine selection. | Unlabelled |
| [No-load direct semantic](Gold/No-Load%20Direct%20Semantic.md) | Assess when silver views are sufficient and when persistence helps. | Unlabelled |

## Snapshots

Check whether the source already retains the history you need before capturing it again.

| Article | Approach | Status |
|---|---|---|
| [Snapshots overview](Snapshots/Snapshots%20Overview.md) | Distinguish business-effective history from observed state. | draft |
| [Period snapshot](Snapshots/Period%20Snapshot.md) | Capture positions at defined intervals. | draft |
| [Full history snapshot](Snapshots/Full%20History%20Snapshot.md) | Preserve each version the pipeline observes. | draft |

## Semantic model

| Article | Approach | Status |
|---|---|---|
| [Full load](Semantic%20Model/Full%20Load.md) | Reload imported data after gold is ready. | working |
| [Incremental refresh with deletions](Semantic%20Model/Power%20BI%20Incremental%20Refresh%20with%20Deletions.md) | Revisit the imported partitions affected by updates and removals. | working |

## Remaining implementation gaps

The bronze and snapshot drafts still need tested end-to-end examples. The Power BI article explains the partition-refresh design but does not yet implement its controller. Row-hash comparison and schema-drift handling do not have standalone implementations here.

DirectQuery and Direct Lake coverage, measured performance results, and validation of export-specific timestamp behavior remain outstanding. SQL examples identify their assumed platform and conformed inputs; formatting checks are not execution tests.
