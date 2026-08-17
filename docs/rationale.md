# Proposition ledger rationale for the folio-insights v2.0 review

## Review question

folio-insights v2.0 has a 15-field shard envelope, including six frozen
identity fields and five discriminated shard subtypes. Its envelope redesign is
on hold while reviewers decide whether the shared Proposition model is a sound
foundation. This document recommends adopting the identity boundary now while
keeping the interpretive vocabulary revisable through the gold-corpus ladder.

## Why a double-entry ledger

A legal proposition has two analytically different sides: someone asserts it,
and someone or some institution validates, rejects, declines, or has not yet
acted on it. Collapsing those sides into a single speaker or status loses the
most useful information. The ledger makes `asserter` and `validator` separate
references and records the adjudicative result in `disposition`.

The balanced case—party asserts, court rules—is easy. The schema earns its keep
on unbalanced entries:

| Legal state | Asserting side | Validating side | Ledger meaning |
|---|---|---|---|
| Litigated proposition | party | court, `ruled` | An adversarial claim received adjudication. |
| Open position | party | `null` | A claim exists, but no validator has acted. |
| Stipulation | `both_parties` | `null` or court, `pro_forma` | Agreement does not require a merits ruling; a court may merely formalize it. |
| Arguendo assumption | court with `assumed: true` | court, `declined` | The court assumes a premise while declining to decide it. |
| Judicial notice | `null` | court | The court validates a proposition without an adversarial asserter. |

`null` is therefore data, not absence. It expresses a legally meaningful empty
side. Downstream systems must preserve it and must not fabricate an actor to
make a row look balanced.

## Why one shared library

folio-enrich extracts and annotates propositions; folio-insights stores and
analyzes shards. If each repository owns a proposition vocabulary, their types,
roles, edge meanings, defaults, and migrations will drift. A seemingly valid
export could then change meaning at the repository boundary.

The carve-out puts the typed ledger and interchange record in
`folio-propositions`. folio-enrich and folio-insights consume the same model.
The five insights shard subtypes become configurations or application-level
composites of that shared model, as recorded in the
[shard mapping](shard-mapping.md), rather than a second ontology.

## Why axiom is an earned status

An axiom is not born as a different kind of textual object. It begins as a
proposition and earns a lifecycle status through use and review. `AxiomStatus`
therefore records `proposition`, `promoted`, `demoted`, or `superseded` on the
same `Proposition` identity. Promotion does not discard provenance; demotion
and supersession remain expressible without converting between unrelated
types. Phase A does not exercise this lifecycle, so the field is expected to
remain design-only throughout Phase A.

## Why taxonomy augmentation is tag-then-batch

The working taxonomy is intentionally closed during an annotation cycle.
When an annotator encounters a candidate outside it, the annotator preserves a
verbatim free-text `proposition_type` and sets `is_new_type: true`. That tag is
evidence for later review, not a live schema mutation.

After the cycle, reviewers batch the tags, inspect duplicates and forced fits,
and decide whether each tag is promoted, merged, or rejected. Accepted changes
ship as a versioned schema revision with a migration before the next cycle.
This keeps every record within one cycle comparable and reproducible. Live
taxonomy edits would make early and late annotations in the same opinion obey
different rules.

## Identity-boundary adoption split

The review should distinguish stable reference mechanics from interpretive
choices. folio-insights can freeze the identity boundary in storage now without
pretending that one unrun annotation cycle has validated the ontology.

### Adopt into frozen storage now

- Proposition and document identifiers: `Proposition.id`,
  `PropositionDocumentRecord.document_id`, and individual/authority reference
  identifiers.
- Document binding through one `PropositionDocumentRecord` per source document.
- `schema_version` stamps on both propositions and document records.
- Span mechanics: the optional but atomic `start_char`, `end_char`, and `text`
  group, including nonnegative offsets and ordered boundaries.
- Reference containers: asserter, validator, citation-edge, triple, generator,
  and document-metadata locations, while allowing their controlled vocabularies
  to evolve.

These fields answer “which thing, in which document and span, under which
schema version?” Stable answers are prerequisites for annotation comparison,
migration, and cross-repository interchange. Freezing their storage positions
does not freeze the semantic vocabulary carried inside them.

### Keep revisable through the gold-corpus ladder

- `WORKING_TAXONOMY` proposition-type values.
- `ActorRole`, `AdjudicationMode`, and `Disposition` vocabularies.
- `CitationEdgeType` vocabulary.
- `SHAPES`, including role expectations and application-level thread
  descriptors.

These are empirical classifications. They should remain revisable until the
gold-corpus ladder—approximately five or six opinions across court levels—has
tested them against changes in tribunal, posture, writing style, and authority
structure. Revision should occur only between cycles, with an explicit schema
version and migration where stored meaning changes.

## What would falsify this schema

The schema should be revised, not defended by increasingly creative encoding,
if annotation produces any of the following patterns:

- Repeated legally relevant spans cannot be classified, even after the
  tag-then-batch process.
- Annotators repeatedly choose a known type, role, edge, or shape only because
  it is the least-wrong option; forced-fit rates cluster by opinion or court
  level.
- A legally coherent ledger row cannot be constructed without inventing an
  asserter, validator, adjudication mode, or disposition.
- One span requires multiple incompatible ledger rows and the model has no
  lossless way to preserve their relationship.
- Span boundaries or document/reference identities cannot round-trip from
  folio-enrich through folio-insights without ambiguity.

Those outcomes would falsify either the vocabulary, the ledger structure, or
the identity boundary. The cycle learnings record must say which one, and the
next cycle must run against the revised, migrated schema.
