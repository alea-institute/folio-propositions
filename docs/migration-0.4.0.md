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
  returns a copy with the IRI computed for every proposition that has
  non-empty text. It refuses (with `ValueError`) to change an existing
  `content_iri` on a proposition whose history holds a signed entry.
- **Empty spans.** The library deliberately rejects spans that normalize to the
  empty string (`content_identity` raises `ValueError`), whereas folio-insights'
  `mint_shard_iri` would hash one. `stamp_content_iris` skips such
  propositions, and a record rejects a `content_iri` on one. Consumers stamp
  only non-empty text.
- **Record version check.** A record now rejects propositions whose
  `schema_version` differs from its own.
- **`Proposition.axiom_history`** (defaults to `[]`). `axiom_status` must equal
  the last entry's `to_status`, or `proposition` when the history is empty;
  entries must chain from `proposition`; each entry's `sequence` must equal its
  index; and consecutive signed entries must have strictly increasing `at`.
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
source URI to compute it from. An `axiom_history` already present is kept, and
entries lacking a `sequence` get their index. Bare proposition dictionaries
migrate the same way, and v1→v4 chains through the frozen historical steps.

Migration is forward-only (`migrate_record` refuses downgrades). Rolling stored
data back to v3 requires keeping the v3 originals.

### The legacy `migrate` entry

A v3 proposition whose `axiom_status` is not `proposition` has no recorded
transition. The migration records exactly one entry so the history stays
consistent with the status:

```json
{
  "sequence": 0,
  "from_status": "proposition",
  "to_status": "promoted",
  "action": "migrate",
  "actor_did": null,
  "at": null,
  "reason": "pre-v4 status without recorded transition",
  "signature": null
}
```

`migrate` entries are unsigned, may only be the first history entry, and are
refused by `apply_transition`. Nobody can verify them, so `verify_history`
raises `AxiomSignatureError` ("unverified legacy status") on one by default.
Pass `verify_history(proposition, verifier, allow_legacy_migrate=True)` only
when you deliberately trust your migrated v3 data. Treat a `migrate` entry as
"status asserted before signing existed", not as a verified decision.

## Applying a signed transition

This fragment runs from the repository root after the signing-extra installation
below. Its setup helpers come from the [consumer example](../examples/migration_v4.py),
not the installed package. The generated signer is deliberately authorized for
this synthetic demonstration; in an application, obtain the allowed DIDs from
your own policy independently of the record being imported.

```python
from datetime import UTC, datetime

from examples.migration_v4 import (
    AuthorizedVerifier,
    DemoSigner,
    migrate_demo_record,
    v3_record,
)
from folio_propositions import (
    AxiomTransitionDraft,
    apply_transition,
    sign_transition,
)

proposition = migrate_demo_record(v3_record()).propositions[0]
signer = DemoSigner()  # ephemeral, in-memory example key
policy = AuthorizedVerifier({signer.did})
draft = AxiomTransitionDraft(
    sequence=len(proposition.axiom_history),  # next history index
    from_status="proposition",
    to_status="promoted",
    action="promote",
    actor_did=signer.did,
    at=datetime.now(UTC),
    reason="Reviewed against the holding",
)
transition = sign_transition(
    proposition.id, proposition.content_iri, draft, signer.key, f"{signer.did}#key-1"
)
promoted = apply_transition(proposition, transition, policy)
```

`apply_transition` returns a new proposition; the input is unchanged. It raises
`IllegalAxiomTransition` for a transition not in the table, not starting from
the current status, not carrying the next `sequence`, or not strictly later
than the last signed entry. It raises `AxiomSignatureError` when the
proposition has no `content_iri` or the signature does not verify.

The signature binds `proposition_id`, `content_iri` and `sequence` (plus the
transition's own fields). A signed transition therefore requires a stamped
content IRI (`sign_transition` raises `ValueError` without one). The binding
also stops an old entry from being re-appended to roll a status back, and
stops a signature from being replayed onto another proposition or span. Stamp
`content_iri` before signing: re-stamping a signed proposition to a different
IRI is refused.

`did:key` is self-certifying: a verified signature proves only that the key
named by `actor_did` signed. Consumers must check `actor_did` against their own
set of authorized signers before trusting a promotion.

## Run the consumer examples

From a checkout of this repository, use Python 3.11 or newer and install the
existing signing extra:

```bash
uv venv .venv
uv pip install --python .venv/bin/python -e '.[signing]'
.venv/bin/python examples/migration_v4.py
```

The [script](../examples/migration_v4.py) generates synthetic v3 records and
ephemeral Ed25519 keys. It performs all migration, serialization, and replay
in memory and does not read or write stored records or key files. This is a
checkout example, not a CLI included in the package wheel. The development
environment from the README already has everything it needs.

Expected output (key and signature bytes are never printed):

```text
Unauthorized signer: rejected despite a valid signature
Unauthorized saved history: rejected
Obsolete demotion: rejected
Native lifecycle: superseded; 4 signed entries verified and replayed
Unsigned legacy status: rejected by default
Signed append: legacy trust still required
Legacy lifecycle: demoted; unsigned anchor retained, 1 signed entry verified
```

### Caller-owned signer policy

`AuthorizedVerifier` copies the caller's allowed DIDs into an immutable set. It
returns `False` for any other actor and delegates allowed actors to
`DidKeyEd25519Verifier`. Pass that same combined verifier to `apply_transition`
and `verify_history`: both authorization and signature validity are required.
The protocol returns a boolean, so `AxiomSignatureError` can mean policy denial
as well as an invalid signature. An empty allowlist rejects every signed entry.

The allowlist must come from the consumer's trusted configuration, not from
actors listed in the imported history. Successfully applying one new transition
checks that entry; it does not approve the earlier history. The example's
`load_demo_record` validates the complete JSON record, then verifies **every**
history entry before returning it for use or further append. An authorized last
actor cannot make an unauthorized earlier actor acceptable.

### Saved-history replay and obsolete transitions

The native example migrates a plain v3 proposition, attaches its source URI,
stamps its content IRI, then follows
`proposition → promoted → demoted → promoted → superseded`. After saving and
reloading the complete record, it reconstructs the lifecycle from the original
clean stamped proposition by applying the recorded transitions unchanged. It
compares the reconstructed proposition, including its history, with the saved
one; no replacement signatures are generated.

The steps protect different boundaries:

| Step | What it checks |
| --- | --- |
| `PropositionDocumentRecord.model_validate_json` | Schema consistency, history chain, sequence indexes, increasing signed timestamps, final status, and source/span binding when that context is present. |
| `verify_history` with the caller's policy | Every signed entry has an authorized actor and a valid signature bound to the proposition id, content IRI, sequence, and transition fields. |
| `apply_transition` during reconstruction | Each recorded event fits the current state, next sequence, and timestamp; `superseded` is terminal. |

Reconstruction from the matching clean base is legitimate replay. Appending
the old demotion to the already re-promoted proposition is rejected: although
its `from_status` matches, its signed sequence is obsolete. Altering the sequence
invalidates its signature. Reusing it for another proposition id or content IRI
also fails verification.

The loader is scoped to these complete source-bearing fixtures. The schema's
optional source/text fields mean JSON validation alone is not a general guarantee
of source/span binding for arbitrary records, and it never verifies signatures.
This example checks the presented history against a **current** caller policy.
It cannot prove a signer was authorized at an earlier date, or detect an omitted
suffix whose remaining history is structurally valid. Those guarantees require
independent policy history or trusted checkpoints, outside this example.

### Explicit trust for legacy status

The separate legacy example starts from a v3 `promoted` status. Migration creates
the unsigned sequence-zero `migrate` opener described above. Default acceptance
rejects it. Only the caller's explicit `trust_legacy_source=True` passes
`allow_legacy_migrate=True` to verification; a flag in imported data cannot opt in.

After that trust decision, the example appends an authorized, signed demotion at
sequence one, preserving the opener. Reloading still requires explicit legacy
trust, and every later signed entry still needs an authorized actor and a valid
signature. The [example tests](../tests/test_migration_examples.py) exercise
unauthorized and tampered later entries, as well as malformed extra `migrate`
entries. The opener remains an unverified historical claim: it is never signed,
removed, or sent to `apply_transition` for native reconstruction.

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
