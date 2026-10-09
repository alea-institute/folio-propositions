import pytest
from pydantic import ValidationError

from folio_propositions import (
    WORKING_TAXONOMY,
    ActorRef,
    AdjudicatorRef,
    AxiomStatus,
    CitationEdge,
    Proposition,
)


def proposition(**overrides):
    values = {
        "id": "p-1",
        "proposition_type": "Legal Proposition",
        "asserter": {"role": "party", "name": "Claimant"},
        "validator": {"role": "court", "name": "Court"},
        "disposition": "accepted",
        "citation_edges": [],
    }
    values.update(overrides)
    return Proposition(**values)


def assert_round_trip(value: Proposition) -> None:
    assert Proposition.model_validate(value.model_dump()) == value


def test_classic_litigated_proposition_round_trips():
    value = proposition()
    assert value.asserter.role.value == "party"
    assert value.validator.mode.value == "ruled"
    assert_round_trip(value)


def test_open_position_has_first_class_null_validator():
    value = proposition(validator=None, disposition="unresolved")
    assert value.validator is None
    assert_round_trip(value)


@pytest.mark.parametrize(
    "validator",
    [None, {"role": "court", "mode": "pro_forma", "name": "Court"}],
)
def test_stipulation_supports_null_or_pro_forma_validator(validator):
    value = proposition(
        proposition_type="stipulation",
        asserter={"role": "both_parties"},
        validator=validator,
        disposition="accepted",
    )
    assert value.asserter.role.value == "both_parties"
    if validator is None:
        assert value.validator is None
    else:
        assert value.validator.mode.value == "pro_forma"
    assert_round_trip(value)


def test_arguendo_represents_assumption_without_falsified_fields():
    value = proposition(
        proposition_type="arguendo assumption",
        asserter={"role": "court", "assumed": True},
        validator={"role": "court", "mode": "declined"},
        disposition="assumed-arguendo",
    )
    assert value.asserter.assumed is True
    assert value.validator.mode.value == "declined"
    assert_round_trip(value)


def test_judicial_notice_has_first_class_null_asserter():
    value = proposition(
        proposition_type="judicial notice",
        asserter=None,
        validator={"role": "court"},
    )
    assert value.asserter is None
    assert_round_trip(value)


def test_disposition_accepts_assumed_arguendo_and_rejects_unknown():
    assert proposition(disposition="assumed-arguendo").disposition.value == "assumed-arguendo"
    with pytest.raises(ValidationError):
        proposition(disposition="maybe")


def test_citation_edge_is_typed_and_requires_individual_reference():
    edge = CitationEdge(
        edge_type="supports",
        authority_individual_id="individual-42",
        authority_text="Example v. Example",
    )
    value = proposition(citation_edges=[edge])
    assert value.citation_edges[0].authority_individual_id == "individual-42"
    assert_round_trip(value)

    with pytest.raises(ValidationError):
        CitationEdge(edge_type="mentions", authority_individual_id="individual-42")
    with pytest.raises(ValidationError):
        CitationEdge(edge_type="supports")


def test_registered_shapes_are_distinguishable_and_unknown_shape_is_rejected():
    litigation = proposition(shape="litigation")
    disputatio = proposition(shape="disputatio")
    assert litigation.shape != disputatio.shape
    with pytest.raises(ValidationError):
        proposition(shape="unknown-ontology")


def test_new_type_tag_is_verbatim_and_closed_taxonomy_is_enforced():
    tag = "  Experimental Mixed Question  "
    assert proposition(proposition_type=tag, is_new_type=True).proposition_type == tag
    with pytest.raises(ValidationError):
        proposition(proposition_type="experimental mixed question")


@pytest.mark.parametrize(
    "proposition_type",
    [
        "cited-authority proposition",
        "hypothetical illustration",
        "policy proposition",
    ],
)
def test_cycle_1_promoted_types_are_in_working_taxonomy(proposition_type):
    value = proposition(proposition_type=proposition_type)
    assert value.is_new_type is False


def test_working_taxonomy_maps_folio_labels_to_iris_and_local_types_to_none():
    assert WORKING_TAXONOMY["Legal Proposition"] == (
        "https://folio.openlegalstandard.org/RNICD9MDcFQJJX6nxX11Vt"
    )
    assert WORKING_TAXONOMY["Judicial Legal Conclusion"] == (
        "https://folio.openlegalstandard.org/RKTUVhpkOGaH53JFNJ4X4s"
    )
    assert WORKING_TAXONOMY["Factual Statement"] == (
        "https://folio.openlegalstandard.org/RnKWv1E6U2Ssc5SRsG14NO"
    )
    assert WORKING_TAXONOMY["Judicial Finding of Fact"] == (
        "https://folio.openlegalstandard.org/R7ZrWzdAOf6mXVtcQ49gWat"
    )
    assert WORKING_TAXONOMY["policy proposition"] is None
    with pytest.raises(TypeError):
        WORKING_TAXONOMY["new type"] = None  # type: ignore[index]
    with pytest.raises(TypeError):
        del WORKING_TAXONOMY["policy proposition"]  # type: ignore[attr-defined]


def test_pre_folio_label_requires_migration_or_explicit_new_type():
    with pytest.raises(ValidationError):
        proposition(proposition_type="party proposition of law")
    assert proposition(
        proposition_type="party proposition of law", is_new_type=True
    ).is_new_type is True


def test_rejected_dissenting_type_remains_a_free_text_new_type():
    value = proposition(
        proposition_type="dissenting judicial proposition", is_new_type=True
    )
    assert value.is_new_type is True
    with pytest.raises(ValidationError):
        proposition(proposition_type="dissenting judicial proposition")


@pytest.mark.parametrize("status", ["promoted", "demoted", "superseded"])
def test_axiom_lifecycle_states_validate_and_round_trip(status):
    legacy_entry = {
        "from_status": "proposition",
        "to_status": status,
        "action": "migrate",
        "actor_did": None,
        "at": None,
    }
    value = proposition(axiom_status=status, axiom_history=[legacy_entry])
    assert value.axiom_status == AxiomStatus(status)
    assert_round_trip(value)


def test_axiom_status_defaults_to_plain_proposition_and_rejects_unknown():
    assert proposition().axiom_status.value == "proposition"
    with pytest.raises(ValidationError):
        proposition(axiom_status="canonical")


def test_actor_and_adjudicator_can_bind_to_individuals():
    actor = ActorRef(role="plaintiff", individual_id="person-1", name="A. Party")
    adjudicator = AdjudicatorRef(role="court", individual_id="court-1")
    value = proposition(asserter=actor, validator=adjudicator)
    assert value.asserter.individual_id == "person-1"
    assert value.validator.individual_id == "court-1"


def test_text_span_is_optional_as_a_complete_group():
    without_span = proposition()
    with_span = proposition(start_char=2, end_char=9, text="holding")
    assert without_span.start_char is None
    assert with_span.text == "holding"
    with pytest.raises(ValidationError):
        proposition(start_char=2, text="partial")
    with pytest.raises(ValidationError):
        proposition(start_char=9, end_char=2, text="backwards")
