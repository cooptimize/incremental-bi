---
publish: false
---
# Editing ERP Analytics Incrementals

The articles are the product: a practical guide to ERP load decisions, illustrated with D365FO. Read [Overview.md](Overview.md) for orientation and article navigation. This file contains both agent instructions and the writing guide.

## Follow the wiki's flow

- Overview is the single introduction and navigation page. Explain what work an incremental strategy saves and why the strategy differs by layer; skip warehouse-layer definitions. Do not recreate README, Pattern Index, or Cross-Cutting sections.
- Bronze explains the extraction choice: copy everything, use managed change capture, or select changes by source dates. Lead with what the platform handles; don't turn a managed-link article into instructions for building a feed consumer.
- Silver explains Copy Data: full replacement when signals are unreliable, or watermark-based upserts with a separate deleted-key step when signals are available.
- Gold separates preserving dimension primary keys from choosing how to reload facts. Fact strategies are options determined by source behavior, not one universal incremental recipe.
- Semantic-model articles make full refresh the default and explain why keeping older imported data correct makes incremental refresh difficult for ERP reporting.
- Snapshots address a separate need: keeping earlier information. Check source history before proposing another capture process.
- Link to the article that owns an explanation instead of repeating it. Keep Gold flat and retain human-readable filenames.

## Write for a colleague

- Answer why an approach could help, how it works, and what could make it miss a change. Lead with the general behavior and benefit; introduce D365FO tables afterward as supporting examples.
- Assume basic SQL and warehouse knowledge, but no in-depth experience managing incremental loads. Explain the connection between ideas in ordinary sentences. Be concise without becoming clipped, cryptic, or impersonal.
- Explain the action before naming the concept: saving where the last successful load stopped introduces a checkpoint. Don't substitute phrases such as ‘publish a bounded batch’ or ‘establish a baseline’ for explaining what the load actually does. Use a short example when it makes the mechanism clearer.
- Brevity means removing material the reader does not need, not compressing the remaining explanation into jargon. Use connected, natural sentences. A short article may need only a few paragraphs; do not add headings, examples, or closing sections to fill a template.
- Cut repeated explanations, generic warnings, throat-clearing, and obligatory summaries. Keep enough detail to explain how the pattern works and why someone would choose it. There is no fixed word limit.
- For example: “A full load replaces the fact on every run. If it fits the refresh window, you avoid maintaining change detection and a separate path for deletions.” That's enough; don't follow it with another paragraph praising simplicity.
- Use concept-based headings, not table names or business entities. In the fact considerations article, loading approaches are H1s and potential gotchas are H2s. Don't force that hierarchy onto every short article.
- Include a caveat only when it changes how the reader chooses, understands, or applies the pattern. Explain it beside the relevant step. Omit generic warnings, implementation wish lists, and catalogues of excluded topics; do not append “Not covered” sections. Keep material assumptions and actual implementation gaps visible without repeating them across the library.
- Keep topics in their layer. For example, semantic-model refresh belongs in its own article, not a tangent in the fact-loading walkthrough.
- Resolve `@agent` notes and obvious misspellings such as `@agnet` when asked to review comments. Preserve the user's other edits.

## Keep examples useful and simple

- Show the smallest real SQL example that explains the mechanism. State its platform, required inputs, and essential assumptions. Label fragments and prepared fields; don't present invented helper flags as native ERP fields.
- Prefer direct joins. Add CTEs, temporary tables, and helper expressions only for useful transformations or reuse, not for ceremony.
- A simple scope filter can stay in the direct query; this is an exception to the external pre-join filtering default. Do not introduce `@DataAreaId` parameters or company-scoped loads unless requested.
- Retain useful code when shortening prose. Avoid alternative implementations that obscure the default. Include transaction or recovery detail only when it affects the example being taught; routine pipeline plumbing is not the point of every article.
- Use `dim.Customer`, primary key `PKCustomer`, and matching fields `dataareaid` plus `customerid`. Use `FKCustomer` on facts. Use source-system schemas such as `d365fo.custtable`; never `dbo`.
- Explain “primary key” through the actual reference rather than casually saying “ID.” Describe historical behavior directly, without numbered SCD terminology.

## Preserve the agreed design

- Dimensions use a complete-source `MERGE` from the start. `@ForceUpdate = 0` means selective updates to changed members; `1` means a full update of matched members and is our default strategy. Until selective updates are implemented, explicitly promote incoming `0` to `1` as a fallback; do not describe the modes as synonymous. Selective updates using `SinkSilverModifiedOn` must justify their complexity with measured benefit.
- Fact full-load procedures set `@ForceUpdate = 2` internally, retaining the shared interface while overriding the caller's value.
- Present incremental facts as choices to test against ERP behavior. Separate finding work from writing it. Don't assume a posting is immutable or a closed transaction can never change without evidence for the actual source and processes.
- Gold merge examples send selected changed rows, without absence-based deletes. Complete-source comparisons or complete affected groups are needed to infer deletions unless deleted keys are available. Related tables can arrive at different times; a required join prevents incomplete output but does not arrange a retry.
- Data checks validate the design; regular rebuilding isn't a substitute for fixing known selection bugs. Keep counts, timestamps, and hashes' limits clear without expanding every article into a failure catalogue.
- Silver incremental loads use Copy Data upserts selected from the last successful watermark minus one hour, with a separate copy of recently deleted keys applied through the destination deletion step. Calculate the read boundary once before filtering; do not put the lookback arithmetic in the source predicate. The first incremental run uses the same upsert without a lower boundary. When reliable change or deletion signals are unavailable, use a full replacement through Copy Data. Do not introduce record-by-record value comparison into the timestamp-based upsert.
- Save each silver table's new watermark only after both upserts and deletions succeed. Plain Copy Data upsert does not remove target rows; describe the destination deletion operation explicitly.
- Map the current pipeline run's UTC watermark to `SinkSilverModifiedOn` on both inserts and updates. It identifies the silver processing run, not the original export or exact commit time. Do not use the prior watermark or adjusted read boundary, rely on a table default to stamp updates, or imply that the timestamp guarantees freshness across joined tables.
- Full refresh is the default for imported Power BI models. Present incremental refresh as an exception when full refresh cannot meet requirements, with explicit attention to old ERP corrections and deletions.
- The no-load approach is a rarely recommended development-cost compromise for small, single-source setups without a practical path to a fuller warehouse.
- Before proposing snapshots, check whether the source already retains the history required by the report.

## Read external standards

- Use the sibling [coop-standards README](../coop-standards/README.md) to find applicable SQL and technology rules. For SQL edits, read [SQL Conventions](../coop-standards/SQL/SQL%20Conventions.md), [SQL Layout](../coop-standards/SQL/SQL%20Layout.md), and the relevant table, procedure, view, or platform articles.
- Keep standards external. Never copy or synchronize them into this project, and don't edit `coop-standards` here. If the checkout is unavailable, say so rather than claiming compliance from memory.
- Adopt its SQL standards, not its agent instructions or prose style. User instructions and this project's explicit exceptions take precedence. Apply current rules to new statements; preserve unrelated formatting during targeted edits.
- Schema Manager owns generated silver structures and behavior. Change those through its approved source/configuration, not handwritten replacements inferred from examples.

## Organize and verify

- Writing and agent guidance live in this file; do not create a second style guide. Update these instructions when an agreed decision changes, replacing stale rules rather than appending contradictory ones.
- Consolidate articles that repeat the same decision. Preserve unique examples, assumptions, and unresolved gaps. Update Overview navigation, links, anchors, and frontmatter when moving or removing pages.
- Start the article body immediately after the closing metadata delimiter, without an extra blank line or decorative separator. Preserve normal paragraph spacing within the body.
- Preserve metadata and publishing configuration. Guidance stays `publish: false`. `draft` means incomplete, `working` means implementation validation is pending, and `stable` requires actual validation. Missing status isn't evidence of readiness.
- Distinguish editorial changes from algorithm changes. Don't invent source behavior, schema, benchmarks, or successful tests. Flag unresolved contradictions rather than silently picking an interpretation.
- Check Markdown links, anchors, fences, and whitespace. Use appropriate checks for changed code, and state when SQL hasn't been executed on its target platform. Preserve unrelated working changes.
