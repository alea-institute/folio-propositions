"""Runnable v3 migration, caller authorization, and saved-history walkthrough.

Run from a checkout with the signing extra installed; see docs/migration-0.4.0.md.
All records are synthetic. Keys and serialized records stay in memory.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from folio_propositions import (
    AXIOM_TRANSITIONS,
    AxiomSignatureError,
    AxiomStatus,
    AxiomTransition,
    AxiomTransitionDraft,
    DidKeyEd25519Verifier,
    IllegalAxiomTransition,
    Proposition,
    PropositionDocumentRecord,
    TransitionSignature,
    TransitionVerifier,
    apply_transition,
    did_key_from_public_bytes,
    migrate_record,
    sign_transition,
    stamp_content_iris,
    verify_history,
)

SOURCE_URI = "https://example.org/migration-demo"
DEMO_TIME = datetime(2026, 10, 26, 12, 0, tzinfo=UTC)


class AuthorizedVerifier:
    """A caller-owned current allowlist composed with signature verification."""

    def __init__(self, allowed_dids: Iterable[str]) -> None:
        self.allowed_dids = frozenset(allowed_dids)
        self.signatures = DidKeyEd25519Verifier()

    def verify(
        self, payload: bytes, signature: TransitionSignature, actor_did: str
    ) -> bool:
        return actor_did in self.allowed_dids and self.signatures.verify(
            payload, signature, actor_did
        )


class DemoSigner:
    """Fresh in-memory demo key; never use this as a key-storage recipe."""

    def __init__(self) -> None:
        self.key = Ed25519PrivateKey.generate()
        raw = self.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        self.did = did_key_from_public_bytes(raw)

    def transition(
        self, proposition: Proposition, to_status: AxiomStatus
    ) -> AxiomTransition:
        sequence = len(proposition.axiom_history)
        draft = AxiomTransitionDraft(
            sequence=sequence,
            from_status=proposition.axiom_status,
            to_status=to_status,
            action=AXIOM_TRANSITIONS[(proposition.axiom_status, to_status)],
            actor_did=self.did,
            at=DEMO_TIME + timedelta(minutes=sequence),
            reason="Synthetic review for the migration example",
        )
        return sign_transition(
            proposition.id,
            proposition.content_iri,
            draft,
            self.key,
            f"{self.did}#key-1",
        )


def v3_record(status: AxiomStatus = AxiomStatus.PROPOSITION) -> dict[str, Any]:
    """A synthetic v3 input with a complete text span but no content identity."""
    text = "This is a synthetic example proposition."
    return {
        "document_id": "migration-demo",
        "schema_version": 3,
        "propositions": [
            {
                "id": "demo-1",
                "schema_version": 3,
                "start_char": 0,
                "end_char": len(text),
                "text": text,
                "proposition_type": "Legal Proposition",
                "asserter": {"role": "party"},
                "validator": None,
                "disposition": "unresolved",
                "axiom_status": status.value,
            }
        ],
    }


def migrate_demo_record(stored: dict[str, Any]) -> PropositionDocumentRecord:
    """Migrate a demo fixture without changing the original, then stamp it."""
    record = PropositionDocumentRecord.model_validate(migrate_record(stored))
    with_source = record.model_copy(update={"source_uri": SOURCE_URI})
    return stamp_content_iris(with_source)


def load_demo_record(
    saved: str,
    verifier: TransitionVerifier,
    *,
    trust_legacy_source: bool = False,
) -> PropositionDocumentRecord:
    """Validate and verify this example's complete, source-bearing records.

    This is not a generic ingestion API: optional source/text context must be
    present to check its binding to content_iri. Policy and legacy trust come
    from the caller, never from fields in the saved record.
    """
    record = PropositionDocumentRecord.model_validate_json(saved)
    for proposition in record.propositions:
        verify_history(proposition, verifier, allow_legacy_migrate=trust_legacy_source)
    return record


def native_demo() -> tuple[PropositionDocumentRecord, Proposition]:
    """Migrate a plain proposition, sign its lifecycle, reload, and replay it."""
    base = migrate_demo_record(v3_record())
    signer = DemoSigner()
    # Supply policy independently of the imported record's claimed actors.
    policy = AuthorizedVerifier({signer.did})
    start = base.propositions[0]

    outsider = DemoSigner()
    unauthorized = outsider.transition(start, AxiomStatus.PROMOTED)
    try:
        apply_transition(start, unauthorized, policy)
    except AxiomSignatureError:
        print("Unauthorized signer: rejected despite a valid signature")
    else:
        raise AssertionError("Expected caller policy to reject the outsider")

    outsider_record = base.model_copy(
        update={
            "propositions": [
                apply_transition(start, unauthorized, DidKeyEd25519Verifier())
            ]
        }
    )
    try:
        load_demo_record(outsider_record.model_dump_json(), policy)
    except AxiomSignatureError:
        print("Unauthorized saved history: rejected")
    else:
        raise AssertionError("Expected saved-history policy rejection")

    current = start
    for status in (AxiomStatus.PROMOTED, AxiomStatus.DEMOTED, AxiomStatus.PROMOTED):
        current = apply_transition(current, signer.transition(current, status), policy)

    # Same from_status, but sequence 1 cannot be appended again at index 3.
    old_demotion = current.axiom_history[1]
    try:
        apply_transition(current, old_demotion, policy)
    except IllegalAxiomTransition:
        print("Obsolete demotion: rejected")
    else:
        raise AssertionError("Expected rejection of an obsolete signed transition")

    current = apply_transition(
        current, signer.transition(current, AxiomStatus.SUPERSEDED), policy
    )
    saved = base.model_copy(update={"propositions": [current]}).model_dump_json()
    restored = load_demo_record(saved, policy)

    # Reconstruct ONLY this native history from its original clean stamped base.
    # Do not clear a migrated legacy anchor or generate replacement signatures.
    replayed = start
    for entry in restored.propositions[0].axiom_history:
        replayed = apply_transition(replayed, entry, policy)
    if replayed != restored.propositions[0]:
        raise AssertionError("Replay did not reproduce the saved proposition")
    print("Native lifecycle: superseded; 4 signed entries verified and replayed")
    return restored, replayed


def legacy_demo() -> PropositionDocumentRecord:
    """Keep an unsigned legacy status claim; trust it only by caller opt-in."""
    base = migrate_demo_record(v3_record(AxiomStatus.PROMOTED))
    signer = DemoSigner()
    policy = AuthorizedVerifier({signer.did})
    saved = base.model_dump_json()
    try:
        load_demo_record(saved, policy)
    except AxiomSignatureError:
        print("Unsigned legacy status: rejected by default")
    else:
        raise AssertionError("Expected rejection of an unsigned legacy status")

    # This opt-in belongs to the caller that trusts the original v3 source.
    # It does not turn the migration opener into a verified historical decision.
    trusted = load_demo_record(saved, policy, trust_legacy_source=True)
    start = trusted.propositions[0]
    demoted = apply_transition(
        start, signer.transition(start, AxiomStatus.DEMOTED), policy
    )
    saved = trusted.model_copy(update={"propositions": [demoted]}).model_dump_json()
    try:
        load_demo_record(saved, policy)
    except AxiomSignatureError:
        print("Signed append: legacy trust still required")
    else:
        raise AssertionError("A signed append must not legitimize an unsigned opener")

    # The opt-in skips only the opener. Every signed entry still needs both
    # caller authorization and a valid signature, on every acceptance.
    restored = load_demo_record(saved, policy, trust_legacy_source=True)
    print(
        "Legacy lifecycle: demoted; unsigned anchor retained, 1 signed entry verified"
    )
    return restored


def main() -> None:
    native_demo()
    legacy_demo()


if __name__ == "__main__":
    main()
