# Migrating to v0.4.0

v0.4.0 raises `SCHEMA_VERSION` from 3 to 4. It adds a shared content identity,
so folio-enrich propositions and folio-insights shards can be matched, and a
signed axiom lifecycle, so `axiom_status` changes carry an auditable history.

## What changed

- **Content identity** (`folio_propositions.identity`). `content_identity`,
  `content_iri`, `normalize_source_uri`, `normalize_span`, and
  `document_source_uri` reproduce the folio-insights shard IRI recipe byte for
  byte. The identity is per `(source URI, span)`, not per proposition type.
  `CONTENT_IRI_PREFIX` is `urn:folio:shard/`; an IRI is that prefix plus the
  first 32 lowercase hex characters of a SHA-256 hash.
- **`Proposition.content_iri`** (optional). When set it must be a well-formed
  content IRI.
- **`PropositionDocumentRecord.source_uri`** (optional). When set, every
  proposition with both `text` and `content_iri` must satisfy
  `content_iri == content_iri(source_uri, text)`. `stamp_content_iris(record)`
  returns a copy with the IRI computed for every proposition that has text.
- **Record version check.** A record now rejects propositions whose
  `schema_version` differs from its own.
- **`Proposition.axiom_history`** (defaults to `[]`). `axiom_status` must equal
  the last entry's `to_status`, or `proposition` when the history is empty, and
  entries must chain from `proposition`.
- **Signed lifecycle** (`folio_propositions.lifecycle`). `AxiomTransition`,
  `AxiomAction`, `AXIOM_TRANSITIONS`, `apply_transition`, `verify_history`,
  `transition_signing_payload`, and the `TransitionVerifier` protocol.
  `superseded` is terminal.
- **Optional did:key signing** (`folio_propositions.signing`, extra
  `folio-propositions[signing]`). `DidKeyEd25519Verifier`, `sign_transition`,
  and `did_key_from_public_bytes`. The core package still depends only on
  pydantic.

## Migrating stored records

```python
from folio_propositions import PropositionDocumentRecord, migrate_record

migrated = migrate_record(stored_record)  # v1, v2 or v3 -> v4
record = PropositionDocumentRecord.model_validate(migrated)
```

The v3→v4 step stamps `schema_version: 4` on the record and its propositions,
adds `axiom_history: []`, and leaves `content_iri` absent: a v3 record has no
source URI to compute it from. Bare proposition dictionaries migrate the same
way, and v1→v4 chains through the frozen historical steps.

### The legacy `migrate` entry

A v3 proposition whose `axiom_status` is not `proposition` has no recorded
transition. The migration records exactly one entry so the history stays
consistent with the status:

```json
{
  "from_status": "proposition",
  "to_status": "promoted",
  "action": "migrate",
  "actor_did": null,
  "at": null,
  "reason": "pre-v4 status without recorded transition",
  "signature": null
}
```

`migrate` entries are unsigned, may only be the first history entry, are
skipped by `verify_history`, and are refused by `apply_transition`. Treat them
as "status asserted before signing existed", not as a verified decision.

## Applying a signed transition

```python
from datetime import UTC, datetime

from folio_propositions import (
    AxiomTransitionDraft,
    DidKeyEd25519Verifier,
    apply_transition,
    sign_transition,
)

draft = AxiomTransitionDraft(
    from_status="proposition",
    to_status="promoted",
    action="promote",
    actor_did=actor_did,  # did:key:z6Mk...
    at=datetime.now(UTC),
    reason="Reviewed against the holding",
)
transition = sign_transition(
    proposition.id, proposition.content_iri, draft, private_key, f"{actor_did}#key-1"
)
promoted = apply_transition(proposition, transition, DidKeyEd25519Verifier())
```

`apply_transition` returns a new proposition; the input is unchanged. It raises
`IllegalAxiomTransition` for a transition not in the table or not starting
from the current status, and `AxiomSignatureError` when the signature does not
verify. The signature covers the proposition id and content IRI, so it cannot
be replayed onto another proposition.

## Consumer guidance

- **folio-enrich.** Keep the job-scoped `id` as the proposition identity
  within a job. Set `source_uri` on each record (the caller's URI, or
  `document_source_uri(text)` when there is none) and call
  `stamp_content_iris` before export. `content_iri` is the cross-product match
  key.
- **folio-insights.** `content_iri` equals `mint_shard_iri(source_uri,
  span)[0]` for the same source and span, and the `provenance_hash` from
  `content_identity` equals its second element. Join enrich propositions to
  shards on that value. A bridged proposition arrives with
  `axiom_status="proposition"`; its corpus-side `epistemic_status` (for
  example `hypothesis`) is separate. See
  [shard mapping](shard-mapping.md#axiom-lifecycle-vs-insights-epistemic-status).
