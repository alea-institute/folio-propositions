"""Local conformance to portable, frozen shared-shard identity examples."""

import hashlib
import json
import re
from pathlib import Path

import pytest
from pydantic import ValidationError
from test_identity import GOLDEN

from folio_propositions import (
    Proposition,
    PropositionDocumentRecord,
    content_identity,
    content_iri,
    normalize_source_uri,
    normalize_span,
    stamp_content_iris,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "shared_shard_identity_v1.json"
CASE_FIELDS = (
    "id",
    "source_uri",
    "span",
    "normalized_source_uri",
    "normalized_span",
    "provenance_hash",
    "iri",
)


def load_cases(path=FIXTURE_PATH):
    corpus = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(corpus, dict), "fixture must be an object"
    version = corpus.get("fixture_version")
    assert type(version) is int and version == 1, "unsupported fixture_version"
    cases = corpus.get("cases")
    assert isinstance(cases, list) and cases, "cases must be a nonempty array"
    seen = set()
    for index, case in enumerate(cases):
        assert isinstance(case, dict), f"cases[{index}] must be an object"
        label = f"cases[{index}] ({case.get('id', 'missing id')})"
        for field in CASE_FIELDS:
            value = case.get(field)
            assert isinstance(value, str) and value, f"{label}: {field} must be a nonempty string"
        assert case["id"] not in seen, f"{label}: duplicate id"
        seen.add(case["id"])
        assert re.fullmatch(r"[0-9a-f]{64}", case["provenance_hash"]), (
            f"{label}: invalid provenance_hash"
        )
        assert re.fullmatch(r"urn:folio:shard/[0-9a-f]{32}", case["iri"]), (
            f"{label}: invalid iri"
        )
    return cases


CASES = load_cases()
BY_ID = {case["id"]: case for case in CASES}


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_literal_payload_and_public_identity_match_fixture(case):
    # Check literal expectations independently before exercising the public APIs.
    payload = (case["normalized_source_uri"] + "\n" + case["normalized_span"]).encode("utf-8")
    assert hashlib.sha256(payload).hexdigest() == case["provenance_hash"]
    assert case["iri"] == "urn:folio:shard/" + case["provenance_hash"][:32]

    assert normalize_source_uri(case["source_uri"]) == case["normalized_source_uri"]
    assert normalize_span(case["span"]) == case["normalized_span"]
    identity = content_identity(case["source_uri"], case["span"])
    assert identity.provenance_hash == case["provenance_hash"]
    assert identity.iri == case["iri"]
    assert content_iri(case["source_uri"], case["span"]) == case["iri"]


@pytest.mark.parametrize("anchor", [pytest.param(anchor, id=anchor.id) for anchor in GOLDEN])
def test_original_golden_anchors_are_preserved(anchor):
    case = BY_ID[anchor.id]
    assert (case["source_uri"], case["span"], case["provenance_hash"]) == anchor.values


@pytest.mark.parametrize(
    "case_ids",
    [
        ("scheme-host-case-trailing-slash", "canonical-a"),
        ("nfc-path", "nfd-path", "encoded-path"),
        ("nfc-span", "nfd-span"),
        ("crlf-span", "lf-span", "bare-cr-span"),
        ("surrounding-whitespace", "unpadded-span"),
    ],
    ids=["source-normalization", "path-nfc", "span-nfc", "newlines", "padding"],
)
def test_equivalent_fixture_inputs_share_identity(case_ids):
    assert len({BY_ID[case_id]["provenance_hash"] for case_id in case_ids}) == 1
    assert len({BY_ID[case_id]["iri"] for case_id in case_ids}) == 1


@pytest.mark.parametrize(
    "case_ids",
    [
        ("base-doc", "changed-source", "changed-span"),
        ("query-and-fragment", "changed-query", "changed-fragment"),
        ("root-slash", "no-root-slash"),
        ("base-doc", "path-case"),
        ("single-space", "double-space", "interior-tab"),
        ("encoded-path", "encoded-path-lowercase"),
        ("encoded-path-slash", "literal-path-slash"),
    ],
    ids=["source-span", "query-fragment", "root", "path-case", "spacing", "hex-case", "escape"],
)
def test_distinct_fixture_inputs_keep_distinct_identities(case_ids):
    assert len({BY_ID[case_id]["provenance_hash"] for case_id in case_ids}) == len(case_ids)
    assert len({BY_ID[case_id]["iri"] for case_id in case_ids}) == len(case_ids)


@pytest.mark.parametrize("identity_function", [content_identity, content_iri])
@pytest.mark.parametrize(
    ("source_uri", "span", "message"),
    [
        ("", "span", "source_uri"),
        ("https://example.com/doc", "", "span"),
        ("https://example.com/doc", " \t\r\n ", "span"),
    ],
    ids=["empty-source", "empty-span", "blank-span"],
)
def test_local_identity_api_rejects_empty_inputs(identity_function, source_uri, span, message):
    with pytest.raises(ValueError, match=message):
        identity_function(source_uri, span)


@pytest.mark.parametrize("version", [None, True, 2, "1"])
def test_loader_rejects_unsupported_version(tmp_path, version):
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps({"fixture_version": version, "cases": CASES}), encoding="utf-8")
    with pytest.raises(AssertionError, match="fixture_version"):
        load_cases(path)


@pytest.mark.parametrize(
    ("cases", "message"),
    [
        ([], "nonempty array"),
        ({}, "nonempty array"),
        ([None], r"cases\[0\] must be an object"),
        ([CASES[0], CASES[0]], "plain-ascii.*duplicate id"),
        ([{**CASES[0], "span": None}], "plain-ascii.*span"),
        ([{**CASES[0], "normalized_span": ""}], "plain-ascii.*normalized_span"),
        ([{**CASES[0], "provenance_hash": "bad"}], "plain-ascii.*provenance_hash"),
        ([{**CASES[0], "iri": "bad"}], "plain-ascii.*iri"),
    ],
    ids=["empty", "wrong-type", "non-object", "duplicate", "null", "blank", "hash", "iri"],
)
def test_loader_identifies_malformed_cases(tmp_path, cases, message):
    path = tmp_path / "fixture.json"
    path.write_text(json.dumps({"fixture_version": 1, "cases": cases}), encoding="utf-8")
    with pytest.raises(AssertionError, match=message):
        load_cases(path)


def spanned(proposition_id, text, **overrides):
    values = {
        "id": proposition_id,
        "start_char": 0 if text is not None else None,
        "end_char": len(text) if text is not None else None,
        "text": text,
        "proposition_type": "Legal Proposition",
        "asserter": {"role": "party"},
        "validator": None,
        "disposition": "unresolved",
    }
    values.update(overrides)
    return Proposition(**values)


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["id"])
def test_distinct_propositions_join_fixture_shard_after_json_round_trip(case):
    record = PropositionDocumentRecord(
        document_id="extraction-1",
        source_uri=case["source_uri"],
        propositions=[
            spanned("legal-1", case["span"], asserter={"role": "appellant"}),
            spanned(
                "fact-2",
                case["span"],
                proposition_type="Factual Statement",
                asserter={"role": "secondary_source", "name": "Example source"},
                start_char=100,
                end_char=100 + len(case["span"]),
            ),
        ],
        document_metadata={"title": "Example document", "extraction": 1},
        generator={"tool": "example-consumer", "version": "1.0"},
    )
    before = record.model_dump()

    stamped = stamp_content_iris(record)

    assert record.model_dump() == before
    assert stamped is not record
    assert all(new is not old for new, old in zip(stamped.propositions, record.propositions))
    expected = record.model_dump()
    for proposition in expected["propositions"]:
        proposition["content_iri"] = case["iri"]
    # Only the stamps change; raw text, offsets, IDs and metadata survive.
    assert stamped.model_dump() == expected
    assert stamp_content_iris(stamped) == stamped
    restored = PropositionDocumentRecord.model_validate_json(stamped.model_dump_json())
    assert restored == stamped
    assert [proposition.content_iri for proposition in restored.propositions] == [
        case["iri"], case["iri"]
    ]


def test_extraction_and_document_metadata_do_not_change_fixture_join_key():
    case = BY_ID["plain-ascii"]
    for extraction, offset in [(1, 0), (2, 500)]:
        record = PropositionDocumentRecord(
            document_id=f"document-{extraction}",
            source_uri=case["source_uri"],
            propositions=[spanned(
                f"proposition-{extraction}",
                case["span"],
                start_char=offset,
                end_char=offset + len(case["span"]),
            )],
            document_metadata={"title": f"Title {extraction}"},
            generator={"tool": f"extractor-{extraction}", "version": str(extraction)},
        )
        before = record.model_dump()
        stamped = stamp_content_iris(record)
        assert record.model_dump() == before
        before["propositions"][0]["content_iri"] = case["iri"]
        assert stamped.model_dump() == before


def test_changed_source_or_span_produces_distinct_fixture_join_keys():
    join_keys = []
    for case_id in ("base-doc", "changed-source", "changed-span"):
        case = BY_ID[case_id]
        record = PropositionDocumentRecord(
            document_id="same-document-id",
            source_uri=case["source_uri"],
            propositions=[spanned("same-proposition-id", case["span"])],
        )
        stamped = stamp_content_iris(record)
        assert stamped.propositions[0].content_iri == case["iri"]
        join_keys.append(stamped.propositions[0].content_iri)
    assert len(set(join_keys)) == 3


def test_missing_and_normalized_empty_text_remain_unstamped():
    case = BY_ID["base-doc"]
    record = PropositionDocumentRecord(
        document_id="mixed-spans",
        source_uri=case["source_uri"],
        propositions=[
            spanned("missing", None),
            spanned("empty", ""),
            spanned("blank", " \t\r\n "),
            spanned("present", case["span"]),
        ],
    )
    stamped = stamp_content_iris(record)
    assert [proposition.content_iri for proposition in stamped.propositions] == [
        None, None, None, case["iri"]
    ]
    assert all(proposition.content_iri is None for proposition in record.propositions)
    assert PropositionDocumentRecord.model_validate_json(stamped.model_dump_json()) == stamped


@pytest.mark.parametrize("stamp", [None, BY_ID["changed-source"]["iri"]])
def test_missing_source_accepts_unverified_stamp_but_prevents_stamping(stamp):
    record = PropositionDocumentRecord(
        document_id="unknown-source",
        propositions=[spanned("p-1", BY_ID["base-doc"]["span"], content_iri=stamp)],
    )
    restored = PropositionDocumentRecord.model_validate_json(record.model_dump_json())
    assert restored.propositions[0].content_iri == stamp
    with pytest.raises(ValueError, match="requires record.source_uri"):
        stamp_content_iris(restored)


def test_record_rejects_validly_shaped_stamp_from_different_source():
    case = BY_ID["base-doc"]
    wrong_stamp = BY_ID["changed-source"]["iri"]
    with pytest.raises(ValidationError, match="p-wrong content_iri does not match"):
        PropositionDocumentRecord(
            document_id="mismatched-stamp",
            source_uri=case["source_uri"],
            propositions=[spanned("p-wrong", case["span"], content_iri=wrong_stamp)],
        )
