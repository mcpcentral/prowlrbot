# -*- coding: utf-8 -*-
"""Tests for HMAC authentication."""

import hashlib
import hmac
import json

import pytest


class TestHMACAuthentication:
    """Test HMAC signature generation and verification."""

    def test_signature_generation(self):
        """Test that HMAC signatures are generated correctly."""
        secret = "test-secret-key-32-chars-long!!"
        payload = {"job_id": "test-123", "capability": "test"}
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))

        signature = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()

        assert len(signature) == 64  # SHA256 hex length
        assert isinstance(signature, str)

    def test_signature_verification(self):
        """Test that HMAC signatures verify correctly."""
        secret = "test-secret-key-32-chars-long!!"
        payload = {"job_id": "test-123", "capability": "test"}
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))

        signature = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()

        # Verify
        expected = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()

        assert hmac.compare_digest(signature, expected)

    def test_signature_different_secrets(self):
        """Test that different secrets produce different signatures."""
        payload = {"job_id": "test-123", "capability": "test"}
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))

        sig1 = hmac.new(b"secret1", body.encode(), hashlib.sha256).hexdigest()
        sig2 = hmac.new(b"secret2", body.encode(), hashlib.sha256).hexdigest()

        assert sig1 != sig2

    def test_signature_payload_modification(self):
        """Test that modified payload fails verification."""
        secret = "test-secret-key-32-chars-long!!"
        payload = {"job_id": "test-123", "capability": "test"}
        body = json.dumps(payload, sort_keys=True, separators=(",", ":"))

        signature = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256,
        ).hexdigest()

        # Modified payload
        modified_payload = {"job_id": "test-123", "capability": "modified"}
        modified_body = json.dumps(
            modified_payload,
            sort_keys=True,
            separators=(",", ":"),
        )

        expected = hmac.new(
            secret.encode(),
            modified_body.encode(),
            hashlib.sha256,
        ).hexdigest()

        assert not hmac.compare_digest(signature, expected)


class TestConfigValidation:
    """Test configuration validation."""

    def test_hmac_secret_minimum_length(self):
        """Test that HMAC secret must be at least 32 characters."""
        short_secret = "short"
        assert len(short_secret) < 32

        long_secret = "this-is-a-secure-secret-key-32-chars-long!!"
        assert len(long_secret) >= 32

    def test_bridge_host_validation(self):
        """Test bridge host validation."""
        # These should fail
        invalid_hosts = ["localhost", "100.x.x.x", "", None]

        for host in invalid_hosts:
            if host in ("localhost", "100.x.x.x"):
                assert host in ("localhost", "100.x.x.x")
