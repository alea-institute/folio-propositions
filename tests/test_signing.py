import base64

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from folio_propositions import (
    DidKeyEd25519Verifier,
    TransitionSignature,
    did_key_from_public_bytes,
)
from folio_propositions.signing import base58btc_encode, public_bytes_from_did_key


@pytest.mark.parametrize("length", [31, 33])
def test_raw_public_key_requires_exactly_32_bytes(length):
    with pytest.raises(ValueError, match="Ed25519 public keys are 32 bytes"):
        did_key_from_public_bytes(bytes(length))


def test_raw_public_key_round_trip():
    raw = bytes(range(32))
    assert public_bytes_from_did_key(did_key_from_public_bytes(raw)) == raw


@pytest.mark.parametrize(
    "decoded",
    [b"\xec\x01" + bytes(32), b"\xed\x01" + bytes(31), b"\xed\x01" + bytes(33)],
    ids=["wrong-codec", "short-key", "long-key"],
)
def test_valid_base58_with_wrong_codec_or_key_length_is_rejected(decoded):
    did = "did:key:z" + base58btc_encode(decoded)
    with pytest.raises(ValueError, match="does not encode an Ed25519 public key"):
        public_bytes_from_did_key(did)


@pytest.mark.parametrize(
    "value",
    [
        "A" * 129,
        "a",
        "\u00e9",
        base64.urlsafe_b64encode(bytes(63)).decode("ascii"),
        base64.urlsafe_b64encode(bytes(65)).decode("ascii"),
    ],
    ids=["overlong", "malformed", "non-ascii", "short-decoded", "long-decoded"],
)
def test_invalid_signature_encodings_return_false(value):
    key = Ed25519PrivateKey.generate()
    did = did_key_from_public_bytes(key.public_key().public_bytes_raw())
    payload = b"synthetic signing boundary test"
    signature = TransitionSignature(
        algorithm="ed25519",
        key_id=f"{did}#key",
        value=base64.urlsafe_b64encode(key.sign(payload)).rstrip(b"=").decode("ascii"),
    )
    verifier = DidKeyEd25519Verifier()
    assert verifier.verify(payload, signature, did) is True
    invalid = signature.model_copy(update={"value": value})
    assert verifier.verify(payload, invalid, did) is False
