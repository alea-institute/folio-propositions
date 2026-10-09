# folio-propositions

`folio-propositions` defines the shared, typed Proposition ledger schema used by
`folio-enrich` and `folio-insights`. Each proposition records an asserter side and
a validator side; either side may be null when that is the legally accurate state.

Install the package with:

```bash
pip install folio-propositions
```

```python
from folio_propositions import Proposition, WORKING_TAXONOMY

open_position = Proposition(
    id="p-1",
    proposition_type="Legal Proposition",
    asserter={"role": "party", "name": "Appellant"},
    validator=None,
    disposition="unresolved",
)

folio_iri = WORKING_TAXONOMY[open_position.proposition_type]
```

`WORKING_TAXONOMY` maps canonical labels to optional FOLIO IRIs. Library-local
working types remain valid entries with a `None` IRI until FOLIO gains an exact
class for them.

## Content identity

`content_iri(source_uri, span)` returns the same `urn:folio:shard/…` IRI that
folio-insights mints for a shard drawn from that span of that source, so the two
products can match a proposition to a corpus shard. The identity is per
`(source, span)`: URIs and spans are normalized (case, trailing slash, NFC,
newlines, surrounding whitespace) before hashing. Set `source_uri` on a
`PropositionDocumentRecord` and call `stamp_content_iris(record)` to fill every
proposition's `content_iri`; `document_source_uri(text)` gives a deterministic
URI when a document has none.

## Axiom lifecycle

`axiom_status` changes only through `apply_transition`, which checks the legal
transition table (`proposition → promoted ⇄ demoted`, any of them →
`superseded`, which is terminal) and verifies the actor's signature. Every
change is appended to `axiom_history`. Install
`folio-propositions[signing]` for the `did:key` Ed25519 verifier and the
`sign_transition` helper. See the [v0.4.0 migration notes](docs/migration-0.4.0.md).

## Docs

See the [documentation index](docs/README.md) for the folio-insights shard
mapping, v2.0 ledger rationale, review-disposition template, gold-cycle
learnings template, and Phase A exit-record template.
