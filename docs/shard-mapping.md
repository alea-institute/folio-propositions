# folio-insights shard mapping

This document maps the five folio-insights v2.0 shard subtypes to the public
`folio-propositions` API at `SCHEMA_VERSION` 3. The shard-envelope redesign is
on hold pending review. Gold annotation cycle 1 (Palsgraf, AI-annotated and
Damien-delegated) is complete; the evidence statuses below reflect that cycle.
It promoted `cited-authority proposition`, `hypothetical illustration`, and
`policy proposition` into the working taxonomy.

The examples intentionally contain only fields accepted by `Proposition` or
`PropositionDocumentRecord`. Application-level relationships are described
outside those model payloads.

## `simple_assertion`

A `simple_assertion` is a balanced litigation-ledger entry. `asserter` is
present, `validator` is present with `mode: "ruled"`, and `disposition` is
`"accepted"`. The example uses the registered `"litigation"` shape and the
closed taxonomy value `"Legal Proposition"`.

```json
{
  "id": "prop-simple-1",
  "schema_version": 3,
  "start_char": 120,
  "end_char": 184,
  "text": "The limitations period began when the judgment became final.",
  "proposition_type": "Legal Proposition",
  "is_new_type": false,
  "asserter": {
    "role": "appellant",
    "individual_id": "party-appellant",
    "name": "Appellant",
    "assumed": false
  },
  "validator": {
    "role": "court",
    "individual_id": "court-panel",
    "name": "Court of Appeals",
    "mode": "ruled"
  },
  "disposition": "accepted",
  "citation_edges": [],
  "triple_ids": ["triple-101"],
  "shape": "litigation",
  "axiom_status": "proposition"
}
```

**Status:** `annotation-tested (cycle 1: Palsgraf, AI-annotated,
Damien-delegated)` for its core balanced proposition fields.

## `hypothesis`

A `hypothesis` is a generated open position: `asserter.role` is `"system"`,
`validator` is `null`, and `disposition` is `"unresolved"`. `null` records that
no validator has acted; it is not missing extraction data.

```json
{
  "id": "prop-hypothesis-1",
  "schema_version": 3,
  "start_char": null,
  "end_char": null,
  "text": null,
  "proposition_type": "Factual Statement",
  "is_new_type": false,
  "asserter": {
    "role": "system",
    "individual_id": null,
    "name": "folio-enrich pre-selector",
    "assumed": false
  },
  "validator": null,
  "disposition": "unresolved",
  "citation_edges": [],
  "triple_ids": [],
  "shape": "disputatio",
  "axiom_status": "proposition"
}
```

**Status:** `design-only` (generated `disputatio` hypothesis not exercised).
Constructed propositions inside case hypotheticals instead map to the promoted
`hypothetical illustration` type.

## `gloss`

A `gloss` uses an asserter with role `"secondary_source"`. A `CitationEdge`
with `edge_type` `"interprets"` (or, when appropriate, `"elaborates"`) points
to the individual identifier of the glossed authority.

```json
{
  "id": "prop-gloss-1",
  "schema_version": 3,
  "start_char": 900,
  "end_char": 957,
  "text": "The treatise reads Example as limited to final judgments.",
  "proposition_type": "cited-authority proposition",
  "is_new_type": false,
  "asserter": {
    "role": "secondary_source",
    "individual_id": "source-treatise-1",
    "name": "Example Treatise",
    "assumed": false
  },
  "validator": null,
  "disposition": "unresolved",
  "citation_edges": [
    {
      "edge_type": "interprets",
      "authority_individual_id": "authority-example-v-example",
      "authority_text": "Example v. Example"
    }
  ],
  "triple_ids": [],
  "shape": "disputatio",
  "axiom_status": "proposition"
}
```

**Status:** `annotation-tested (cycle 1: Palsgraf, AI-annotated,
Damien-delegated)` for secondary-source attribution and the natural mapping to
`cited-authority proposition`; hand-added `CitationEdge` semantics remain
design-only (only tool-attached edges were exercised).

## `disputed_proposition`

A `disputed_proposition` is a thread of library `Proposition` nodes in the
`"disputatio"` shape: an *utrum* question, one or more objections, and a
*respondeo*. The thread and its stance links are application-level structures;
there is no stance-edge model in this library. Each node remains an ordinary
`Proposition`. In this valid interchange example, folio-insights carries the
thread roles and links in the open `document_metadata` mapping.

```json
{
  "document_id": "opinion-example-1",
  "schema_version": 3,
  "propositions": [
    {
      "id": "utrum-1",
      "proposition_type": "Legal Proposition",
      "asserter": {"role": "system", "name": "Thread constructor"},
      "validator": null,
      "disposition": "unresolved",
      "shape": "disputatio"
    },
    {
      "id": "objection-1",
      "proposition_type": "Legal Proposition",
      "asserter": {"role": "appellant", "name": "Appellant"},
      "validator": null,
      "disposition": "unresolved",
      "shape": "disputatio"
    },
    {
      "id": "respondeo-1",
      "proposition_type": "Judicial Legal Conclusion",
      "asserter": {"role": "court", "name": "Court of Appeals"},
      "validator": {"role": "court", "name": "Court of Appeals", "mode": "ruled"},
      "disposition": "accepted",
      "shape": "disputatio"
    }
  ],
  "document_metadata": {
    "disputatio_threads": [
      {
        "utrum": "utrum-1",
        "objections": ["objection-1"],
        "respondeo": "respondeo-1",
        "stance_links": [
          {"from": "objection-1", "to": "utrum-1", "stance": "objects"},
          {"from": "respondeo-1", "to": "objection-1", "stance": "responds"}
        ]
      }
    ]
  },
  "generator": {"tool": "folio-insights", "version": "2.0-review"}
}
```

**Status:** `design-only`. It becomes `annotation-tested` when cycle 1 yields a
real question/objection/response sequence whose nodes validate independently
and whose application-level links preserve the annotator's intended stances.
The promoted `policy proposition` may occur as an individual node, but does not
by itself exercise the `disputatio` structure.

## `conflicting_authorities`

`conflicting_authorities` is a **cross-document composite, explicitly not a
single-model configuration**. It stays application-level in folio-insights.
The composite draws on propositions from separate
`PropositionDocumentRecord`s and detects incompatible citation edges—for
example, `"follows"` and `"overrules"` directed toward the same
`authority_individual_id`. The following is one valid component record, not a
serialization of the composite itself.

```json
{
  "document_id": "opinion-later-court",
  "schema_version": 3,
  "propositions": [
    {
      "id": "prop-follows-1",
      "proposition_type": "Judicial Legal Conclusion",
      "asserter": {"role": "court", "individual_id": "court-later"},
      "validator": {"role": "court", "individual_id": "court-later", "mode": "ruled"},
      "disposition": "accepted",
      "citation_edges": [
        {
          "edge_type": "follows",
          "authority_individual_id": "authority-shared",
          "authority_text": "Shared Authority"
        },
        {
          "edge_type": "overrules",
          "authority_individual_id": "authority-shared",
          "authority_text": "Shared Authority"
        }
      ],
      "shape": "litigation"
    }
  ],
  "document_metadata": {"composite_membership": "candidate-conflict-7"},
  "generator": {"tool": "folio-insights", "version": "2.0-review"}
}
```

In production, the contrasting edges may occur in different component records;
folio-insights owns their cross-document grouping and interpretation.

**Status:** `design-only`. It becomes `annotation-tested` when cycle 1 (or the
first cycle containing the pattern) demonstrates that separately annotated
citation edges can be composed into a genuine authority conflict without
conflating mere disagreement, distinction, or chronology.

## Public API completeness and evidence status

Every public export and every public model field is listed below. Enum rows list
their complete value groups. The table records cycle-1 evidence without
claiming that one opinion exercised every public surface.

| Public element | Fields or values represented | Status |
|---|---|---|
| `SCHEMA_VERSION` | Current value `3`; record and proposition schema stamp | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)` via the persisted gold-record migrations |
| `WORKING_TAXONOMY` | Label→optional-IRI mapping: four canonical FOLIO labels carry IRIs; six library-local types carry `None` | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)`; `proposition_type` and `is_new_type` exercised |
| `ActorRole` | Exercised: `court`; `plaintiff`; `appellant`; `party`; `both_parties`; `secondary_source` | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)` |
| `ActorRole` | Deferred: `defendant`; `appellee`; `petitioner`; `respondent`; `system` | `design-only` (no Palsgraf instance) |
| `AdjudicationMode` | `ruled`; `pro_forma`; `declined` | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)`; all three modes exercised |
| `Disposition` | `accepted`; `rejected`; `revised`; `unresolved`; `assumed-arguendo` | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)`; all five exercised, including explicit `unresolved` |
| `CitationEdgeType` | `supports`; `distinguishes`; `overrules`; `follows`; `cites_record_evidence`; `interprets`; `elaborates`; `cites` | `design-only` |
| `AxiomStatus` | `proposition`; `promoted`; `demoted`; `superseded` | `design-only`; expected to remain design-only through Phase A because no Phase A annotation exercise covers the axiom lifecycle |
| `ActorRef` | `role`; `individual_id`; `name`; `assumed` | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)`; listed roles and `assumed` exercised |
| `AdjudicatorRef` | `role`; `individual_id`; `name`; `mode` | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)`; all three modes exercised |
| `CitationEdge` | `edge_type`; `authority_individual_id`; `authority_text` | `design-only` (only tool-attached edges exercised; hand-added edges deferred) |
| `PropositionShape` | Dataclass fields `name`; `expected_roles`; `description` | `design-only` |
| `SHAPES` | `litigation`; `disputatio`, each mapped to a `PropositionShape` | `design-only` (`litigation` only; `disputatio` deferred) |
| `Proposition` core | `id`; `start_char`; `end_char`; `text` | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)` |
| `Proposition` assertion/adjudication | `proposition_type`; `is_new_type`; `ActorRef`; validator including first-class `null`; `Disposition` | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)` |
| `Proposition.asserter` judicial-notice null case | first-class `null` asserter | `design-only` (no instance in Palsgraf) |
| `Proposition.triple_ids` | linked triple identifiers | `design-only` (not exercised in Palsgraf) |
| `Proposition.shape` | registered ontology selector | `design-only` (`litigation` only; `disputatio` deferred) |
| `Proposition.axiom_status` | axiom lifecycle state | `design-only` (expected through Phase A) |
| `GeneratorInfo` | `tool`; `version` | `design-only` (interchange not exercised by annotation) |
| `PropositionDocumentRecord` | `document_id`; `schema_version`; `propositions`; `document_metadata`; `generator` | `design-only` (interchange not exercised by annotation) |
| `MIGRATIONS` | Registry keyed by `(version_from, version_to)` | `design-only` |
| `register_migration` | Consecutive-version migration registration hook | `design-only` |
| `migrate_record` | Copying, forward-only interchange-record migration hook; no downgrades | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)`; v1→v2 and v2→v3 ran against the persisted cycle-1 gold record |

The package also exports `Proposition`, `PropositionDocumentRecord`, and the
supporting types above from `folio_propositions.__all__`; no shard mapping adds
fields to those public shapes.
