from datetime import UTC, datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from pydantic import ValidationError

from folio_propositions import (
    AXIOM_TRANSITION_ACTIONS,
    AXIOM_TRANSITIONS,
    REASON_REQUIRED_ACTIONS,
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
        "sequence": 0,
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
    position = len(value.axiom_history)
    overrides.setdefault("sequence", position)
    overrides.setdefault("at", AT + timedelta(minutes=position))
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
        ("proposition", "demoted"): "reject",
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


def test_action_table_adds_override_beside_each_default_action():
    assert {
        pair: set(actions) for pair, actions in AXIOM_TRANSITION_ACTIONS.items()
    } == {
        ("proposition", "promoted"): {"promote"},
        ("proposition", "demoted"): {"reject"},
        ("promoted", "demoted"): {"demote", "override"},
        ("demoted", "promoted"): {"promote", "override"},
        ("proposition", "superseded"): {"supersede"},
        ("promoted", "superseded"): {"supersede"},
        ("demoted", "superseded"): {"supersede"},
    }
    # Every default action is one of the pair's legal actions.
    for pair, action in AXIOM_TRANSITIONS.items():
        assert action in AXIOM_TRANSITION_ACTIONS[pair]
    assert AXIOM_TRANSITIONS.keys() == AXIOM_TRANSITION_ACTIONS.keys()
    assert set(REASON_REQUIRED_ACTIONS) == {AxiomAction.REJECT, AxiomAction.OVERRIDE}
    with pytest.raises(TypeError):
        AXIOM_TRANSITION_ACTIONS[("superseded", "promoted")] = frozenset()  # type: ignore[index]


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
        sequence=len(start.axiom_history),
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
        sequence=len(superseded.axiom_history),
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
        sequence=0,
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
            sequence=0,
            from_status="proposition",
            to_status="promoted",
            action="migrate",
            actor_did=None,
            at=None,
            signature={"algorithm": "ed25519", "key_id": "did:key:z#z", "value": "AA"},
        )


def test_signed_transitions_require_actor_time_signature_and_aware_time():
    base = {
        "sequence": 0,
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
        AxiomTransition(**{**base, "at": datetime(2026, 10, 9, 12, 0)})
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
    iri = "urn:folio:shard/0123456789abcdef0123456789abcdef"
    payload = transition_signing_payload("p-1", iri, transition)
    assert payload == (
        '{"action":"promote","actor_did":"' + signer.did + '",'
        '"at":"2026-10-09T12:00:00Z","content_iri":"' + iri + '",'
        '"from_status":"proposition","proposition_id":"p-1","reason":"café",'
        '"schema_version":4,"sequence":0,"to_status":"promoted"}'
    ).encode("utf-8")
    with pytest.raises(ValueError, match="content_iri"):
        transition_signing_payload("p-1", None, transition)


def test_history_chain_validation():
    entry = {
        "sequence": 0,
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
                {
                    **entry,
                    "sequence": 1,
                    "from_status": "promoted",
                    "to_status": "superseded",
                },
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


def test_verify_history_detects_tampering_and_gates_migrate(signer):
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
                "sequence": 0,
                "from_status": "proposition",
                "to_status": "promoted",
                "action": "migrate",
                "actor_did": None,
                "at": None,
            }
        ],
    )
    with pytest.raises(AxiomSignatureError, match="unverified legacy status"):
        verify_history(legacy, VERIFIER)
    verify_history(legacy, VERIFIER, allow_legacy_migrate=True)
    after = advance(legacy, AxiomStatus.DEMOTED, signer)
    assert after.axiom_history[1].sequence == 1
    with pytest.raises(AxiomSignatureError, match="unverified legacy status"):
        verify_history(after, VERIFIER)
    verify_history(after, VERIFIER, allow_legacy_migrate=True)


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


def test_replaying_an_old_signed_demote_is_rejected(signer):
    value = reach(AxiomStatus.DEMOTED, signer)
    repromoted = advance(value, AxiomStatus.PROMOTED, signer)
    old_demote = repromoted.axiom_history[1]
    assert [entry.sequence for entry in repromoted.axiom_history] == [0, 1, 2]

    with pytest.raises(IllegalAxiomTransition, match="sequence"):
        apply_transition(repromoted, old_demote, VERIFIER)
    # Bumping the sequence breaks the signature (and the stale time is refused).
    bumped = old_demote.model_copy(update={"sequence": 3})
    with pytest.raises(IllegalAxiomTransition, match="strictly later"):
        apply_transition(repromoted, bumped, VERIFIER)
    later = old_demote.model_copy(update={"sequence": 3, "at": AT + timedelta(days=1)})
    with pytest.raises(AxiomSignatureError):
        apply_transition(repromoted, later, VERIFIER)
    # Hand-appending the replayed entry to stored data fails model validation.
    with pytest.raises(ValidationError):
        Proposition.model_validate(
            {
                **repromoted.model_dump(),
                "axiom_status": "demoted",
                "axiom_history": [
                    *repromoted.model_dump()["axiom_history"],
                    old_demote.model_dump(),
                ],
            }
        )


def test_signing_payload_binds_sequence(signer):
    iri = content_iri("https://example.com/doc", "span")
    first = draft("proposition", "promoted", signer=signer, sequence=0)
    second = draft("proposition", "promoted", signer=signer, sequence=1)
    assert transition_signing_payload("p", iri, first) != transition_signing_payload(
        "p", iri, second
    )


def test_history_requires_index_sequence_and_increasing_signed_times(signer):
    value = reach(AxiomStatus.DEMOTED, signer)
    dumped = value.model_dump()
    wrong_sequence = [dict(entry) for entry in dumped["axiom_history"]]
    wrong_sequence[1]["sequence"] = 5
    with pytest.raises(ValidationError, match="sequence"):
        Proposition.model_validate({**dumped, "axiom_history": wrong_sequence})
    same_time = [dict(entry) for entry in dumped["axiom_history"]]
    same_time[1]["at"] = same_time[0]["at"]
    with pytest.raises(ValidationError, match="strictly later"):
        Proposition.model_validate({**dumped, "axiom_history": same_time})


def test_apply_transition_refuses_non_increasing_time(signer):
    promoted = reach(AxiomStatus.PROMOTED, signer)
    stale = signed(promoted, "promoted", "demoted", signer, at=AT)
    with pytest.raises(IllegalAxiomTransition, match="strictly later"):
        apply_transition(promoted, stale, VERIFIER)


def test_signed_lifecycle_requires_stamped_content_iri(signer):
    unstamped = proposition(content_iri=None)
    with pytest.raises(ValueError, match="content_iri"):
        sign_transition(
            unstamped.id,
            None,
            draft("proposition", "promoted", signer=signer),
            signer.key,
            signer.key_id,
        )
    # A transition signed for the stamped twin cannot be applied unstamped.
    transition = signed(proposition(), "proposition", "promoted", signer)
    with pytest.raises(AxiomSignatureError, match="content_iri"):
        apply_transition(unstamped, transition, VERIFIER)
    promoted = reach(AxiomStatus.PROMOTED, signer)
    stripped = promoted.model_copy(update={"content_iri": None})
    with pytest.raises(AxiomSignatureError, match="content_iri"):
        verify_history(stripped, VERIFIER)


def test_overlong_did_key_and_key_id_are_rejected_before_decoding(signer):
    with pytest.raises(ValueError, match="exceeds"):
        base58btc_decode("2" * 129)
    with pytest.raises(ValueError, match="too long"):
        public_bytes_from_did_key("did:key:z" + "2" * 10_000)
    value = proposition()
    transition = signed(value, "proposition", "promoted", signer)
    payload = transition_signing_payload(value.id, value.content_iri, transition)
    long_did = "did:key:z" + "2" * 10_000
    long_signature = transition.signature.model_copy(update={"key_id": long_did + "#k"})
    assert VERIFIER.verify(payload, long_signature, long_did) is False
    long_fragment = transition.signature.model_copy(
        update={"key_id": signer.did + "#" + "z" * 10_000}
    )
    assert VERIFIER.verify(payload, long_fragment, signer.did) is False
    assert VERIFIER.verify(payload, transition.signature, signer.did) is True


LEGAL_TRIPLES = [
    (from_status, to_status, action)
    for (from_status, to_status), actions in AXIOM_TRANSITION_ACTIONS.items()
    for action in sorted(actions, key=lambda value: value.value)
]


@pytest.mark.parametrize(("from_status", "to_status", "action"), LEGAL_TRIPLES)
def test_every_legal_action_applies_and_verifies(
    from_status, to_status, action, signer
):
    start = reach(from_status, signer)
    transition = signed(start, from_status, to_status, signer, action=action)
    result = apply_transition(start, transition, VERIFIER)
    assert result.axiom_status == to_status
    assert result.axiom_history[-1].action == action
    verify_history(result, VERIFIER)
    assert Proposition.model_validate_json(result.model_dump_json()) == result


def test_reject_moves_an_unreviewed_proposition_to_demoted(signer):
    value = proposition()
    transition = signed(
        value,
        "proposition",
        "demoted",
        signer,
        action="reject",
        reason="encodings disagree on subd. 7",
    )
    rejected = apply_transition(value, transition, VERIFIER)
    assert rejected.axiom_status == AxiomStatus.DEMOTED
    entry = rejected.axiom_history[0]
    assert entry.action == AxiomAction.REJECT
    assert entry.actor_did == signer.did
    assert entry.reason == "encodings disagree on subd. 7"
    # A rejected proposition can still be superseded by newer content.
    superseded = advance(rejected, AxiomStatus.SUPERSEDED, signer)
    assert superseded.axiom_status == AxiomStatus.SUPERSEDED
    verify_history(superseded, VERIFIER)


def test_reject_is_the_only_action_from_proposition_to_demoted():
    for action in (AxiomAction.DEMOTE, AxiomAction.OVERRIDE, AxiomAction.PROMOTE):
        with pytest.raises(ValidationError, match="requires action"):
            draft("proposition", "demoted", action=action)


def test_reject_cannot_leave_a_promoted_or_demoted_status():
    for from_status in ("promoted", "demoted", "superseded"):
        with pytest.raises(ValidationError):
            draft(from_status, "demoted", action=AxiomAction.REJECT)


def test_override_demotes_a_promoted_axiom_and_records_author_and_reason(signer):
    promoted = reach(AxiomStatus.PROMOTED, signer)
    overseer = Signer()
    transition = signed(
        promoted,
        "promoted",
        "demoted",
        overseer,
        action="override",
        reason="audit sample 12 shows the rule misreads subd. 3",
    )
    overridden = apply_transition(promoted, transition, VERIFIER)
    assert overridden.axiom_status == AxiomStatus.DEMOTED
    entry = overridden.axiom_history[-1]
    assert entry.action == AxiomAction.OVERRIDE
    assert entry.actor_did == overseer.did
    assert entry.actor_did != promoted.axiom_history[0].actor_did
    assert entry.reason == "audit sample 12 shows the rule misreads subd. 3"
    verify_history(overridden, VERIFIER)


def test_override_can_reinstate_a_demoted_axiom(signer):
    demoted = reach(AxiomStatus.DEMOTED, signer)
    transition = signed(
        demoted,
        "demoted",
        "promoted",
        signer,
        action="override",
        reason="verification failure was a solver timeout",
    )
    reinstated = apply_transition(demoted, transition, VERIFIER)
    assert reinstated.axiom_status == AxiomStatus.PROMOTED
    assert reinstated.axiom_history[-1].action == AxiomAction.OVERRIDE


@pytest.mark.parametrize(
    ("from_status", "to_status"),
    [
        ("proposition", "promoted"),
        ("proposition", "superseded"),
        ("promoted", "superseded"),
        ("demoted", "superseded"),
        ("superseded", "promoted"),
        ("superseded", "demoted"),
    ],
)
def test_override_is_refused_outside_promoted_and_demoted(from_status, to_status):
    with pytest.raises(ValidationError):
        draft(from_status, to_status, action=AxiomAction.OVERRIDE)


@pytest.mark.parametrize(
    ("from_status", "to_status", "action"),
    [
        ("proposition", "demoted", AxiomAction.REJECT),
        ("promoted", "demoted", AxiomAction.OVERRIDE),
        ("demoted", "promoted", AxiomAction.OVERRIDE),
    ],
)
@pytest.mark.parametrize("reason", [None, "", "   \n\t"])
def test_reject_and_override_require_a_reason(from_status, to_status, action, reason):
    with pytest.raises(ValidationError, match="reason"):
        draft(from_status, to_status, action=action, reason=reason)
    with pytest.raises(ValidationError, match="reason"):
        AxiomTransition(
            sequence=0,
            from_status=from_status,
            to_status=to_status,
            action=action,
            actor_did="did:key:z6MkExample",
            at=AT,
            reason=reason,
            signature={"algorithm": "ed25519", "key_id": "did:key:z#z", "value": "AA"},
        )


def test_forged_reasonless_override_is_refused_by_apply_transition(signer):
    promoted = reach(AxiomStatus.PROMOTED, signer)
    forged = AxiomTransition.model_construct(
        sequence=len(promoted.axiom_history),
        from_status=AxiomStatus.PROMOTED,
        to_status=AxiomStatus.DEMOTED,
        action=AxiomAction.OVERRIDE,
        actor_did=signer.did,
        at=AT + timedelta(days=1),
        reason=None,
        signature=TransitionSignature(
            algorithm="ed25519", key_id=signer.key_id, value="AA"
        ),
    )
    with pytest.raises(IllegalAxiomTransition, match="reason"):
        apply_transition(promoted, forged, VERIFIER)


def test_action_is_signed_so_demote_cannot_be_relabelled_override(signer):
    promoted = reach(AxiomStatus.PROMOTED, signer)
    demote = signed(promoted, "promoted", "demoted", signer)
    relabelled = demote.model_copy(update={"action": AxiomAction.OVERRIDE})
    with pytest.raises(AxiomSignatureError):
        apply_transition(promoted, relabelled, VERIFIER)


def test_override_payload_is_canonical_utc_json(signer):
    transition = draft(
        "promoted",
        "demoted",
        action="override",
        signer=signer,
        sequence=1,
        reason="overseer override",
    )
    iri = "urn:folio:shard/0123456789abcdef0123456789abcdef"
    assert transition_signing_payload("p-1", iri, transition) == (
        '{"action":"override","actor_did":"' + signer.did + '",'
        '"at":"2026-10-09T12:00:00Z","content_iri":"' + iri + '",'
        '"from_status":"promoted","proposition_id":"p-1",'
        '"reason":"overseer override","schema_version":4,"sequence":1,'
        '"to_status":"demoted"}'
    ).encode("utf-8")
