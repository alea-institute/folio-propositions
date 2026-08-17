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


def test_v1_to_v2_migration_stub_bumps_version_and_record_still_validates():
    stored = {
        "document_id": "doc-legacy",
        "schema_version": 1,
        "propositions": [],
        "document_metadata": {"title": "Legacy"},
    }
    migrated = migrate_record(stored, target_version=2)
    assert migrated["schema_version"] == 2
    assert stored["schema_version"] == 1
    assert PropositionDocumentRecord.model_validate(migrated).schema_version == 2

