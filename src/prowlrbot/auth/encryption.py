# -*- coding: utf-8 -*-
"""AES-256-equivalent encryption at rest using only Python stdlib.

Implements a Fernet-like authenticated encryption scheme built on
HMAC-SHA256 as a PRF (pseudo-random function) in counter mode, with
an HMAC-SHA256 authentication tag for integrity.

Cipher construction:
    encrypt(plaintext):
        1. Generate a 16-byte random IV.
        2. PKCS#7-pad the plaintext to a 16-byte block boundary.
        3. For each 16-byte block *i*, compute a keystream block:
           K_i = HMAC-SHA256(master_key, IV || i.to_bytes(4, 'big'))
           and XOR the plaintext block with the first 16 bytes of K_i.
        4. Compute an auth tag:
           tag = HMAC-SHA256(master_key, IV || ciphertext)
        5. Return base64(IV + ciphertext + tag).

    decrypt(token):
        1. base64-decode and split IV (16), ciphertext (variable), tag (32).
        2. Verify tag with hmac.compare_digest (constant-time).
        3. Decrypt by regenerating the same keystream blocks and XORing.
        4. Remove PKCS#7 padding.

Key derivation:
    PBKDF2-HMAC-SHA256, 100 000 iterations, 32-byte output.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import struct
from pathlib import Path

logger = logging.getLogger(__name__)

_IV_LEN = 16
_BLOCK_LEN = 16
_TAG_LEN = 32  # HMAC-SHA256 digest length
_KEY_LEN = 32  # 256 bits
_PBKDF2_ITERATIONS = 100_000
_SALT_LEN = 16


class SecretEncryptor:
    """Authenticated encryption using HMAC-SHA256 in counter mode.

    Args:
        key: A 32-byte master key. If ``None``, you must call
            :meth:`derive_key` or :meth:`load_key_file` before
            encrypting/decrypting.
    """

    def __init__(self, key: bytes | None = None) -> None:
        if key is not None and len(key) != _KEY_LEN:
            raise ValueError(
                f"Key must be exactly {_KEY_LEN} bytes, got {len(key)}",
            )
        self._key: bytes | None = key

    # ------------------------------------------------------------------
    # Key derivation
    # ------------------------------------------------------------------

    @staticmethod
    def derive_key(
        password: str,
        salt: bytes | None = None,
    ) -> tuple[bytes, bytes]:
        """Derive a 256-bit key from *password* using PBKDF2-HMAC-SHA256.

        Args:
            password: Human-readable master password.
            salt: Optional salt bytes. A random 16-byte salt is generated
                when ``None``.

        Returns:
            ``(key, salt)`` tuple where *key* is 32 bytes.
        """
        if salt is None:
            salt = os.urandom(_SALT_LEN)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            _PBKDF2_ITERATIONS,
            dklen=_KEY_LEN,
        )
        return key, salt

    # ------------------------------------------------------------------
    # Encrypt / Decrypt
    # ------------------------------------------------------------------

    def _require_key(self) -> bytes:
        if self._key is None:
            raise RuntimeError(
                "No encryption key set. Call derive_key() or " "load_key_file() first.",
            )
        return self._key

    @staticmethod
    def _pkcs7_pad(data: bytes) -> bytes:
        pad_len = _BLOCK_LEN - (len(data) % _BLOCK_LEN)
        return data + bytes([pad_len] * pad_len)

    @staticmethod
    def _pkcs7_unpad(data: bytes) -> bytes:
        if not data:
            raise ValueError("Cannot unpad empty data")
        pad_len = data[-1]
        if pad_len < 1 or pad_len > _BLOCK_LEN:
            raise ValueError("Invalid PKCS#7 padding")
        if data[-pad_len:] != bytes([pad_len] * pad_len):
            raise ValueError("Invalid PKCS#7 padding")
        return data[:-pad_len]

    @staticmethod
    def _keystream_block(key: bytes, iv: bytes, index: int) -> bytes:
        """Derive a 16-byte keystream block using HMAC-SHA256 as PRF."""
        counter = struct.pack(">I", index)
        digest = hmac.new(key, iv + counter, hashlib.sha256).digest()
        return digest[:_BLOCK_LEN]

    @staticmethod
    def _xor_bytes(a: bytes, b: bytes) -> bytes:
        return bytes(x ^ y for x, y in zip(a, b))

    def encrypt(self, plaintext: str) -> str:
        """Encrypt *plaintext* and return a base64-encoded token.

        The token format is: ``base64(IV + ciphertext + auth_tag)``.
        """
        key = self._require_key()
        iv = os.urandom(_IV_LEN)

        padded = self._pkcs7_pad(plaintext.encode("utf-8"))
        num_blocks = len(padded) // _BLOCK_LEN

        ciphertext_blocks: list[bytes] = []
        for i in range(num_blocks):
            pt_block = padded[i * _BLOCK_LEN : (i + 1) * _BLOCK_LEN]
            ks_block = self._keystream_block(key, iv, i)
            ciphertext_blocks.append(self._xor_bytes(pt_block, ks_block))

        ciphertext = b"".join(ciphertext_blocks)

        # Authenticate: HMAC-SHA256(key, iv || ciphertext)
        tag = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()

        return base64.b64encode(iv + ciphertext + tag).decode("ascii")

    def decrypt(self, token: str) -> str:
        """Decrypt a base64-encoded *token* produced by :meth:`encrypt`.

        Raises:
            ValueError: If the token is malformed or the authentication
                tag does not match (i.e., data was tampered with).
        """
        key = self._require_key()

        try:
            raw = base64.b64decode(token)
        except Exception as exc:
            raise ValueError("Invalid base64 token") from exc

        min_len = _IV_LEN + _BLOCK_LEN + _TAG_LEN  # at least one block
        if len(raw) < min_len:
            raise ValueError("Token too short")

        iv = raw[:_IV_LEN]
        tag = raw[-_TAG_LEN:]
        ciphertext = raw[_IV_LEN:-_TAG_LEN]

        if len(ciphertext) % _BLOCK_LEN != 0:
            raise ValueError(
                "Ciphertext length is not a multiple of block size",
            )

        # Verify auth tag first (constant-time comparison).
        expected_tag = hmac.new(key, iv + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            raise ValueError(
                "Authentication failed: ciphertext may have been tampered with",
            )

        # Decrypt
        num_blocks = len(ciphertext) // _BLOCK_LEN
        plaintext_blocks: list[bytes] = []
        for i in range(num_blocks):
            ct_block = ciphertext[i * _BLOCK_LEN : (i + 1) * _BLOCK_LEN]
            ks_block = self._keystream_block(key, iv, i)
            plaintext_blocks.append(self._xor_bytes(ct_block, ks_block))

        padded = b"".join(plaintext_blocks)
        return self._pkcs7_unpad(padded).decode("utf-8")

    # ------------------------------------------------------------------
    # Key file persistence
    # ------------------------------------------------------------------

    def save_key_file(self, path: Path, password: str) -> None:
        """Derive a key from *password* and persist the salt to *path*.

        The key itself is never stored — only the salt, so it can be
        re-derived later with the same password.

        The file is chmod 0o600 on systems that support it.
        """
        key, salt = self.derive_key(password)
        self._key = key

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(salt)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass

        logger.info("Encryption key salt saved to %s", path)

    def load_key_file(self, path: Path, password: str) -> bytes:
        """Load salt from *path*, derive the key, and return it.

        The encryptor's internal key is also set so subsequent
        :meth:`encrypt`/:meth:`decrypt` calls use it.
        """
        if not path.is_file():
            raise FileNotFoundError(f"Key file not found: {path}")

        salt = path.read_bytes()
        if len(salt) != _SALT_LEN:
            raise ValueError(
                f"Invalid key file: expected {_SALT_LEN} bytes of salt, "
                f"got {len(salt)}",
            )

        key, _ = self.derive_key(password, salt=salt)
        self._key = key
        return key
