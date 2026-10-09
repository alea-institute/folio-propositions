# folio-insights shard mapping

This document maps the five folio-insights v2.0 shard subtypes to the public
`folio-propositions` API at `SCHEMA_VERSION` 4. The shard-envelope redesign is
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
closed taxonomy value `"Legal Proposition"`. Its `content_iri` is
`content_iri("https://example.com/opinions/example", text)`; in an interchange
record that value is checked against the record's `source_uri`.

```json
{
  "id": "prop-simple-1",
  "schema_version": 4,
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
  "axiom_status": "proposition",
  "content_iri": "urn:folio:shard/cd86bce64db42a4641ae3c36d2e613f2",
  "axiom_history": []
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
  "schema_version": 4,
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
  "axiom_status": "proposition",
  "axiom_history": []
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
  "schema_version": 4,
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
  "axiom_status": "proposition",
  "axiom_history": []
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
  "schema_version": 4,
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
  "schema_version": 4,
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

## Axiom lifecycle vs. insights epistemic status

`Proposition.axiom_status` is this library's promotion lifecycle: a
proposition becomes an axiom only through a signed `promote` transition
recorded in `axiom_history`, and may later be demoted or superseded. It says
who vouched for the proposition as settled, and when.

folio-insights' `epistemic_status` (for example `hypothesis`) is a corpus-side
field describing how well the corpus supports a shard. It is not part of the
`Proposition` model and is not changed by `apply_transition`. The two are
independent: a bridged folio-enrich proposition arrives in folio-insights as
`epistemic_status="hypothesis"` with `axiom_status="proposition"`, and only a
later signed transition changes the latter.

## Public API completeness and evidence status

Every public export and every public model field is listed below. Enum rows list
their complete value groups. The table records cycle-1 evidence without
claiming that one opinion exercised every public surface.

| Public element | Fields or values represented | Status |
|---|---|---|
| `SCHEMA_VERSION` | Current value `4`; record and proposition schema stamp | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)` via the persisted gold-record migrations |
| `WORKING_TAXONOMY` | Label→optional-IRI mapping: four canonical FOLIO labels carry IRIs; six library-local types carry `None` | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)`; `proposition_type` and `is_new_type` exercised |
| `ActorRole` | Exercised: `court`; `plaintiff`; `appellant`; `party`; `both_parties`; `secondary_source` | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)` |
| `ActorRole` | Deferred: `defendant`; `appellee`; `petitioner`; `respondent`; `system` | `design-only` (no Palsgraf instance) |
| `AdjudicationMode` | `ruled`; `pro_forma`; `declined` | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)`; all three modes exercised |
| `Disposition` | `accepted`; `rejected`; `revised`; `unresolved`; `assumed-arguendo` | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)`; all five exercised, including explicit `unresolved` |
| `CitationEdgeType` | `supports`; `distinguishes`; `overrules`; `follows`; `cites_record_evidence`; `interprets`; `elaborates`; `cites` | `design-only` |
| `AxiomStatus` | `proposition`; `promoted`; `demoted`; `superseded` | `implemented (v0.4.0: signed transitions; annotation evidence pending)` |
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
| `Proposition.axiom_status` | axiom lifecycle state | `implemented (v0.4.0: signed transitions; annotation evidence pending)` |
| `Proposition.axiom_history` | ordered `AxiomTransition` entries that must chain from `proposition` to `axiom_status`, with `sequence` equal to the index and strictly increasing signed `at` | `implemented (v0.4.0: signed transitions; annotation evidence pending)` |
| `Proposition.content_iri` | optional `urn:folio:shard/` + 32 lowercase hex content IRI | `implemented (v0.4.0; cross-product matching pending)` |
| `GeneratorInfo` | `tool`; `version` | `design-only` (interchange not exercised by annotation) |
| `PropositionDocumentRecord` | `document_id`; `schema_version`; `propositions`; `document_metadata`; `generator`; `source_uri` (checks each `content_iri` against `content_iri(source_uri, text)`) | `design-only` (interchange not exercised by annotation) |
| `stamp_content_iris` | Copy of a record with `content_iri` computed for every proposition with text; requires `source_uri` | `implemented (v0.4.0; cross-product matching pending)` |
| `CONTENT_IRI_PREFIX`; `ContentIdentity`; `content_identity`; `content_iri` | folio-insights shard IRI recipe: `(source_uri, span)` → IRI and full SHA-256 provenance hash | `implemented (v0.4.0; golden vectors from the folio-insights recipe)` |
| `normalize_source_uri`; `normalize_span`; `document_source_uri` | Recipe normalizers; deterministic `urn:sha256:` URI for a document without a caller URI | `implemented (v0.4.0)` |
| `AxiomAction` | `promote`; `demote`; `supersede`; `migrate` (migration-only) | `implemented (v0.4.0: signed transitions; annotation evidence pending)` |
| `AXIOM_TRANSITIONS` | Read-only legal `(from, to)` → action table; `superseded` terminal | `implemented (v0.4.0: signed transitions; annotation evidence pending)` |
| `AxiomTransition`; `AxiomTransitionDraft`; `TransitionSignature` | `sequence`; `from_status`; `to_status`; `action`; `actor_did`; `at`; `reason`; `signature` (`algorithm`; `key_id`; `value`) | `implemented (v0.4.0: signed transitions; annotation evidence pending)` |
| `apply_transition`; `verify_history`; `transition_signing_payload` | Checked, signature-verified status change (requires a stamped `content_iri`); history re-verification (`migrate` entries rejected unless `allow_legacy_migrate=True`); canonical JSON payload binding `proposition_id`, `content_iri` and `sequence` | `implemented (v0.4.0: signed transitions; annotation evidence pending)` |
| `TransitionVerifier`; `IllegalAxiomTransition`; `AxiomSignatureError` | Verifier protocol and lifecycle errors | `implemented (v0.4.0: signed transitions; annotation evidence pending)` |
| `DidKeyEd25519Verifier`; `sign_transition`; `did_key_from_public_bytes` | Optional `did:key` Ed25519 signing (`signing` extra); self-certifying, so consumers must check `actor_did` against their authorized signers | `implemented (v0.4.0: signed transitions; annotation evidence pending)` |
| `MIGRATIONS` | Registry keyed by `(version_from, version_to)` | `design-only` |
| `register_migration` | Consecutive-version migration registration hook | `design-only` |
| `migrate_record` | Copying, forward-only interchange-record migration hook; no downgrades | `annotation-tested (cycle 1: Palsgraf, AI-annotated, Damien-delegated)`; v1→v2 and v2→v3 ran against the persisted cycle-1 gold record; v3→v4 unit-tested only |

The package also exports `Proposition`, `PropositionDocumentRecord`, and the
supporting types above from `folio_propositions.__all__`; no shard mapping adds
fields to those public shapes.
