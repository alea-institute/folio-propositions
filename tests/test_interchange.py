import pytest

from folio_propositions import (
    SCHEMA_VERSION,
    Proposition,
    PropositionDocumentRecord,
    migrate_record,
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
    # must continue through v3 before model validation.


def test_v1_to_v2_migration_accepts_bare_proposition_dict():
    stored = legacy_proposition("dissenting judicial proposition")
    migrated = migrate_record(stored, target_version=3)

    assert migrated["schema_version"] == 3
    assert migrated["proposition_type"] == "Judicial Legal Conclusion"
    assert migrated["is_new_type"] is False
    assert stored["schema_version"] == 1
    assert stored["proposition_type"] == "dissenting judicial proposition"
    assert Proposition.model_validate(migrated).schema_version == 3


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

    assert migrated["schema_version"] == 3
    assert [item["proposition_type"] for item in migrated["propositions"]] == [
        "Legal Proposition",
        "Judicial Legal Conclusion",
        "Factual Statement",
        "Judicial Finding of Fact",
        "policy proposition",
    ]
    assert all(item["schema_version"] == 3 for item in migrated["propositions"])
    assert stored["schema_version"] == 2
    assert PropositionDocumentRecord.model_validate(migrated).schema_version == 3


def test_v2_to_v3_preserves_custom_type_that_collides_with_new_taxonomy():
    stored = legacy_proposition("Legal Proposition", True)
    stored["schema_version"] = 2

    migrated = migrate_record(stored)

    assert migrated["proposition_type"] == "Legal Proposition"
    assert migrated["is_new_type"] is True


def test_document_shaped_v1_record_migrates_to_v3_and_is_idempotent():
    stored = {
        "document_id": "doc-v1",
        "schema_version": 1,
        "propositions": [legacy_proposition("dissenting judicial proposition")],
    }

    migrated = migrate_record(stored)

    assert migrated["schema_version"] == 3
    assert migrated["propositions"][0]["schema_version"] == 3
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
