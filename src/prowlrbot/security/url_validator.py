# -*- coding: utf-8 -*-
"""URL validation to prevent SSRF attacks.

Blocks requests to private/internal networks, loopback, link-local,
and cloud metadata endpoints.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

# Cloud metadata endpoints (AWS, GCP, Azure)
_BLOCKED_HOSTS = frozenset(
    {
        "metadata.google.internal",
        "metadata.gfe.goog",
    },
)

_BLOCKED_PREFIXES = (
    "169.254.169.254",
    "fd00::",
)


def validate_outbound_url(url: str) -> tuple[bool, str]:
    """Check whether *url* is safe for server-side requests.

    Returns (allowed, reason).  If *allowed* is ``False``, the request
    MUST NOT proceed.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Malformed URL"

    if parsed.scheme not in ("http", "https"):
        return (
            False,
            f"Scheme '{parsed.scheme}' not allowed; use http or https",
        )

    hostname = parsed.hostname
    if not hostname:
        return False, "No hostname in URL"

    # Block known metadata hostnames
    if hostname.lower() in _BLOCKED_HOSTS:
        return False, f"Blocked host: {hostname}"

    # Resolve hostname to IP and validate
    try:
        infos = socket.getaddrinfo(
            hostname,
            parsed.port or 443,
            proto=socket.IPPROTO_TCP,
        )
    except socket.gaierror:
        return False, f"DNS resolution failed for {hostname}"

    for _family, _type, _proto, _canonname, sockaddr in infos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue

        if ip.is_loopback:
            return False, f"Loopback address {ip_str} blocked"
        if ip.is_private:
            return False, f"Private address {ip_str} blocked"
        if ip.is_reserved:
            return False, f"Reserved address {ip_str} blocked"
        if ip.is_link_local:
            return False, f"Link-local address {ip_str} blocked"
        # Cloud metadata IPs
        if ip_str.startswith("169.254.169.254"):
            return False, "Cloud metadata endpoint blocked"

    return True, "OK"
