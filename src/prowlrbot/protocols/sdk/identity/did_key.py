# -*- coding: utf-8 -*-
"""did:key method — ephemeral, cryptographic identities.

A did:key is derived entirely from a public key, requiring no external
registry. Ideal for ephemeral agents that need verifiable identity for
a single session or short-lived task.

Format: did:key:z<base58-multicodec-ed25519-pubkey>

Ref: https://w3c-ccg.github.io/did-method-key/
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..crypto import KeyPair, NACL_AVAILABLE
from .did_document import DIDDocument


@dataclass
class DIDKeyIdentity:
    """An identity derived from an Ed25519 keypair.

    Attributes:
        did: The did:key string.
        keypair: The underlying Ed25519 keypair.
    """

    did: str
    keypair: KeyPair


class DIDKeyMethod:
    """did:key method for ephemeral, self-certifying identities.

    Usage::

        method = DIDKeyMethod()
        identity = method.generate()
        print(identity.did)  # did:key:z6Mk...

        doc = method.resolve(identity.did)
    """

    @staticmethod
    def generate() -> DIDKeyIdentity:
        """Generate a new did:key identity.

        Returns:
            A DIDKeyIdentity with keypair and DID.

        Raises:
            RuntimeError: If PyNaCl is not installed.
        """
        kp = KeyPair.generate()
        return DIDKeyIdentity(did=kp.did_key, keypair=kp)

    @staticmethod
    def resolve(did: str, public_key: str = "") -> DIDDocument:
        """Resolve a did:key to a DID Document.

        Since did:key is self-describing, resolution just unpacks
        the public key from the DID itself.

        Args:
            did: The did:key string.
            public_key: Optional pre-extracted public key.

        Returns:
            A DIDDocument with the embedded public key.
        """
        return DIDDocument.for_agent(
            did=did,
            public_key=public_key,
        )
