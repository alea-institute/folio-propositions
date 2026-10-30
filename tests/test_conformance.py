"""The shipped conformance files must match the implementation they describe."""

import importlib.util
import json
import sys
import unicodedata
from datetime import UTC, datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from folio_propositions import (
    ActorRole,
    AxiomAction,
    AxiomStatus,
    Proposition,
    PropositionDocumentRecord,
    __version__,
    content_identity,
    content_iri,
    document_source_uri,
)

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_conformance.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_conformance", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


generator = _load_generator()

# Unicode White_Space: what Rust's str::trim() strips. Python's str.strip()
# also strips U+001C-U+001F.
UNICODE_WHITE_SPACE = "".join(
    chr(code)
    for code in [
        *range(0x09, 0x0E),
        0x20,
        0x85,
        0xA0,
        0x1680,
        *range(0x2000, 0x200B),
        0x2028,
        0x2029,
        0x202F,
        0x205F,
        0x3000,
    ]
)
SEPARATORS = "\u001c\u001d\u001e\u001f"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", sorted(generator.outputs(), key=str), ids=str)
def test_committed_conformance_files_match_the_generator(path):
    expected = generator.outputs()[path]
    assert path.read_text(encoding="utf-8") == expected, (
        f"{path.relative_to(ROOT)} is stale; run python scripts/generate_conformance.py"
    )


def test_generator_check_mode_passes():
    assert generator.main(["--check"]) == 0


VECTORS = load(generator.IDENTITY_VECTORS)


def test_vector_file_is_version_stamped():
    assert VECTORS["format"] == "folio-propositions/identity-vectors"
    assert VECTORS["format_version"] == 1
    assert VECTORS["recipe"] == "folio-content-iri-v1"
    assert VECTORS["generated_by"] == f"folio-propositions {__version__}"
    ids = [
        vector["id"]
        for section in (
            "content_identity",
            "content_identity_errors",
            "document_source_uri",
        )
        for vector in VECTORS[section]
    ]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize(
    "vector", VECTORS["content_identity"], ids=lambda vector: vector["id"]
)
def test_identity_vector_reproduces_every_step(vector):
    source_uri = vector["input"]["source_uri"]
    span = vector["input"]["span"]
    expected = vector["expected"]
    assert bytes.fromhex(vector["input"]["source_uri_utf8_hex"]).decode() == source_uri
    assert bytes.fromhex(vector["input"]["span_utf8_hex"]).decode() == span
    payload = bytes.fromhex(expected["payload_utf8_hex"])
    assert payload == (
        expected["normalized_source_uri"] + "\n" + expected["normalized_span"]
    ).encode("utf-8")
    identity = content_identity(source_uri, span)
    assert identity.provenance_hash == expected["provenance_hash"]
    assert identity.iri == expected["iri"]
    assert expected["iri"] == "urn:folio:shard/" + expected["provenance_hash"][:32]


@pytest.mark.parametrize(
    "vector", VECTORS["content_identity_errors"], ids=lambda vector: vector["id"]
)
def test_error_vectors_raise(vector):
    with pytest.raises(ValueError, match=vector["expected"]["message"]):
        content_identity(vector["input"]["source_uri"], vector["input"]["span"])


@pytest.mark.parametrize(
    "vector", VECTORS["document_source_uri"], ids=lambda vector: vector["id"]
)
def test_document_source_uri_vectors(vector):
    assert document_source_uri(vector["input"]["text"]) == vector["expected"]["uri"]


def _by_id(vector_id: str) -> dict:
    return next(v for v in VECTORS["content_identity"] if v["id"] == vector_id)


@pytest.mark.parametrize(
    ("nfc_id", "nfd_id"), [("span-nfc", "span-nfd"), ("uri-path-nfc", "uri-path-nfd")]
)
def test_nfc_and_nfd_vector_pairs_differ_in_input_and_share_an_iri(nfc_id, nfd_id):
    nfc, nfd = _by_id(nfc_id), _by_id(nfd_id)
    assert nfc["input"] != nfd["input"]
    assert nfc["expected"]["iri"] == nfd["expected"]["iri"]

    def joined(vector):
        return vector["input"]["source_uri"] + vector["input"]["span"]

    assert unicodedata.is_normalized("NFC", joined(nfc))
    assert not unicodedata.is_normalized("NFC", joined(nfd))


def test_separator_vectors_exercise_the_python_rust_strip_difference():
    covered = set()
    for vector in VECTORS["content_identity"] + VECTORS["content_identity_errors"]:
        span = vector["input"]["span"]
        python_stripped = span.strip()
        rust_trimmed = span.strip(UNICODE_WHITE_SPACE)
        if python_stripped != rust_trimmed:
            covered.update(set(span) & set(SEPARATORS))
    assert covered == set(SEPARATORS)
    # The only characters on which the two strips disagree are U+001C-U+001F.
    python_space = {chr(c) for c in range(sys.maxunicode + 1) if chr(c).isspace()}
    assert python_space ^ set(UNICODE_WHITE_SPACE) == set(SEPARATORS)


def test_vectors_agree_with_folio_insights_golden_values():
    # Values computed by folio_insights.shards.minting.mint_shard_iri; see
    # tests/test_identity.py GOLDEN.
    assert _by_id("plain-ascii")["expected"]["provenance_hash"] == (
        "60fd4827bbe451edea90e38b6735314d5d95bf6e29c9918a980d8f3169a34438"
    )
    assert _by_id("uri-path-nfc")["expected"]["provenance_hash"] == (
        "9b76e0ee402e98b4a5ca4dfc6229913d0405dc045e186482140bf9b423dd8cb5"
    )


PROPOSITION_SCHEMA = load(generator.PROPOSITION_SCHEMA)
RECORD_SCHEMA = load(generator.RECORD_SCHEMA)
PROPOSITION_VALIDATOR = Draft202012Validator(
    PROPOSITION_SCHEMA, format_checker=Draft202012Validator.FORMAT_CHECKER
)
RECORD_VALIDATOR = Draft202012Validator(
    RECORD_SCHEMA, format_checker=Draft202012Validator.FORMAT_CHECKER
)


def test_schemas_are_valid_draft_2020_12_and_stamped():
    for schema in (PROPOSITION_SCHEMA, RECORD_SCHEMA):
        Draft202012Validator.check_schema(schema)
        assert schema["x-folio-schema-version"] == 4
        assert schema["x-folio-invariants"]


def test_schema_properties_match_model_fields():
    assert set(PROPOSITION_SCHEMA["properties"]) == set(Proposition.model_fields)
    assert set(RECORD_SCHEMA["properties"]) == set(
        PropositionDocumentRecord.model_fields
    )
    assert set(PROPOSITION_SCHEMA["required"]) == {
        name for name, field in Proposition.model_fields.items() if field.is_required()
    }


def test_schema_enums_match_python_enums():
    defs = PROPOSITION_SCHEMA["$defs"]
    assert defs["AxiomAction"]["enum"] == [member.value for member in AxiomAction]
    assert defs["AxiomStatus"]["enum"] == [member.value for member in AxiomStatus]
    assert {"reject", "override"} <= set(defs["AxiomAction"]["enum"])
    assert defs["ActorRole"]["enum"] == [member.value for member in ActorRole]
    assert {"legislature", "agency"} <= set(defs["ActorRole"]["enum"])


def _sample(**overrides) -> dict:
    iri = content_iri("https://example.com/doc", "span")
    sig = {"algorithm": "ed25519", "key_id": "did:key:z6MkA#z6MkA", "value": "AA"}

    def entry(sequence, from_status, to_status, action, minute, reason="checked"):
        return {
            "sequence": sequence,
            "from_status": from_status,
            "to_status": to_status,
            "action": action,
            "actor_did": "did:key:z6MkA",
            "at": datetime(2026, 10, 30, 12, minute, tzinfo=UTC),
            "reason": reason,
            "signature": sig,
        }

    values = {
        "id": "p-1",
        "start_char": 0,
        "end_char": 4,
        "text": "span",
        "proposition_type": "Legal Proposition",
        "asserter": {"role": "party"},
        "validator": None,
        "disposition": "unresolved",
        "content_iri": iri,
        "axiom_status": "promoted",
        "axiom_history": [
            entry(0, "proposition", "demoted", "reject", 0),
            entry(1, "demoted", "promoted", "override", 1),
            entry(2, "promoted", "demoted", "override", 2),
            entry(3, "demoted", "promoted", "promote", 3),
        ],
    }
    values.update(overrides)
    return values


def test_model_dumps_validate_against_the_schema():
    proposition = Proposition(**_sample())
    PROPOSITION_VALIDATOR.validate(proposition.model_dump(mode="json"))
    minimal = Proposition(
        id="p-2",
        proposition_type="stipulation",
        asserter=None,
        validator=None,
        disposition="accepted",
    )
    PROPOSITION_VALIDATOR.validate(minimal.model_dump(mode="json"))
    record = PropositionDocumentRecord(
        document_id="d-1",
        source_uri="https://example.com/doc",
        propositions=[proposition, minimal],
        generator={"tool": "test", "version": "1"},
    )
    RECORD_VALIDATOR.validate(record.model_dump(mode="json"))


@pytest.mark.parametrize(
    "overrides",
    [
        {"disposition": "maybe"},
        {"axiom_status": "rejected"},
        {"content_iri": "urn:folio:shard/NOT-HEX"},
        {"content_iri": "urn:folio:shard/" + "a" * 31},
        {"asserter": {"role": "senate"}},
        {"start_char": -1},
        {"id": None},
    ],
)
def test_shape_violations_are_rejected_by_both_model_and_schema(overrides):
    data = _sample(**overrides)
    with pytest.raises(ValidationError):
        Proposition(**data)
    as_json = json.loads(json.dumps(data, default=lambda value: value.isoformat()))
    assert not PROPOSITION_VALIDATOR.is_valid(as_json)


def test_unknown_axiom_action_is_rejected_by_both_model_and_schema():
    data = _sample()
    data["axiom_history"][0] = {**data["axiom_history"][0], "action": "veto"}
    with pytest.raises(ValidationError):
        Proposition(**data)
    as_json = json.loads(json.dumps(data, default=lambda value: value.isoformat()))
    assert not PROPOSITION_VALIDATOR.is_valid(as_json)
