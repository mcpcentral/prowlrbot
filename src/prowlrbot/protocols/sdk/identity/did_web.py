# -*- coding: utf-8 -*-
"""did:web method — persistent, DNS-bound identities.

A did:web DID is tied to a domain name, resolved via HTTPS.
The DID Document is hosted at a well-known URL derived from the DID.

Format: did:web:example.com:agents:planner
Resolves to: https://example.com/agents/planner/did.json

Ref: https://w3c-ccg.github.io/did-method-web/
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .did_document import DIDDocument

logger = logging.getLogger(__name__)


@dataclass
class DIDWebIdentity:
    """A persistent identity bound to a web domain.

    Attributes:
        did: The did:web string.
        domain: The hosting domain.
        path: The path within the domain.
        document_url: Where the DID Document is hosted.
    """

    did: str
    domain: str
    path: str
    document_url: str


class DIDWebMethod:
    """did:web method for persistent, DNS-bound identities.

    Usage::

        method = DIDWebMethod()

        # Create a DID for an agent hosted at example.com
        identity = method.create(
            domain="example.com",
            path="agents/planner",
        )
        print(identity.did)  # did:web:example.com:agents:planner
        print(identity.document_url)  # https://example.com/agents/planner/did.json
    """

    @staticmethod
    def create(
        domain: str,
        path: str = "",
        port: Optional[int] = None,
    ) -> DIDWebIdentity:
        """Create a did:web identity for an agent.

        Args:
            domain: The hosting domain (e.g. "example.com").
            path: Path within the domain (e.g. "agents/planner").
            port: Optional port (encoded as domain%3A8080).

        Returns:
            A DIDWebIdentity with the DID and document URL.
        """
        # Encode domain with port
        domain_part = domain
        if port:
            domain_part = f"{domain}%3A{port}"

        # Build DID
        if path:
            path_parts = path.strip("/").replace("/", ":")
            did = f"did:web:{domain_part}:{path_parts}"
            doc_url = f"https://{domain}:{port}" if port else f"https://{domain}"
            doc_url += f"/{path.strip('/')}/did.json"
        else:
            did = f"did:web:{domain_part}"
            doc_url = f"https://{domain}:{port}" if port else f"https://{domain}"
            doc_url += "/.well-known/did.json"

        return DIDWebIdentity(
            did=did,
            domain=domain,
            path=path,
            document_url=doc_url,
        )

    @staticmethod
    def did_to_url(did: str) -> str:
        """Convert a did:web to its resolution URL.

        Args:
            did: A did:web string.

        Returns:
            The HTTPS URL where the DID Document should be hosted.
        """
        if not did.startswith("did:web:"):
            raise ValueError(f"Not a did:web: {did}")

        parts = did[8:].split(":")  # Remove "did:web:" prefix
        domain = parts[0].replace("%3A", ":")

        if len(parts) == 1:
            return f"https://{domain}/.well-known/did.json"
        else:
            path = "/".join(parts[1:])
            return f"https://{domain}/{path}/did.json"

    @staticmethod
    def generate_document(
        identity: DIDWebIdentity,
        public_key: str = "",
        endpoints: Optional[Dict[str, str]] = None,
    ) -> DIDDocument:
        """Generate a DID Document for hosting at the document URL.

        Args:
            identity: The DIDWebIdentity to generate a document for.
            public_key: Base64url-encoded Ed25519 public key.
            endpoints: Transport → URL mapping.

        Returns:
            A DIDDocument ready to serialize as did.json.
        """
        return DIDDocument.for_agent(
            did=identity.did,
            public_key=public_key,
            endpoints=endpoints,
        )
