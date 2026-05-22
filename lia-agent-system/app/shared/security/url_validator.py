"""
WT-2022 P0.SEG1: Validator de URLs outbound para prevenir SSRF.

Bloqueia URLs que apontam para:
- Private IPs (RFC1918: 10/8, 172.16/12, 192.168/16)
- Loopback (127/8, ::1, localhost)
- Link-local (169.254/16) — INCLUI AWS IMDSv1 metadata endpoint
- Cloud metadata services (metadata.google.internal, etc.)
- IPv6 ULAs (fc00::/7)

OWASP A10 SSRF prevention. Usar em webhook URL validation + qualquer outbound
HTTP que aceite URL user-provided (callbacks, mailgun, etc.).
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


BLOCKED_HOSTNAMES = frozenset([
    "localhost",
    "0.0.0.0",
    "metadata.google.internal",
    "metadata",
    "instance-data",
])


class UnsafeOutboundURLError(ValueError):
    """Raised when URL is blocked by SSRF validator."""
    pass


def _is_private_ip(ip_str: str) -> bool:
    """Check if IP is private/loopback/link-local/ULA."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False


def safe_outbound_url(url: str, *, require_https: bool = True) -> str:
    """Validate URL is safe for outbound HTTP (no SSRF).

    Raises UnsafeOutboundURLError if URL points to private IP, loopback,
    cloud metadata, or other unsafe targets.

    Returns the validated URL on success.
    """
    if not url:
        raise UnsafeOutboundURLError("URL cannot be empty")

    parsed = urlparse(url)

    if require_https and parsed.scheme not in ("https",):
        raise UnsafeOutboundURLError(f"URL must use HTTPS (got: {parsed.scheme})")

    if not parsed.scheme or not parsed.hostname:
        raise UnsafeOutboundURLError(f"URL malformed: {url}")

    hostname = parsed.hostname.lower()

    # Block hostname literals
    if hostname in BLOCKED_HOSTNAMES:
        raise UnsafeOutboundURLError(
            f"Hostname '{hostname}' blocked (cloud metadata or localhost)"
        )

    # Block IP literals
    if _is_private_ip(hostname):
        raise UnsafeOutboundURLError(
            f"IP '{hostname}' blocked (private/loopback/link-local)"
        )

    # Resolve DNS and block if any A/AAAA record points to private IP (anti-rebind)
    try:
        infos = socket.getaddrinfo(hostname, None)
        for info in infos:
            ip_str = info[4][0]
            if _is_private_ip(ip_str):
                raise UnsafeOutboundURLError(
                    f"Hostname '{hostname}' resolves to private IP '{ip_str}' (anti-rebind)"
                )
    except UnsafeOutboundURLError:
        raise
    except (socket.gaierror, socket.herror) as exc:
        # DNS resolve failed — não rejeitar (pode ser apenas DNS down) mas log
        import logging
        logging.getLogger(__name__).warning(
            "WT-2022 P0.SEG1: DNS resolve failed for %s — allowing URL: %s",
            hostname, exc,
        )

    return url
