import pytest
from pydantic import ValidationError

from folio_propositions import (
    SCHEMA_VERSION,
    Proposition,
    PropositionDocumentRecord,
    content_iri,
    migrate_record,
    stamp_content_iris,
)


def test_interchange_record_json_round_trip_preserves_schema_version():
    record = PropositionDocumentRecord(
        document_id="doc-1",
        propositions=[
            Proposition(
                id="p-1",
                proposition_type="judicial notice",
                asserter=None,
                validator={"role": "court"},
                disposition="accepted",
                citation_edges=[],
            )
        ],
        document_metadata={"title": "Example", "word_count": 1200},
        generator={"tool": "folio-enrich", "version": "0.1.0"},
    )
    restored = PropositionDocumentRecord.model_validate_json(record.model_dump_json())
    assert restored == record
    assert restored.schema_version == SCHEMA_VERSION


def legacy_proposition(proposition_type, is_new_type=True):
    return {
        "id": f"p-{proposition_type}",
        "schema_version": 1,
        "proposition_type": proposition_type,
        "is_new_type": is_new_type,
        "asserter": {"role": "court"},
        "validator": {"role": "court"},
        "disposition": "accepted",
    }


def test_v1_to_v2_migration_normalizes_cycle_1_record():
    affected_types = [
        "dissenting judicial proposition",
        "hypothetical party claim",
        "cited-authority proposition",
        "hypothetical illustration",
        "policy proposition",
        "definitional proposition",
    ]
    stored = {
        "document_id": "doc-legacy",
        "schema_version": 1,
        "propositions": [legacy_proposition(value) for value in affected_types],
        "document_metadata": {"title": "Legacy"},
    }
    migrated = migrate_record(stored, target_version=2)
    assert migrated["schema_version"] == 2
    assert stored["schema_version"] == 1
    assert [item["proposition_type"] for item in migrated["propositions"]] == [
        "judicial proposition of law",
        "hypothetical illustration",
        "cited-authority proposition",
        "hypothetical illustration",
        "policy proposition",
        "definitional proposition",
    ]
    assert [item["is_new_type"] for item in migrated["propositions"]] == [
        False,
        False,
        False,
        False,
        False,
        True,
    ]
    assert all(item["schema_version"] == 2 for item in migrated["propositions"])
    # Current models validate the current taxonomy, so a historical v2 payload
    # must continue through v3 and v4 before model validation.


def test_v1_to_v2_migration_accepts_bare_proposition_dict():
    stored = legacy_proposition("dissenting judicial proposition")
    at_v3 = migrate_record(stored, target_version=3)
    migrated = migrate_record(stored)

    assert at_v3["schema_version"] == 3
    assert at_v3["proposition_type"] == "Judicial Legal Conclusion"
    assert migrated["schema_version"] == 4
    assert migrated["proposition_type"] == "Judicial Legal Conclusion"
    assert migrated["is_new_type"] is False
    assert migrated["axiom_history"] == []
    assert stored["schema_version"] == 1
    assert stored["proposition_type"] == "dissenting judicial proposition"
    assert Proposition.model_validate(migrated).schema_version == 4


def test_v2_to_v3_migration_aligns_folio_labels_and_preserves_local_types():
    stored = {
        "document_id": "doc-v2",
        "schema_version": 2,
        "propositions": [
            legacy_proposition("party proposition of law", False),
            legacy_proposition("judicial proposition of law", False),
            legacy_proposition("party proposition of fact", False),
            legacy_proposition("judicial proposition of fact", False),
            legacy_proposition("policy proposition", False),
        ],
    }
    for proposition in stored["propositions"]:
        proposition["schema_version"] = 2

    migrated = migrate_record(stored)

    assert migrated["schema_version"] == 4
    assert [item["proposition_type"] for item in migrated["propositions"]] == [
        "Legal Proposition",
        "Judicial Legal Conclusion",
        "Factual Statement",
        "Judicial Finding of Fact",
        "policy proposition",
    ]
    assert all(item["schema_version"] == 4 for item in migrated["propositions"])
    assert stored["schema_version"] == 2
    assert PropositionDocumentRecord.model_validate(migrated).schema_version == 4


def test_v2_to_v3_preserves_custom_type_that_collides_with_new_taxonomy():
    stored = legacy_proposition("Legal Proposition", True)
    stored["schema_version"] = 2

    migrated = migrate_record(stored)

    assert migrated["proposition_type"] == "Legal Proposition"
    assert migrated["is_new_type"] is True


def test_document_shaped_v1_record_migrates_to_v4_and_is_idempotent():
    stored = {
        "document_id": "doc-v1",
        "schema_version": 1,
        "propositions": [legacy_proposition("dissenting judicial proposition")],
    }

    migrated = migrate_record(stored)

    assert migrated["schema_version"] == 4
    assert migrated["propositions"][0]["schema_version"] == 4
    assert migrated["propositions"][0]["proposition_type"] == (
        "Judicial Legal Conclusion"
    )
    assert migrate_record(migrated) == migrated


def test_migrate_record_preserves_value_error_for_invalid_version_type():
    with pytest.raises(ValueError, match="schema_version must be an integer"):
        migrate_record({"schema_version": "2"})


def test_migrate_record_rejects_mixed_parent_and_proposition_versions():
    stored = {
        "document_id": "partial-v3",
        "schema_version": 3,
        "propositions": [legacy_proposition("party proposition of law", True)],
    }
    stored["propositions"][0]["schema_version"] = 2

    with pytest.raises(ValueError, match="proposition schema_version"):
        migrate_record(stored)


SOURCE_URI = "https://example.com/opinions/palsgraf"


def spanned(proposition_id, text, **overrides):
    values = {
        "id": proposition_id,
        "start_char": 0,
        "end_char": len(text),
        "text": text,
        "proposition_type": "Legal Proposition",
        "asserter": {"role": "party"},
        "validator": None,
        "disposition": "unresolved",
    }
    values.update(overrides)
    return Proposition(**values)


def test_stamp_content_iris_matches_identity_and_leaves_input_untouched():
    record = PropositionDocumentRecord(
        document_id="doc-identity",
        source_uri=SOURCE_URI,
        propositions=[
            spanned("p-1", "The risk reasonably to be perceived defines the duty."),
            spanned(
                "p-2",
                "The risk reasonably to be perceived defines the duty.",
                proposition_type="Factual Statement",
            ),
            Proposition(
                id="p-3",
                proposition_type="judicial notice",
                asserter=None,
                validator={"role": "court"},
                disposition="accepted",
            ),
        ],
    )

    stamped = stamp_content_iris(record)

    expected = content_iri(
        SOURCE_URI, "The risk reasonably to be perceived defines the duty."
    )
    assert [item.content_iri for item in stamped.propositions] == [
        expected,
        expected,  # identity is per (source, span), not per proposition type
        None,
    ]
    assert all(item.content_iri is None for item in record.propositions)
    restored = PropositionDocumentRecord.model_validate_json(stamped.model_dump_json())
    assert restored == stamped


def test_stamp_content_iris_requires_source_uri():
    record = PropositionDocumentRecord(
        document_id="doc", propositions=[spanned("p-1", "text")]
    )
    with pytest.raises(ValueError, match="source_uri"):
        stamp_content_iris(record)


def test_record_rejects_content_iri_that_does_not_match_source_and_text():
    wrong = content_iri("https://example.com/other", "text")
    with pytest.raises(ValidationError, match="p-bad"):
        PropositionDocumentRecord(
            document_id="doc",
            source_uri=SOURCE_URI,
            propositions=[spanned("p-bad", "text", content_iri=wrong)],
        )
    # Without a source URI the record cannot check, so it accepts the stamp.
    PropositionDocumentRecord(
        document_id="doc", propositions=[spanned("p-ok", "text", content_iri=wrong)]
    )


def test_record_rejects_mismatched_proposition_schema_version():
    with pytest.raises(ValidationError, match="schema_version"):
        PropositionDocumentRecord(
            document_id="doc",
            propositions=[spanned("p-old", "text", schema_version=3)],
        )


@pytest.mark.parametrize(
    "bad_iri",
    [
        "urn:folio:shard/ABCDEF0123456789abcdef0123456789",
        "urn:folio:shard/abc",
        "urn:folio:other/0123456789abcdef0123456789abcdef",
        "urn:folio:shard/0123456789abcdef0123456789abcdef0",
    ],
)
def test_proposition_rejects_malformed_content_iri(bad_iri):
    with pytest.raises(ValidationError, match="content_iri"):
        spanned("p", "text", content_iri=bad_iri)


def test_v3_to_v4_migration_adds_history_and_legacy_migrate_entry():
    stored = {
        "document_id": "doc-v3",
        "schema_version": 3,
        "propositions": [
            {**legacy_proposition("Legal Proposition", False), "schema_version": 3},
            {
                **legacy_proposition("Judicial Legal Conclusion", False),
                "schema_version": 3,
                "axiom_status": "promoted",
            },
        ],
    }

    migrated = migrate_record(stored)

    assert migrated["schema_version"] == 4
    first, second = migrated["propositions"]
    assert first["axiom_history"] == []
    assert "content_iri" not in first
    assert second["axiom_history"] == [
        {
            "sequence": 0,
            "from_status": "proposition",
            "to_status": "promoted",
            "action": "migrate",
            "actor_did": None,
            "at": None,
            "reason": "pre-v4 status without recorded transition",
            "signature": None,
        }
    ]
    record = PropositionDocumentRecord.model_validate(migrated)
    assert record.propositions[1].axiom_status.value == "promoted"
    assert record.propositions[1].axiom_history[0].action.value == "migrate"
    assert "axiom_history" not in stored["propositions"][0]
    assert migrate_record(migrated) == migrated


def test_v3_to_v4_migration_accepts_bare_proposition_dict():
    stored = {
        **legacy_proposition("policy proposition", False),
        "schema_version": 3,
        "axiom_status": "superseded",
    }

    migrated = migrate_record(stored)

    assert migrated["schema_version"] == 4
    assert migrated["axiom_history"][0]["to_status"] == "superseded"
    assert Proposition.model_validate(migrated).axiom_status.value == "superseded"


def test_v1_record_with_axiom_status_chains_to_v4():
    stored = {
        "document_id": "doc-v1",
        "schema_version": 1,
        "propositions": [
            {
                **legacy_proposition("dissenting judicial proposition"),
                "axiom_status": "demoted",
            }
        ],
    }

    migrated = migrate_record(stored)

    proposition = migrated["propositions"][0]
    assert proposition["schema_version"] == 4
    assert proposition["proposition_type"] == "Judicial Legal Conclusion"
    assert proposition["axiom_history"][0]["to_status"] == "demoted"
    assert PropositionDocumentRecord.model_validate(migrated).schema_version == 4


def test_stamp_refuses_to_change_iri_bound_by_signed_history():
    from datetime import UTC, datetime

    old_iri = content_iri("https://example.com/old", "text")
    entry = {
        "sequence": 0,
        "from_status": "proposition",
        "to_status": "promoted",
        "action": "promote",
        "actor_did": "did:key:z6MkExample",
        "at": datetime(2026, 10, 9, tzinfo=UTC),
        "signature": {
            "algorithm": "ed25519",
            "key_id": "did:key:z6MkExample#k",
            "value": "AA",
        },
    }
    signed_prop = spanned(
        "p-signed",
        "text",
        content_iri=old_iri,
        axiom_status="promoted",
        axiom_history=[entry],
    )
    record = PropositionDocumentRecord(document_id="doc", propositions=[signed_prop])
    record = record.model_copy(update={"source_uri": SOURCE_URI})
    with pytest.raises(ValueError, match="p-signed"):
        stamp_content_iris(record)

    # Same IRI is fine, and an unsigned proposition may be re-stamped freely.
    same = record.model_copy(update={"source_uri": "https://example.com/old"})
    assert stamp_content_iris(same).propositions[0].content_iri == old_iri
    unsigned = record.model_copy(
        update={"propositions": [spanned("p-free", "text", content_iri=old_iri)]}
    )
    assert stamp_content_iris(unsigned).propositions[0].content_iri == content_iri(
        SOURCE_URI, "text"
    )


@pytest.mark.parametrize("text", ["", "   ", " \r\n\t "])
def test_stamp_skips_empty_text_and_record_rejects_iri_on_empty_text(text):
    record = PropositionDocumentRecord(
        document_id="doc",
        source_uri=SOURCE_URI,
        propositions=[spanned("p-empty", text), spanned("p-full", "text")],
    )
    stamped = stamp_content_iris(record)
    assert stamped.propositions[0].content_iri is None
    assert stamped.propositions[1].content_iri == content_iri(SOURCE_URI, "text")

    iri = content_iri(SOURCE_URI, "text")
    with pytest.raises(ValidationError, match="p-empty"):
        PropositionDocumentRecord(
            document_id="doc",
            source_uri=SOURCE_URI,
            propositions=[spanned("p-empty", text, content_iri=iri)],
        )


def test_v3_to_v4_migration_with_null_axiom_status_invents_no_history():
    stored = {
        **legacy_proposition("Legal Proposition", False),
        "schema_version": 3,
        "axiom_status": None,
    }

    migrated = migrate_record(stored)

    assert migrated["axiom_history"] == []
    assert migrated["axiom_status"] is None  # left for model validation to judge
    with pytest.raises(ValidationError):
        Proposition.model_validate(migrated)


def test_v3_to_v4_migration_preserves_existing_history_and_numbers_it():
    existing = [
        {
            "from_status": "proposition",
            "to_status": "promoted",
            "action": "migrate",
            "actor_did": None,
            "at": None,
            "reason": "already recorded",
            "signature": None,
        }
    ]
    stored = {
        **legacy_proposition("Legal Proposition", False),
        "schema_version": 3,
        "axiom_status": "promoted",
        "axiom_history": existing,
    }

    migrated = migrate_record(stored)

    assert migrated["axiom_history"] == [{**existing[0], "sequence": 0}]
    assert "sequence" not in stored["axiom_history"][0]
    assert Proposition.model_validate(migrated).axiom_history[0].reason == (
        "already recorded"
    )
