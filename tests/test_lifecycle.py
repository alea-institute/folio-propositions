from datetime import UTC, datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from pydantic import ValidationError

from folio_propositions import (
    AXIOM_TRANSITIONS,
    AxiomAction,
    AxiomSignatureError,
    AxiomStatus,
    AxiomTransition,
    AxiomTransitionDraft,
    DidKeyEd25519Verifier,
    IllegalAxiomTransition,
    Proposition,
    TransitionSignature,
    apply_transition,
    content_iri,
    did_key_from_public_bytes,
    sign_transition,
    transition_signing_payload,
    verify_history,
)
from folio_propositions.signing import (
    base58btc_decode,
    base58btc_encode,
    public_bytes_from_did_key,
)

AT = datetime(2026, 10, 9, 12, 0, tzinfo=UTC)
VERIFIER = DidKeyEd25519Verifier()
STATUSES = list(AxiomStatus)


class Signer:
    def __init__(self) -> None:
        self.key = Ed25519PrivateKey.generate()
        raw = self.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        self.did = did_key_from_public_bytes(raw)
        self.key_id = f"{self.did}#{self.did[len('did:key:') :]}"


@pytest.fixture
def signer() -> Signer:
    return Signer()


def proposition(**overrides) -> Proposition:
    values = {
        "id": "p-1",
        "start_char": 0,
        "end_char": 4,
        "text": "span",
        "proposition_type": "Legal Proposition",
        "asserter": {"role": "party"},
        "validator": {"role": "court"},
        "disposition": "accepted",
        "content_iri": content_iri("https://example.com/doc", "span"),
    }
    values.update(overrides)
    return Proposition(**values)


def draft(from_status, to_status, action=None, signer=None, **overrides):
    action = (
        action or AXIOM_TRANSITIONS[(AxiomStatus(from_status), AxiomStatus(to_status))]
    )
    values = {
        "from_status": from_status,
        "to_status": to_status,
        "action": action,
        "actor_did": signer.did if signer else "did:key:z6MkExample",
        "at": AT,
        "reason": "reviewed",
    }
    values.update(overrides)
    return AxiomTransitionDraft(**values)


def signed(value: Proposition, from_status, to_status, signer, **overrides):
    return sign_transition(
        value.id,
        value.content_iri,
        draft(from_status, to_status, signer=signer, **overrides),
        signer.key,
        signer.key_id,
    )


def advance(value: Proposition, to_status, signer) -> Proposition:
    transition = signed(value, value.axiom_status, to_status, signer)
    return apply_transition(value, transition, VERIFIER)


def reach(status: AxiomStatus, signer) -> Proposition:
    """Build a proposition in ``status`` through legal signed transitions."""

    path = {
        AxiomStatus.PROPOSITION: [],
        AxiomStatus.PROMOTED: [AxiomStatus.PROMOTED],
        AxiomStatus.DEMOTED: [AxiomStatus.PROMOTED, AxiomStatus.DEMOTED],
        AxiomStatus.SUPERSEDED: [AxiomStatus.SUPERSEDED],
    }[status]
    value = proposition()
    for step in path:
        value = advance(value, step, signer)
    assert value.axiom_status == status
    return value


def test_transition_table_is_read_only_and_complete():
    assert dict(AXIOM_TRANSITIONS) == {
        ("proposition", "promoted"): "promote",
        ("promoted", "demoted"): "demote",
        ("demoted", "promoted"): "promote",
        ("proposition", "superseded"): "supersede",
        ("promoted", "superseded"): "supersede",
        ("demoted", "superseded"): "supersede",
    }
    assert not any(
        from_status == AxiomStatus.SUPERSEDED for from_status, _ in AXIOM_TRANSITIONS
    )
    assert AxiomAction.MIGRATE not in AXIOM_TRANSITIONS.values()
    with pytest.raises(TypeError):
        AXIOM_TRANSITIONS[("superseded", "promoted")] = AxiomAction.PROMOTE  # type: ignore[index]


@pytest.mark.parametrize(("pair", "action"), list(AXIOM_TRANSITIONS.items()))
def test_every_legal_transition_applies(pair, action, signer):
    from_status, to_status = pair
    start = reach(from_status, signer)
    transition = signed(start, from_status, to_status, signer)
    result = apply_transition(start, transition, VERIFIER)

    assert result.axiom_status == to_status
    assert result.axiom_history[-1] == transition
    assert result.axiom_history[-1].action == action
    assert len(result.axiom_history) == len(start.axiom_history) + 1
    assert start.axiom_status == from_status  # input unchanged
    verify_history(result, VERIFIER)
    assert Proposition.model_validate_json(result.model_dump_json()) == result


ILLEGAL_PAIRS = [
    (from_status, to_status)
    for from_status in STATUSES
    for to_status in STATUSES
    if (from_status, to_status) not in AXIOM_TRANSITIONS
]


def test_grid_partition_covers_all_sixteen_pairs():
    assert len(ILLEGAL_PAIRS) + len(AXIOM_TRANSITIONS) == 16


@pytest.mark.parametrize(("from_status", "to_status"), ILLEGAL_PAIRS)
def test_every_illegal_pair_raises(from_status, to_status, signer):
    start = reach(from_status, signer)
    # A well-formed model refuses the pair outright.
    with pytest.raises(ValidationError):
        draft(from_status, to_status, action=AxiomAction.PROMOTE, signer=signer)
    # A forged object that skipped validation is still refused by apply_transition.
    forged = AxiomTransition.model_construct(
        from_status=from_status,
        to_status=to_status,
        action=AxiomAction.PROMOTE,
        actor_did=signer.did,
        at=AT,
        reason=None,
        signature=TransitionSignature(
            algorithm="ed25519", key_id=signer.key_id, value="AA"
        ),
    )
    with pytest.raises(IllegalAxiomTransition):
        apply_transition(start, forged, VERIFIER)


def test_wrong_action_for_legal_pair_is_rejected():
    with pytest.raises(ValidationError):
        draft("proposition", "promoted", action=AxiomAction.SUPERSEDE)


def test_transition_must_start_from_current_status(signer):
    start = reach(AxiomStatus.PROMOTED, signer)
    transition = signed(start, "proposition", "superseded", signer)
    with pytest.raises(IllegalAxiomTransition):
        apply_transition(start, transition, VERIFIER)


def test_ae2_signed_promotion_applies_and_superseded_cannot_be_promoted(signer):
    value = proposition()
    promoted = apply_transition(
        value, signed(value, "proposition", "promoted", signer), VERIFIER
    )
    assert promoted.axiom_status == AxiomStatus.PROMOTED
    assert promoted.axiom_history[0].actor_did == signer.did

    superseded = advance(promoted, AxiomStatus.SUPERSEDED, signer)
    forged = AxiomTransition.model_construct(
        from_status=AxiomStatus.SUPERSEDED,
        to_status=AxiomStatus.PROMOTED,
        action=AxiomAction.PROMOTE,
        actor_did=signer.did,
        at=AT,
        reason=None,
        signature=None,
    )
    with pytest.raises(IllegalAxiomTransition):
        apply_transition(superseded, forged, VERIFIER)
    # Even a validly signed demoted->promoted entry cannot revive it.
    with pytest.raises(IllegalAxiomTransition):
        apply_transition(
            superseded, signed(superseded, "demoted", "promoted", signer), VERIFIER
        )


def test_tampered_reason_fails_signature(signer):
    value = proposition()
    transition = signed(value, "proposition", "promoted", signer)
    tampered = transition.model_copy(update={"reason": "rubber-stamped"})
    with pytest.raises(AxiomSignatureError):
        apply_transition(value, tampered, VERIFIER)


def test_signature_binds_proposition_id_and_content_iri(signer):
    value = proposition()
    transition = signed(value, "proposition", "promoted", signer)
    with pytest.raises(AxiomSignatureError):
        apply_transition(value.model_copy(update={"id": "p-2"}), transition, VERIFIER)
    other_iri = content_iri("https://example.com/other", "span")
    with pytest.raises(AxiomSignatureError):
        apply_transition(
            value.model_copy(update={"content_iri": other_iri}), transition, VERIFIER
        )


def test_wrong_key_fails_signature(signer):
    value = proposition()
    impostor = Signer()
    transition = sign_transition(
        value.id,
        value.content_iri,
        draft("proposition", "promoted", signer=signer),
        impostor.key,
        signer.key_id,
    )
    with pytest.raises(AxiomSignatureError):
        apply_transition(value, transition, VERIFIER)


def test_key_id_must_belong_to_actor(signer):
    value = proposition()
    other = Signer()
    transition = sign_transition(
        value.id,
        value.content_iri,
        draft("proposition", "promoted", signer=signer),
        signer.key,
        other.key_id,
    )
    with pytest.raises(AxiomSignatureError):
        apply_transition(value, transition, VERIFIER)
    bare = transition.model_copy(
        update={
            "signature": transition.signature.model_copy(update={"key_id": signer.did})
        }
    )
    with pytest.raises(AxiomSignatureError):
        apply_transition(value, bare, VERIFIER)


def test_malformed_signature_value_or_actor_did_is_rejected(signer):
    value = proposition()
    transition = signed(value, "proposition", "promoted", signer)
    garbled = transition.model_copy(
        update={"signature": transition.signature.model_copy(update={"value": "!!"})}
    )
    with pytest.raises(AxiomSignatureError):
        apply_transition(value, garbled, VERIFIER)
    payload = transition_signing_payload(value.id, value.content_iri, transition)
    assert (
        VERIFIER.verify(payload, transition.signature, "did:web:example.com") is False
    )
    assert VERIFIER.verify(payload, transition.signature, "did:key:z0OIl") is False


def test_migrate_entries_are_rejected_by_apply_transition():
    value = proposition()
    migrate = AxiomTransition(
        from_status="proposition",
        to_status="promoted",
        action="migrate",
        actor_did=None,
        at=None,
    )
    with pytest.raises(IllegalAxiomTransition):
        apply_transition(value, migrate, VERIFIER)


def test_migrate_entries_must_be_unsigned():
    with pytest.raises(ValidationError):
        AxiomTransition(
            from_status="proposition",
            to_status="promoted",
            action="migrate",
            actor_did=None,
            at=None,
            signature={"algorithm": "ed25519", "key_id": "did:key:z#z", "value": "AA"},
        )


def test_signed_transitions_require_actor_time_signature_and_aware_time():
    base = {
        "from_status": "proposition",
        "to_status": "promoted",
        "action": "promote",
        "actor_did": "did:key:z6MkExample",
        "at": AT,
        "signature": {
            "algorithm": "ed25519",
            "key_id": "did:key:z6MkExample#k",
            "value": "AA",
        },
    }
    AxiomTransition(**base)
    for missing in ("actor_did", "at", "signature"):
        with pytest.raises(ValidationError):
            AxiomTransition(**{**base, missing: None})
    with pytest.raises(ValidationError):
        AxiomTransition(**{**base, "at": datetime(2026, 10, 9, 12, 0)})  # noqa: DTZ001
    with pytest.raises(ValidationError):
        AxiomTransition(
            **{**base, "signature": {**base["signature"], "algorithm": "rsa"}}
        )


def test_signing_payload_is_canonical_utc_json(signer):
    eastern = timezone(timedelta(hours=-5))
    transition = draft(
        "proposition",
        "promoted",
        signer=signer,
        at=datetime(2026, 10, 9, 7, 0, tzinfo=eastern),
        reason="café",
    )
    payload = transition_signing_payload("p-1", None, transition)
    assert payload == (
        '{"action":"promote","actor_did":"' + signer.did + '",'
        '"at":"2026-10-09T12:00:00Z","content_iri":null,"from_status":"proposition",'
        '"proposition_id":"p-1","reason":"café","schema_version":4,'
        '"to_status":"promoted"}'
    ).encode("utf-8")


def test_history_chain_validation():
    entry = {
        "from_status": "proposition",
        "to_status": "promoted",
        "action": "migrate",
        "actor_did": None,
        "at": None,
    }
    assert proposition(axiom_status="promoted", axiom_history=[entry]).axiom_status == (
        AxiomStatus.PROMOTED
    )
    # Status must equal the history end state.
    with pytest.raises(ValidationError):
        proposition(axiom_status="promoted")
    with pytest.raises(ValidationError):
        proposition(axiom_status="demoted", axiom_history=[entry])
    # First entry must start from proposition.
    with pytest.raises(ValidationError):
        proposition(
            axiom_status="promoted",
            axiom_history=[{**entry, "from_status": "demoted"}],
        )
    # Migrate entries may only open the history.
    with pytest.raises(ValidationError):
        proposition(
            axiom_status="superseded",
            axiom_history=[
                entry,
                {**entry, "from_status": "promoted", "to_status": "superseded"},
            ],
        )


def test_broken_chain_between_signed_entries_is_rejected(signer):
    promoted = reach(AxiomStatus.PROMOTED, signer)
    extra = signed(promoted, "demoted", "superseded", signer)
    with pytest.raises(ValidationError):
        Proposition.model_validate(
            {
                **promoted.model_dump(),
                "axiom_status": "superseded",
                "axiom_history": [
                    *promoted.model_dump()["axiom_history"],
                    extra.model_dump(),
                ],
            }
        )


def test_verify_history_detects_tampering_and_skips_migrate(signer):
    value = reach(AxiomStatus.DEMOTED, signer)
    verify_history(value, VERIFIER)
    history = list(value.axiom_history)
    history[1] = history[1].model_copy(update={"reason": "edited later"})
    tampered = value.model_copy(update={"axiom_history": history})
    with pytest.raises(AxiomSignatureError):
        verify_history(tampered, VERIFIER)

    legacy = proposition(
        axiom_status="promoted",
        axiom_history=[
            {
                "from_status": "proposition",
                "to_status": "promoted",
                "action": "migrate",
                "actor_did": None,
                "at": None,
            }
        ],
    )
    verify_history(legacy, VERIFIER)
    after = advance(legacy, AxiomStatus.DEMOTED, signer)
    verify_history(after, VERIFIER)


def test_base58btc_known_vectors_and_round_trip():
    assert base58btc_encode(b"hello world") == "StV1DL6CwTryKyV"
    assert base58btc_decode("StV1DL6CwTryKyV") == b"hello world"
    assert base58btc_encode(b"\x00\x00\x01") == "112"
    assert base58btc_decode("112") == b"\x00\x00\x01"
    assert base58btc_encode(b"") == ""
    with pytest.raises(ValueError):
        base58btc_decode("0OIl")


def test_did_key_round_trip_and_ed25519_prefix(signer):
    raw = signer.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    did = did_key_from_public_bytes(raw)
    # Every Ed25519 did:key (multicodec 0xed01, base58btc) starts with z6Mk.
    assert did.startswith("did:key:z6Mk")
    assert public_bytes_from_did_key(did) == raw
    fixed = bytes(range(32))
    assert public_bytes_from_did_key(did_key_from_public_bytes(fixed)) == fixed
    with pytest.raises(ValueError):
        did_key_from_public_bytes(b"short")
    with pytest.raises(ValueError):
        public_bytes_from_did_key("did:web:example.com")
