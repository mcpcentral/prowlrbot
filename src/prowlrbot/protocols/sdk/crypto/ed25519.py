# -*- coding: utf-8 -*-
"""Ed25519 keypair generation and message signing.

Uses PyNaCl (libsodium bindings) when available. Provides a pure-Python
fallback that raises clear errors when Ed25519 is needed but PyNaCl
is not installed.

Ed25519 is used for cross-organization trust where HMAC shared secrets
are impractical. Each agent generates a keypair; the public key is
published in the agent's DID Document or AgentCard.

Ref: Bernstein, D.J. et al. (2012). "High-speed high-security signatures."
     NIST FIPS 186-5 approved Ed25519 as EdDSA.
"""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Detect PyNaCl availability
NACL_AVAILABLE = False
try:
    import nacl.signing
    import nacl.encoding
    import nacl.utils

    NACL_AVAILABLE = True
except ImportError:
    pass

# base58 encoding for did:key (optional, fallback to hex)
_BASE58_AVAILABLE = False
try:
    import base58

    _BASE58_AVAILABLE = True
except ImportError:
    pass


def _b58encode(data: bytes) -> str:
    """Base58 encode, with hex fallback if base58 not available."""
    if _BASE58_AVAILABLE:
        return base58.b58encode(data).decode()
    return data.hex()


@dataclass
class KeyPair:
    """An Ed25519 signing keypair.

    Attributes:
        private_key: 64-byte private key (base64url-encoded).
        public_key: 32-byte public key (base64url-encoded).
        did_key: The did:key representation of the public key.
    """

    private_key: str
    public_key: str
    did_key: str = ""

    @classmethod
    def generate(cls) -> "KeyPair":
        """Generate a new Ed25519 keypair.

        Returns:
            A KeyPair with base64url-encoded keys.

        Raises:
            RuntimeError: If PyNaCl is not installed.
        """
        if not NACL_AVAILABLE:
            raise RuntimeError(
                "Ed25519 requires PyNaCl. Install with: pip install pynacl"
            )

        signing_key = nacl.signing.SigningKey.generate()
        verify_key = signing_key.verify_key

        private_b64 = base64.urlsafe_b64encode(
            signing_key.encode()
        ).decode().rstrip("=")
        public_b64 = base64.urlsafe_b64encode(
            verify_key.encode()
        ).decode().rstrip("=")

        # did:key multicodec prefix for Ed25519: 0xed01
        multicodec = b"\xed\x01" + verify_key.encode()
        did_key = "did:key:z" + _b58encode(multicodec)

        return cls(
            private_key=private_b64,
            public_key=public_b64,
            did_key=did_key,
        )

    @classmethod
    def from_private_key(cls, private_key_b64: str) -> "KeyPair":
        """Reconstruct a keypair from a private key.

        Args:
            private_key_b64: Base64url-encoded private key.

        Returns:
            The full KeyPair derived from the private key.
        """
        if not NACL_AVAILABLE:
            raise RuntimeError(
                "Ed25519 requires PyNaCl. Install with: pip install pynacl"
            )

        # Pad base64url
        padded = private_key_b64 + "=" * (4 - len(private_key_b64) % 4)
        raw = base64.urlsafe_b64decode(padded)
        signing_key = nacl.signing.SigningKey(raw)
        verify_key = signing_key.verify_key

        public_b64 = base64.urlsafe_b64encode(
            verify_key.encode()
        ).decode().rstrip("=")

        multicodec = b"\xed\x01" + verify_key.encode()
        did_key = "did:key:z" + _b58encode(multicodec)

        return cls(
            private_key=private_key_b64,
            public_key=public_b64,
            did_key=did_key,
        )


class Ed25519Signer:
    """Signs and verifies messages using Ed25519.

    Usage::

        kp = KeyPair.generate()
        signer = Ed25519Signer(kp)

        sig = signer.sign(b"hello")
        assert signer.verify(b"hello", sig)

        # Verify with just public key
        assert Ed25519Signer.verify_with_public_key(
            b"hello", sig, kp.public_key
        )
    """

    def __init__(self, keypair: KeyPair) -> None:
        if not NACL_AVAILABLE:
            raise RuntimeError(
                "Ed25519 requires PyNaCl. Install with: pip install pynacl"
            )
        self._keypair = keypair
        padded = keypair.private_key + "=" * (4 - len(keypair.private_key) % 4)
        self._signing_key = nacl.signing.SigningKey(
            base64.urlsafe_b64decode(padded)
        )
        self._verify_key = self._signing_key.verify_key

    def sign(self, message: bytes) -> str:
        """Sign a message and return the signature as base64url.

        Args:
            message: The bytes to sign.

        Returns:
            Base64url-encoded signature string.
        """
        signed = self._signing_key.sign(message)
        sig_bytes = signed.signature
        return base64.urlsafe_b64encode(sig_bytes).decode().rstrip("=")

    def verify(self, message: bytes, signature: str) -> bool:
        """Verify a signature against a message.

        Args:
            message: The original message bytes.
            signature: Base64url-encoded signature.

        Returns:
            True if the signature is valid.
        """
        try:
            padded = signature + "=" * (4 - len(signature) % 4)
            sig_bytes = base64.urlsafe_b64decode(padded)
            self._verify_key.verify(message, sig_bytes)
            return True
        except Exception:
            return False

    def sign_message(self, msg_dict: dict) -> dict:
        """Sign a ROAR message dict and add ed25519 auth fields.

        Args:
            msg_dict: Message dict with at least {id, intent, payload}.

        Returns:
            Auth dict with signature, signer, algorithm, and public_key.
        """
        canonical = json.dumps(
            {
                "id": msg_dict.get("id", ""),
                "intent": msg_dict.get("intent", ""),
                "payload": msg_dict.get("payload", {}),
            },
            sort_keys=True,
        )
        sig = self.sign(canonical.encode())
        return {
            "signature": f"ed25519:{sig}",
            "signer": self._keypair.did_key or "unknown",
            "algorithm": "ed25519",
            "public_key": self._keypair.public_key,
        }

    @staticmethod
    def verify_with_public_key(
        message: bytes, signature: str, public_key_b64: str
    ) -> bool:
        """Verify a signature using only the public key.

        Useful for verifying messages from remote agents whose
        public key is published in their AgentCard or DID Document.

        Args:
            message: The original message bytes.
            signature: Base64url-encoded signature.
            public_key_b64: Base64url-encoded public key.

        Returns:
            True if valid.
        """
        if not NACL_AVAILABLE:
            return False
        try:
            padded_key = public_key_b64 + "=" * (4 - len(public_key_b64) % 4)
            padded_sig = signature + "=" * (4 - len(signature) % 4)
            verify_key = nacl.signing.VerifyKey(
                base64.urlsafe_b64decode(padded_key)
            )
            verify_key.verify(message, base64.urlsafe_b64decode(padded_sig))
            return True
        except Exception:
            return False
