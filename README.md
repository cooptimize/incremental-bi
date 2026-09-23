# ERP Analytics Incrementals

**Agents:** Read [AGENTS.md](AGENTS.md) before editing this repository.

A practitioner's reference for incremental loading in ERP analytics, with examples grounded in Microsoft Dynamics 365 Finance & Operations. The primary stack is F&O → Synapse/Fabric Link → bronze/silver/gold → a Power BI semantic model.

The library explores the decisions that make incremental pipelines difficult to operate: discovering deletions, choosing reliable watermarks, rebuilding joined facts, preserving dimension keys, and keeping imported reports in sync. Articles explain how patterns work and where their assumptions break, so developers can choose an approach that fits their data and refresh requirements.

This is a connected reference for developers who already know SQL, F&O, and data pipelines. It contains implementation patterns rather than developer standards, and its recommendations depend on the source, reporting requirements, and available load window.

## Start here

- [Overview](Overview.md) explains how incremental loading differs at each layer and how the choices connect.
- [Pattern index](Pattern%20Index.md) lists the patterns, their intended uses, and their maturity.
- [Why deletions are hard](Why%20Deletions%20Are%20Hard.md) follows the deletion problem from extraction through reporting.

## Browse by layer

- [Bronze](Bronze/) — full extraction, change feeds, and partition-based extraction.
- [Silver](Silver/) — conforming loads, hard deletes, and partition change tracking.
- [Gold](Gold/) — dimension loads, fact rebuilds, and audit and repair.
- [Semantic model](Semantic%20Model/) — full and incremental Power BI refresh.
- [Cross-cutting](Cross-Cutting/) — watermarks, delete detection, partition keys, and the shared `@ForceUpdate` contract.
- [Decisions](Decisions/) — diagnosing unreliable change detection and choosing a fallback.
- [Snapshots](Snapshots/) — period snapshots and retained change history, starting with what the source already provides.

## Maturity and scope

This is a living reference. `draft` means content is incomplete; `working` means the approach is written but still needs validation against a real implementation; `stable` means it has been validated. Some articles do not yet carry a status. Neither a missing label nor a polished explanation establishes that an example has been tested.

Current coverage focuses on imported semantic models. DirectQuery and Direct Lake remain outside the developed patterns, snapshot articles are exploratory, and performance arguments are not backed by recorded environment benchmarks. The pattern index records additional gaps.

## Contributing

Contributions are most useful when they bring a concrete case: the source and target involved, the change that was missed, the expected result, and what the implementation actually did. Open an issue for a missing or incorrect pattern, or propose an article change with enough context to assess its assumptions.

Follow [STYLE.md](STYLE.md) when writing. Explain the reasoning and practical consequences, keep unresolved details visible, and distinguish an editorial improvement from a validated technical correction.

SQL examples follow [Cooptimize Standards](https://github.com/cooptimize/coop-standards). Keep a checkout beside this repository as `../coop-standards/`; its [README](../coop-standards/README.md) links the SQL and technology standards. The standards stay in that library rather than being copied here. This project’s STYLE.md governs article prose.

The articles are maintained as Markdown with an Obsidian Publish theme in [publish.css](publish.css). The repository is licensed under the [MIT License](LICENSE).
