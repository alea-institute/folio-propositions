"""Exercise the checkout example with real, ephemeral signing keys."""

import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from folio_propositions import (
    AxiomSignatureError,
    AxiomStatus,
    DidKeyEd25519Verifier,
    IllegalAxiomTransition,
    apply_transition,
    content_iri,
    transition_signing_payload,
)

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "migration_v4.py"


@pytest.fixture(scope="module")
def example():
    spec = importlib.util.spec_from_file_location("migration_v4", EXAMPLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def signer(example):
    return example.DemoSigner()


@pytest.fixture
def policy(example, signer):
    return example.AuthorizedVerifier({signer.did})


@pytest.fixture
def base(example):
    return example.migrate_demo_record(example.v3_record())


def saved_record(base, proposition):
    return base.model_copy(update={"propositions": [proposition]}).model_dump_json()


def test_native_walkthrough_replays_unchanged_signed_entries(example):
    restored, replayed = example.native_demo()
    final = restored.propositions[0]
    assert final.axiom_status == AxiomStatus.SUPERSEDED
    assert [entry.sequence for entry in final.axiom_history] == [0, 1, 2, 3]
    assert [entry.action.value for entry in final.axiom_history] == [
        "promote",
        "demote",
        "promote",
        "supersede",
    ]
    assert final.content_iri == content_iri(restored.source_uri, final.text)
    assert replayed == final
    assert all(a is b for a, b in zip(replayed.axiom_history, final.axiom_history))


def test_migration_and_append_leave_inputs_unchanged(example, signer, policy):
    stored = example.v3_record()
    original = deepcopy(stored)
    record = example.migrate_demo_record(stored)
    before = record.model_dump_json()
    start = record.propositions[0]
    promoted = apply_transition(
        start, signer.transition(start, AxiomStatus.PROMOTED), policy
    )
    assert stored == original
    assert record.model_dump_json() == before
    assert record.schema_version == start.schema_version == 4
    assert start.axiom_history == []
    assert promoted.axiom_status == AxiomStatus.PROMOTED


@pytest.mark.parametrize("empty_policy", [False, True])
def test_valid_but_unauthorized_signature_fails_apply_and_reload(
    example, base, signer, empty_policy
):
    outsider = example.DemoSigner()
    policy = example.AuthorizedVerifier(set() if empty_policy else {signer.did})
    start = base.propositions[0]
    entry = outsider.transition(start, AxiomStatus.PROMOTED)
    bare_verifier = DidKeyEd25519Verifier()
    assert bare_verifier.verify(
        transition_signing_payload(start.id, start.content_iri, entry),
        entry.signature,
        outsider.did,
    )
    with pytest.raises(AxiomSignatureError):
        apply_transition(start, entry, policy)
    signed_by_outsider = apply_transition(start, entry, bare_verifier)
    with pytest.raises(AxiomSignatureError):
        example.load_demo_record(saved_record(base, signed_by_outsider), policy)


def test_policy_copies_allowlist(example, base, signer):
    allowed = {signer.did}
    policy = example.AuthorizedVerifier(allowed)
    allowed.clear()
    start = base.propositions[0]
    entry = signer.transition(start, AxiomStatus.PROMOTED)
    assert apply_transition(start, entry, policy).axiom_status == AxiomStatus.PROMOTED
    outsider = example.DemoSigner()
    allowed.add(outsider.did)
    with pytest.raises(AxiomSignatureError):
        apply_transition(
            start, outsider.transition(start, AxiomStatus.PROMOTED), policy
        )


def test_allowed_actor_still_needs_valid_signature(example, base, signer, policy):
    start = base.propositions[0]
    entry = signer.transition(start, AxiomStatus.PROMOTED)
    tampered = entry.model_copy(update={"reason": "changed after signing"})
    with pytest.raises(AxiomSignatureError):
        apply_transition(start, tampered, policy)
    promoted = apply_transition(start, entry, policy)
    data = json.loads(saved_record(base, promoted))
    data["propositions"][0]["axiom_history"][0]["reason"] = tampered.reason
    with pytest.raises(AxiomSignatureError):
        example.load_demo_record(json.dumps(data), policy)


def test_reload_checks_earlier_actors_against_current_policy(
    example, base, signer, policy
):
    earlier = example.DemoSigner()
    both = example.AuthorizedVerifier({signer.did, earlier.did})
    start = base.propositions[0]
    promoted = apply_transition(
        start, earlier.transition(start, AxiomStatus.PROMOTED), both
    )
    demoted = apply_transition(
        promoted, signer.transition(promoted, AxiomStatus.DEMOTED), policy
    )
    saved = saved_record(base, demoted)
    assert example.load_demo_record(saved, both).propositions[0] == demoted
    with pytest.raises(AxiomSignatureError):
        example.load_demo_record(saved, policy)


@pytest.mark.parametrize("edit", ["source", "text", "sequence", "status", "time"])
def test_reload_validates_record_before_consuming_history(example, edit):
    record, _ = example.native_demo()
    data = record.model_dump(mode="json")
    proposition = data["propositions"][0]
    if edit == "source":
        data["source_uri"] = "https://example.org/different"
    elif edit == "text":
        proposition["text"] = "A different synthetic span."
    elif edit == "sequence":
        proposition["axiom_history"][0]["sequence"] = 9
    elif edit == "status":
        proposition["axiom_status"] = "demoted"
    else:
        proposition["axiom_history"][1]["at"] = proposition["axiom_history"][0]["at"]
    # An empty policy would raise AxiomSignatureError if verification ran first.
    with pytest.raises(ValidationError):
        example.load_demo_record(json.dumps(data), example.AuthorizedVerifier(set()))


def test_old_demotion_and_cross_identity_replay_fail(example, base, signer, policy):
    start = base.propositions[0]
    promotion = signer.transition(start, AxiomStatus.PROMOTED)
    promoted = apply_transition(start, promotion, policy)
    demotion = signer.transition(promoted, AxiomStatus.DEMOTED)
    demoted = apply_transition(promoted, demotion, policy)
    promoted_again = apply_transition(
        demoted, signer.transition(demoted, AxiomStatus.PROMOTED), policy
    )
    before = promoted_again.model_dump_json()
    with pytest.raises(IllegalAxiomTransition, match="sequence"):
        apply_transition(promoted_again, demotion, policy)
    assert promoted_again.model_dump_json() == before
    for changes in (
        {"id": "different-proposition"},
        {"content_iri": content_iri("https://example.org/other", start.text)},
    ):
        with pytest.raises(AxiomSignatureError):
            apply_transition(start.model_copy(update=changes), promotion, policy)
