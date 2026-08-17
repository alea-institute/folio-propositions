from folio_propositions import (
    Proposition,
    PropositionDocumentRecord,
    SCHEMA_VERSION,
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
    assert PropositionDocumentRecord.model_validate(migrated).schema_version == 2


def test_v1_to_v2_migration_accepts_bare_proposition_dict():
    stored = legacy_proposition("dissenting judicial proposition")
    migrated = migrate_record(stored, target_version=2)

    assert migrated["schema_version"] == 2
    assert migrated["proposition_type"] == "judicial proposition of law"
    assert migrated["is_new_type"] is False
    assert stored["schema_version"] == 1
    assert stored["proposition_type"] == "dissenting judicial proposition"
    assert Proposition.model_validate(migrated).schema_version == 2
