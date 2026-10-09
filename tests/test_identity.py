import hashlib
import unicodedata

import pytest

from folio_propositions import (
    CONTENT_IRI_PREFIX,
    ContentIdentity,
    content_identity,
    content_iri,
    document_source_uri,
    normalize_source_uri,
    normalize_span,
)

# Golden vectors computed with the frozen folio-insights recipe
# (folio_insights.shards.minting.mint_shard_iri). Never regenerate these from
# this library: a mismatch means the shared contract broke.
GOLDEN = [
    pytest.param(
        "https://example.com/opinions/palsgraf",
        "The risk reasonably to be perceived defines the duty to be obeyed.",
        "60fd4827bbe451edea90e38b6735314d5d95bf6e29c9918a980d8f3169a34438",
        id="plain-ascii",
    ),
    pytest.param(
        "HTTPS://Example.COM/a/",
        "x\ny",
        "14fb4355508f618ede208ef919c1499f8b1b7d869665f14c1f8a2244deaddcff",
        id="scheme-host-case-trailing-slash",
    ),
    pytest.param(
        "https://example.com/café",
        "span",
        "9b76e0ee402e98b4a5ca4dfc6229913d0405dc045e186482140bf9b423dd8cb5",
        id="nfc-path",
    ),
    pytest.param(
        "https://example.com/café",
        "span",
        "9b76e0ee402e98b4a5ca4dfc6229913d0405dc045e186482140bf9b423dd8cb5",
        id="nfd-path",
    ),
    pytest.param(
        "https://example.com/doc",
        "line one\r\nline two",
        "293c36cd655b6e86ca388f953c3190cf44e65fc9eb1b763b60f0cd67780e5e0f",
        id="crlf-span",
    ),
    pytest.param(
        "https://example.com/doc",
        "  padded span \n",
        "a3bb531c78c793373fc2e3256318da582cfcd0e48838cfee8354deff0088a5b9",
        id="surrounding-whitespace",
    ),
    pytest.param(
        "https://example.com/doc?page=2#para-7",
        "span",
        "f20f78877bb6b6f203ae5ad5bf5bd3fce99ecc4008183f88495575a5169c15f3",
        id="query-and-fragment",
    ),
    pytest.param(
        "urn:sha256:abc123",
        "span",
        "83023af2a4c18f82ce310676bf7373e1b0ef71c63e63b33ffde1ad33394f3a05",
        id="urn-uri",
    ),
]


@pytest.mark.parametrize(("source_uri", "span", "provenance_hash"), GOLDEN)
def test_golden_vectors_match_folio_insights_recipe(source_uri, span, provenance_hash):
    identity = content_identity(source_uri, span)
    assert identity == ContentIdentity(
        iri=CONTENT_IRI_PREFIX + provenance_hash[:32],
        provenance_hash=provenance_hash,
    )
    assert content_iri(source_uri, span) == identity.iri


def test_ae1_host_case_trailing_slash_crlf_and_whitespace_are_equivalent():
    assert content_iri("https://Example.com/a/", "x\r\ny ") == content_iri(
        "https://example.com/a", "x\ny"
    )


def test_query_and_fragment_are_preserved_and_distinguish_identities():
    assert normalize_source_uri("https://example.com/doc?page=2#para-7") == (
        "https://example.com/doc?page=2#para-7"
    )
    assert content_iri("https://example.com/doc?page=2", "span") != content_iri(
        "https://example.com/doc?page=3", "span"
    )
    assert content_iri("https://example.com/doc#a", "span") != content_iri(
        "https://example.com/doc#b", "span"
    )


def test_root_path_slash_is_kept_and_non_ascii_path_is_percent_encoded():
    assert normalize_source_uri("https://example.com/") == "https://example.com/"
    assert normalize_source_uri("https://example.com/café/") == (
        "https://example.com/caf%C3%A9"
    )


@pytest.mark.parametrize(
    "text",
    [
        "café holding",
        "The Ångström rule",
        "naïve résumé — über",
        "ẛ̣ ligature",
    ],
)
def test_nfc_and_nfd_spans_share_an_identity(text):
    nfc = unicodedata.normalize("NFC", text)
    nfd = unicodedata.normalize("NFD", text)
    assert nfc != nfd
    assert content_iri("https://example.com/doc", nfc) == content_iri(
        "https://example.com/doc", nfd
    )


@pytest.mark.parametrize("segment", ["café", "Ångström", "résumé"])
def test_nfc_and_nfd_uri_paths_share_an_identity(segment):
    nfc_uri = "https://example.com/" + unicodedata.normalize("NFC", segment)
    nfd_uri = "https://example.com/" + unicodedata.normalize("NFD", segment)
    assert nfc_uri != nfd_uri
    assert normalize_source_uri(nfc_uri) == normalize_source_uri(nfd_uri)
    assert content_iri(nfc_uri, "span") == content_iri(nfd_uri, "span")


@pytest.mark.parametrize(
    "lines",
    [
        ["one", "two"],
        ["first paragraph", "", "second paragraph"],
        ["a", "b", "c", "d"],
    ],
)
@pytest.mark.parametrize("separator", ["\r\n", "\r"])
def test_crlf_and_cr_spans_equal_lf_spans(lines, separator):
    lf = "\n".join(lines)
    other = separator.join(lines)
    assert normalize_span(other) == normalize_span(lf)
    assert content_iri("https://example.com/doc", other) == content_iri(
        "https://example.com/doc", lf
    )


def test_identity_is_per_source_and_span():
    base = content_iri("https://example.com/doc", "span")
    assert base != content_iri("https://example.com/other", "span")
    assert base != content_iri("https://example.com/doc", "other span")


@pytest.mark.parametrize(
    ("source_uri", "span"),
    [
        ("", "span"),
        ("https://example.com/doc", ""),
        ("https://example.com/doc", " \r\n\t "),
    ],
)
def test_empty_source_or_span_is_rejected(source_uri, span):
    with pytest.raises(ValueError):
        content_identity(source_uri, span)


def test_document_source_uri_is_deterministic_over_canonical_text():
    text = "Opinion text\r\nsecond line  "
    expected = "urn:sha256:" + hashlib.sha256(b"Opinion text\nsecond line").hexdigest()
    assert document_source_uri(text) == expected
    assert document_source_uri("  Opinion text\nsecond line") == expected
    assert document_source_uri("Different text") != expected
    with pytest.raises(ValueError):
        document_source_uri("   ")
