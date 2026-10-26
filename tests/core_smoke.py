"""Run with an installed core-only wheel: python -I tests/core_smoke.py.

The recording verifier checks the public protocol, not cryptographic validity.
Real Ed25519 verification belongs to the development/signing test suite.
"""

import importlib.metadata
import importlib.resources
import importlib.util
import json
import sys
import sysconfig
import unittest
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit

import folio_propositions
from folio_propositions import (
    SCHEMA_VERSION,
    AxiomSignatureError,
    AxiomStatus,
    AxiomTransition,
    Proposition,
    PropositionDocumentRecord,
    TransitionSignature,
    apply_transition,
    content_iri,
    migrate_record,
    stamp_content_iris,
    verify_history,
)

ACTOR = "did:example:reviewer"
AT = datetime(2026, 10, 26, 12, tzinfo=UTC)
IRI = "urn:folio:shard/0123456789abcdef0123456789abcdef"


class RecordingVerifier:
    def __init__(self, accepts=True):
        self.accepts = accepts
        self.calls = []

    def verify(self, payload, signature, actor_did):
        self.calls.append((payload, signature, actor_did))
        return self.accepts


def proposition(**overrides):
    return Proposition(
        **{
            "id": "p-1",
            "proposition_type": "Legal Proposition",
            "asserter": {"role": "party", "name": "Example party"},
            "validator": None,
            "disposition": "unresolved",
            **overrides,
        }
    )


def transition(sequence=0):
    return AxiomTransition(
        sequence=sequence,
        from_status="proposition" if sequence == 0 else "promoted",
        to_status="promoted" if sequence == 0 else "demoted",
        action="promote" if sequence == 0 else "demote",
        actor_did=ACTOR,
        at=AT + timedelta(minutes=sequence),
        reason="synthetic protocol check",
        signature=TransitionSignature(
            algorithm="ed25519",
            key_id=f"{ACTOR}#test",
            value=f"synthetic-signature-{sequence}",
        ),
    )


def expected_payload(sequence=0):
    # This oracle is independent of transition_signing_payload.
    return json.dumps(
        {
            "schema_version": 4,
            "proposition_id": "p-1",
            "content_iri": IRI,
            "sequence": sequence,
            "from_status": "proposition" if sequence == 0 else "promoted",
            "to_status": "promoted" if sequence == 0 else "demoted",
            "action": "promote" if sequence == 0 else "demote",
            "actor_did": ACTOR,
            "at": "2026-10-26T12:00:00Z" if sequence == 0 else "2026-10-26T12:01:00Z",
            "reason": "synthetic protocol check",
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


class CoreWheelSmoke(unittest.TestCase):
    def test_installed_wheel_provenance_and_package_data(self):
        self.assertTrue(sys.flags.isolated, "run this script with python -I")
        self.assertIsNone(importlib.util.find_spec("cryptography"))
        distribution = importlib.metadata.distribution("folio-propositions")
        imported = Path(folio_propositions.__file__).resolve()
        self.assertEqual(
            imported,
            Path(distribution.locate_file("folio_propositions/__init__.py")).resolve(),
        )
        self.assertTrue(imported.is_relative_to(Path(sys.prefix).resolve()))
        self.assertTrue(
            any(
                imported.is_relative_to(Path(sysconfig.get_path(kind)).resolve())
                for kind in ("purelib", "platlib")
            )
        )
        provenance = json.loads(distribution.read_text("direct_url.json"))
        self.assertTrue(urlsplit(provenance["url"]).path.endswith(".whl"))
        self.assertNotIn("dir_info", provenance)
        self.assertIn("archive_info", provenance)
        self.assertEqual(distribution.version, folio_propositions.__version__)
        self.assertTrue(
            importlib.resources.files("folio_propositions").joinpath("py.typed").is_file()
        )

    def test_json_round_trips_preserve_schema_and_null_actors(self):
        positions = [
            proposition(),
            proposition(
                id="p-2",
                proposition_type="judicial notice",
                asserter=None,
                validator={"role": "court"},
                disposition="accepted",
            ),
        ]
        for value in positions:
            with self.subTest(id=value.id):
                self.assertEqual(
                    Proposition.model_validate_json(value.model_dump_json()), value
                )
        record = PropositionDocumentRecord(document_id="doc-1", propositions=positions)
        restored = PropositionDocumentRecord.model_validate_json(record.model_dump_json())
        self.assertEqual(restored, record)
        self.assertEqual(SCHEMA_VERSION, 4)
        self.assertEqual(restored.schema_version, 4)
        self.assertTrue(all(item.schema_version == 4 for item in restored.propositions))
        self.assertIsNone(restored.propositions[0].validator)
        self.assertIsNone(restored.propositions[1].asserter)

    def test_migration_and_stamping_preserve_inputs(self):
        stored = {
            "document_id": "doc-v3",
            "schema_version": 3,
            "source_uri": "https://example.com/synthetic",
            "propositions": [
                {
                    **proposition().model_dump(mode="json"),
                    "schema_version": 3,
                    "start_char": 0,
                    "end_char": 4,
                    "text": "span",
                }
            ],
        }
        del stored["propositions"][0]["axiom_history"]
        before = deepcopy(stored)
        migrated = migrate_record(stored)
        self.assertEqual(stored, before)
        self.assertEqual(migrated["schema_version"], 4)
        self.assertEqual(migrated["propositions"][0]["schema_version"], 4)
        self.assertEqual(migrated["propositions"][0]["axiom_history"], [])
        record = PropositionDocumentRecord.model_validate(migrated)
        before_stamp = record.model_dump()
        stamped = stamp_content_iris(record)
        self.assertIsNot(stamped, record)
        self.assertEqual(record.model_dump(), before_stamp)
        self.assertIsNone(record.propositions[0].content_iri)
        self.assertEqual(
            stamped.propositions[0].content_iri,
            content_iri("https://example.com/synthetic", "span"),
        )

    def test_accepting_verifier_receives_payload_and_returns_new_state(self):
        value = proposition(content_iri=IRI)
        before = value.model_dump()
        entry = transition()
        verifier = RecordingVerifier()
        result = apply_transition(value, entry, verifier)
        self.assertEqual(verifier.calls, [(expected_payload(), entry.signature, ACTOR)])
        self.assertIsNot(result, value)
        self.assertEqual(value.model_dump(), before)
        self.assertEqual(result.axiom_status, AxiomStatus.PROMOTED)
        self.assertEqual(result.axiom_history, [entry])

    def test_rejecting_verifier_leaves_input_unchanged(self):
        value = proposition(content_iri=IRI)
        before = value.model_dump()
        entry = transition()
        verifier = RecordingVerifier(accepts=False)
        with self.assertRaisesRegex(AxiomSignatureError, "signature does not verify"):
            apply_transition(value, entry, verifier)
        self.assertEqual(verifier.calls, [(expected_payload(), entry.signature, ACTOR)])
        self.assertEqual(value.model_dump(), before)

    def test_history_verification_visits_each_signed_entry_in_order(self):
        value = proposition(content_iri=IRI)
        entries = [transition(0), transition(1)]
        for entry in entries:
            value = apply_transition(value, entry, RecordingVerifier())
        self.assertEqual(value.axiom_status, AxiomStatus.DEMOTED)
        verifier = RecordingVerifier()
        verify_history(value, verifier)
        self.assertEqual(
            verifier.calls,
            [
                (expected_payload(0), entries[0].signature, ACTOR),
                (expected_payload(1), entries[1].signature, ACTOR),
            ],
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
