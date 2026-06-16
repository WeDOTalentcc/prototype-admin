"""lia-pii — PII masking, field visibility, LGPD consent for WeDOTalent.

Extracted from lia-agent-system app/shared/pii_masking.py and
app/shared/rbac/pii_field_{catalog,resolver}.py.

Public API (stable):
  masking:         mask_pii, mask_pii_outbound, strip_pii_for_llm_prompt,
                   PIIMaskingFilter, install_global_pii_masking,
                   get_masked_logger, mask_phone_preserve_tail,
                   set_chat_pii_mask_identity, reset_chat_pii_mask_identity,
                   chat_should_mask_identity
  field_catalog:   GATEABLE_PII_FIELDS, SALARY_FIELDS, SENSITIVE_FIELDS,
                   ALWAYS_VISIBLE_FIELDS, VACANCY_FIELDS, ALL_CONFIGURABLE_FIELDS,
                   field_group
  field_visibility: resolve_pii_field_visibility, resolve_field_visibility
"""

from lia_pii.masking import (
    CPF_PATTERN,
    EMAIL_PATTERN,
    PHONE_BR_PATTERN,
    PII_PATTERNS,
    PIIMaskingFilter,
    chat_should_mask_identity,
    get_masked_logger,
    install_global_pii_masking,
    mask_phone_preserve_tail,
    mask_pii,
    mask_pii_outbound,
    reset_chat_pii_mask_identity,
    set_chat_pii_mask_identity,
    strip_pii_for_llm_prompt,
)
from lia_pii.field_catalog import (
    ALL_CONFIGURABLE_FIELDS,
    ALWAYS_VISIBLE_FIELDS,
    GATEABLE_PII_FIELDS,
    SALARY_FIELDS,
    SENSITIVE_FIELDS,
    VACANCY_FIELDS,
    field_group,
)
from lia_pii.field_visibility import (
    resolve_field_visibility,
    resolve_pii_field_visibility,
)

__all__ = [
    # masking
    "CPF_PATTERN",
    "EMAIL_PATTERN",
    "PHONE_BR_PATTERN",
    "PII_PATTERNS",
    "PIIMaskingFilter",
    "chat_should_mask_identity",
    "get_masked_logger",
    "install_global_pii_masking",
    "mask_phone_preserve_tail",
    "mask_pii",
    "mask_pii_outbound",
    "reset_chat_pii_mask_identity",
    "set_chat_pii_mask_identity",
    "strip_pii_for_llm_prompt",
    # field_catalog
    "ALL_CONFIGURABLE_FIELDS",
    "ALWAYS_VISIBLE_FIELDS",
    "GATEABLE_PII_FIELDS",
    "SALARY_FIELDS",
    "SENSITIVE_FIELDS",
    "VACANCY_FIELDS",
    "field_group",
    # field_visibility
    "resolve_field_visibility",
    "resolve_pii_field_visibility",
]
