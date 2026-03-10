# -*- coding: utf-8 -*-
"""Tests for ROAR Protocol Phase 4 — Identity Enhancement."""
from __future__ import annotations

import time
import unittest

from src.prowlrbot.protocols.sdk.crypto import NACL_AVAILABLE
from src.prowlrbot.protocols.sdk.identity.delegation import (
    AutonomyLevel,
    CapabilityDelegation,
    DelegationToken,
)
from src.prowlrbot.protocols.sdk.identity.did_document import (
    DIDDocument,
    ServiceEndpoint,
    VerificationMethod,
)
from src.prowlrbot.protocols.sdk.identity.did_web import DIDWebIdentity, DIDWebMethod


class TestDIDDocument(unittest.TestCase):
    """Tests for W3C DID Document generation."""

    def test_basic_document(self):
        doc = DIDDocument(id="did:roar:agent:test-12345678")
        assert doc.id == "did:roar:agent:test-12345678"
        assert doc.controller == doc.id
        assert doc.created > 0

    def test_for_agent_with_key(self):
        doc = DIDDocument.for_agent(
            did="did:roar:agent:planner-abcdef00",
            display_name="planner",
            public_key="fake-base64-public-key",
            endpoints={"http": "http://localhost:8089"},
        )
        assert len(doc.verification_methods) == 1
        assert doc.verification_methods[0].type == "Ed25519VerificationKey2020"
        assert doc.verification_methods[0].public_key_base64 == "fake-base64-public-key"
        assert len(doc.authentication) == 1
        assert len(doc.services) == 1
        assert doc.services[0].service_endpoint == "http://localhost:8089"

    def test_for_agent_without_key(self):
        doc = DIDDocument.for_agent(did="did:roar:agent:simple-11111111")
        assert len(doc.verification_methods) == 0
        assert len(doc.authentication) == 0

    def test_to_dict_json_ld(self):
        doc = DIDDocument.for_agent(
            did="did:roar:agent:test-12345678",
            public_key="test-key",
            endpoints={"http": "http://example.com/roar"},
        )
        d = doc.to_dict()
        assert d["@context"][0] == "https://www.w3.org/ns/did/v1"
        assert d["id"] == "did:roar:agent:test-12345678"
        assert "verificationMethod" in d
        assert "service" in d
        assert d["service"][0]["type"] == "ROARMessaging"

    def test_multiple_endpoints(self):
        doc = DIDDocument.for_agent(
            did="did:roar:agent:multi-12345678",
            endpoints={
                "http": "http://localhost:8089",
                "websocket": "ws://localhost:8089/roar/ws",
            },
        )
        assert len(doc.services) == 2


class TestDIDWebMethod(unittest.TestCase):
    """Tests for did:web DID method."""

    def test_create_simple(self):
        identity = DIDWebMethod.create(domain="example.com", path="agents/planner")
        assert identity.did == "did:web:example.com:agents:planner"
        assert identity.document_url == "https://example.com/agents/planner/did.json"
        assert identity.domain == "example.com"

    def test_create_root(self):
        identity = DIDWebMethod.create(domain="example.com")
        assert identity.did == "did:web:example.com"
        assert identity.document_url == "https://example.com/.well-known/did.json"

    def test_create_with_port(self):
        identity = DIDWebMethod.create(domain="localhost", port=8089)
        assert "localhost%3A8089" in identity.did

    def test_did_to_url(self):
        url = DIDWebMethod.did_to_url("did:web:example.com:agents:planner")
        assert url == "https://example.com/agents/planner/did.json"

    def test_did_to_url_root(self):
        url = DIDWebMethod.did_to_url("did:web:example.com")
        assert url == "https://example.com/.well-known/did.json"

    def test_did_to_url_invalid(self):
        with self.assertRaises(ValueError):
            DIDWebMethod.did_to_url("did:roar:agent:test")

    def test_generate_document(self):
        identity = DIDWebMethod.create(domain="example.com", path="agents/test")
        doc = DIDWebMethod.generate_document(
            identity,
            public_key="test-pubkey",
            endpoints={"http": "https://example.com/agents/test/roar"},
        )
        assert doc.id == identity.did
        assert len(doc.verification_methods) == 1
        assert len(doc.services) == 1


class TestAutonomyLevel(unittest.TestCase):
    """Tests for graduated autonomy levels."""

    def test_watch_cannot_act(self):
        assert not AutonomyLevel.WATCH.can_act()
        assert AutonomyLevel.WATCH.requires_approval()

    def test_guide_cannot_act(self):
        assert not AutonomyLevel.GUIDE.can_act()
        assert AutonomyLevel.GUIDE.requires_approval()

    def test_delegate_can_act(self):
        assert AutonomyLevel.DELEGATE.can_act()
        assert not AutonomyLevel.DELEGATE.requires_approval()

    def test_autonomous_can_act(self):
        assert AutonomyLevel.AUTONOMOUS.can_act()
        assert not AutonomyLevel.AUTONOMOUS.requires_approval()


class TestDelegationToken(unittest.TestCase):
    """Tests for delegation tokens."""

    def test_token_creation(self):
        token = DelegationToken(
            grantor="did:roar:human:admin-12345678",
            grantee="did:roar:agent:worker-abcdef00",
            capabilities=["code-review"],
            autonomy_level=AutonomyLevel.DELEGATE,
        )
        assert token.id.startswith("dt-")
        assert token.valid
        assert not token.expired
        assert not token.revoked

    def test_token_allows(self):
        token = DelegationToken(
            capabilities=["code-review", "testing"],
        )
        assert token.allows("code-review")
        assert token.allows("testing")
        assert not token.allows("deploy")

    def test_wildcard_allows_all(self):
        token = DelegationToken(capabilities=["*"])
        assert token.allows("anything")
        assert token.allows("code-review")

    def test_expired_token_not_valid(self):
        token = DelegationToken(
            capabilities=["code-review"],
            expires_at=time.time() - 10,  # Already expired
        )
        assert token.expired
        assert not token.valid
        assert not token.allows("code-review")

    def test_revoked_token_not_valid(self):
        token = DelegationToken(
            capabilities=["code-review"],
            revoked=True,
        )
        assert not token.valid
        assert not token.allows("code-review")


class TestCapabilityDelegation(unittest.TestCase):
    """Tests for the delegation management system."""

    def setUp(self):
        self.delegation = CapabilityDelegation()
        self.admin_did = "did:roar:human:admin-12345678"
        self.agent_did = "did:roar:agent:worker-abcdef00"

    def test_grant_and_authorize(self):
        self.delegation.grant(
            grantor=self.admin_did,
            grantee=self.agent_did,
            capabilities=["code-review"],
            autonomy_level=AutonomyLevel.DELEGATE,
        )
        assert self.delegation.is_authorized(self.agent_did, "code-review")
        assert not self.delegation.is_authorized(self.agent_did, "deploy")

    def test_revoke(self):
        token = self.delegation.grant(
            grantor=self.admin_did,
            grantee=self.agent_did,
            capabilities=["code-review"],
        )
        assert self.delegation.revoke(token.id)
        assert not self.delegation.is_authorized(self.agent_did, "code-review")

    def test_ttl_expiration(self):
        self.delegation.grant(
            grantor=self.admin_did,
            grantee=self.agent_did,
            capabilities=["code-review"],
            autonomy_level=AutonomyLevel.DELEGATE,
            ttl_seconds=0.05,
        )
        assert self.delegation.is_authorized(self.agent_did, "code-review")
        time.sleep(0.1)
        assert not self.delegation.is_authorized(self.agent_did, "code-review")

    def test_autonomy_level_check(self):
        self.delegation.grant(
            grantor=self.admin_did,
            grantee=self.agent_did,
            capabilities=["code-review"],
            autonomy_level=AutonomyLevel.GUIDE,
        )
        # GUIDE < DELEGATE, so not authorized for DELEGATE-level actions
        assert not self.delegation.is_authorized(
            self.agent_did, "code-review", min_autonomy=AutonomyLevel.DELEGATE
        )
        # But authorized at GUIDE level
        assert self.delegation.is_authorized(
            self.agent_did, "code-review", min_autonomy=AutonomyLevel.GUIDE
        )

    def test_get_autonomy_level(self):
        self.delegation.grant(
            grantor=self.admin_did,
            grantee=self.agent_did,
            capabilities=["code-review"],
            autonomy_level=AutonomyLevel.DELEGATE,
        )
        assert self.delegation.get_autonomy_level(self.agent_did) == AutonomyLevel.DELEGATE

    def test_get_autonomy_level_no_tokens(self):
        assert self.delegation.get_autonomy_level(self.agent_did) == AutonomyLevel.WATCH

    def test_multiple_tokens_highest_wins(self):
        self.delegation.grant(
            grantor=self.admin_did,
            grantee=self.agent_did,
            capabilities=["code-review"],
            autonomy_level=AutonomyLevel.GUIDE,
        )
        self.delegation.grant(
            grantor=self.admin_did,
            grantee=self.agent_did,
            capabilities=["deploy"],
            autonomy_level=AutonomyLevel.AUTONOMOUS,
        )
        assert self.delegation.get_autonomy_level(self.agent_did) == AutonomyLevel.AUTONOMOUS

    def test_list_tokens(self):
        self.delegation.grant(
            grantor=self.admin_did,
            grantee=self.agent_did,
            capabilities=["code-review"],
        )
        self.delegation.grant(
            grantor=self.admin_did,
            grantee=self.agent_did,
            capabilities=["testing"],
        )
        tokens = self.delegation.list_tokens(grantee=self.agent_did)
        assert len(tokens) == 2

    def test_cleanup_expired(self):
        self.delegation.grant(
            grantor=self.admin_did,
            grantee=self.agent_did,
            capabilities=["code-review"],
            ttl_seconds=0.05,
        )
        time.sleep(0.1)
        removed = self.delegation.cleanup_expired()
        assert removed == 1
        assert len(self.delegation.list_tokens()) == 0


@unittest.skipUnless(NACL_AVAILABLE, "PyNaCl not installed")
class TestEd25519Signing(unittest.TestCase):
    """Tests for Ed25519 cryptographic signing (requires PyNaCl)."""

    def test_keypair_generation(self):
        from src.prowlrbot.protocols.sdk.crypto import KeyPair

        kp = KeyPair.generate()
        assert kp.private_key
        assert kp.public_key
        assert kp.did_key.startswith("did:key:z")

    def test_sign_and_verify(self):
        from src.prowlrbot.protocols.sdk.crypto import Ed25519Signer, KeyPair

        kp = KeyPair.generate()
        signer = Ed25519Signer(kp)
        sig = signer.sign(b"hello world")
        assert signer.verify(b"hello world", sig)

    def test_verify_fails_for_wrong_message(self):
        from src.prowlrbot.protocols.sdk.crypto import Ed25519Signer, KeyPair

        kp = KeyPair.generate()
        signer = Ed25519Signer(kp)
        sig = signer.sign(b"hello")
        assert not signer.verify(b"wrong", sig)


class TestEd25519Unavailable(unittest.TestCase):
    """Tests for graceful fallback when PyNaCl is not installed."""

    @unittest.skipIf(NACL_AVAILABLE, "PyNaCl is installed")
    def test_generate_raises(self):
        from src.prowlrbot.protocols.sdk.crypto import KeyPair

        with self.assertRaises(RuntimeError) as ctx:
            KeyPair.generate()
        assert "PyNaCl" in str(ctx.exception)


if __name__ == "__main__":
    unittest.main()
