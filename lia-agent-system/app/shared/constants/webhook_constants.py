"""
Canonical webhook constants — single source of truth.

P1-W3-13: Unified HMAC signature header across all 3 webhook systems
(Studio Webhooks, Job Status Webhooks, Communication Webhooks).

All outgoing webhook dispatchers MUST use WEBHOOK_SIGNATURE_HEADER as the
primary signature header. WEBHOOK_SIGNATURE_HEADER_LEGACY is sent alongside
for backward compatibility with clients already configured.
"""

# Canonical outgoing signature header (use this everywhere)
WEBHOOK_SIGNATURE_HEADER = "X-WeDO-Signature"

# Legacy header kept for backward compat — sent alongside canonical header
# to avoid breaking existing webhook receivers during transition period.
WEBHOOK_SIGNATURE_HEADER_LEGACY = "X-Webhook-Signature"

# Event type header (Studio Webhooks)
WEBHOOK_EVENT_HEADER = "X-WeDO-Event"
