# -*- coding: utf-8 -*-
"""ROAR Protocol SDK — Cryptographic primitives for identity and signing.

Provides Ed25519 keypair management and message signing/verification.
Falls back to HMAC-SHA256 when Ed25519 is unavailable (PyNaCl not installed).

Usage::

    from prowlrbot.protocols.sdk.crypto import KeyPair, Ed25519Signer

    kp = KeyPair.generate()
    signer = Ed25519Signer(kp)
    signature = signer.sign(message_bytes)
    assert signer.verify(message_bytes, signature)
"""
from .ed25519 import KeyPair, Ed25519Signer, NACL_AVAILABLE

__all__ = [
    "KeyPair",
    "Ed25519Signer",
    "NACL_AVAILABLE",
]
