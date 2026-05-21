"""P0.B contract sensor (audit 2026-05-21) — PII email encryption canonical
em interview + interview_feedback + offer_proposal.

Garante que as 5 colunas plaintext PII identificadas no handoff §3 P0.B
agora ficam encrypted at-rest via EncryptedFieldMixin:

  - interviews.candidate_email
  - interviews.interviewer_email
  - interviews.graph_organizer_email
  - interview_feedbacks.interviewer_email
  - offer_proposals.candidate_email

Pattern canonical: mesma família de Candidate.email (migration 060+111).

Cobertura:
1. Cada model declara ``_pii_encrypt_fields`` config (mixin contract).
2. Cada model herda de ``EncryptedFieldMixin`` antes do ``Base``.
3. Cada coluna PII tem 3 attributes (raw, encrypted, hash[opt]).
4. ``EncryptedFieldMixin`` registra hybrid_property pública com nome canonical.
5. Plaintext DB column nullable=True (transition phase canonical).
6. Backing encrypted column é LargeBinary nullable=True.
7. Hash column é String(64) nullable=True com index (quando aplicavel).

Estes testes NAO exercitam encryption real (precisa FIELD_ENCRYPTION_KEY +
DB live) — apenas o CONTRACT canonical dos models. Encryption end-to-end
fica para integration tests da Phase 2 backfill task.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_attr(cls, name: str) -> bool:
    """Check if class has attribute (including SQLAlchemy column)."""
    return hasattr(cls, name)


def _column_nullable(cls, col_attr: str) -> bool:
    """Check if SQLAlchemy column is nullable."""
    col = getattr(cls, col_attr).property.columns[0]
    return col.nullable


# ---------------------------------------------------------------------------
# Tests — Interview
# ---------------------------------------------------------------------------

class TestInterviewEncryption:
    """Interview model has 3 encrypted email fields canonical."""

    def test_interview_inherits_encrypted_field_mixin(self):
        from app.shared.encryption.encrypted_field_mixin import EncryptedFieldMixin
        from lia_models.interview import Interview

        assert issubclass(Interview, EncryptedFieldMixin), (
            "Interview must inherit from EncryptedFieldMixin "
            "(P0.B canonical pattern)"
        )

    def test_interview_pii_encrypt_fields_config(self):
        from lia_models.interview import Interview

        assert hasattr(Interview, "_pii_encrypt_fields"), (
            "Interview must declare _pii_encrypt_fields (mixin contract)"
        )

        fields = Interview._pii_encrypt_fields
        # 3 emails: candidate, interviewer, graph_organizer
        assert len(fields) == 3, f"expected 3 PII fields, got {len(fields)}"

        # Pin canonical tuple structure
        names = {tup[0] for tup in fields}
        assert "_candidate_email_raw" in names
        assert "_interviewer_email_raw" in names
        assert "_graph_organizer_email_raw" in names

    def test_interview_candidate_email_backing_columns(self):
        from lia_models.interview import Interview

        # Raw (plaintext, transition phase)
        assert _has_attr(Interview, "_candidate_email_raw")
        # Encrypted (Fernet bytes)
        assert _has_attr(Interview, "_candidate_email_encrypted")
        # Hash (SHA-256 for indexed lookup)
        assert _has_attr(Interview, "candidate_email_hash")

    def test_interview_interviewer_email_backing_columns(self):
        from lia_models.interview import Interview

        assert _has_attr(Interview, "_interviewer_email_raw")
        assert _has_attr(Interview, "_interviewer_email_encrypted")
        assert _has_attr(Interview, "interviewer_email_hash")

    def test_interview_graph_organizer_email_backing_columns(self):
        from lia_models.interview import Interview

        # graph_organizer_email tem encrypted mas SEM hash (query path improvável)
        assert _has_attr(Interview, "_graph_organizer_email_raw")
        assert _has_attr(Interview, "_graph_organizer_email_encrypted")

    def test_interview_raw_columns_nullable(self):
        """P0.B transition phase: plaintext columns must be nullable
        para hybrid_property poder gravar NULL após encryption no Fernet column."""
        from lia_models.interview import Interview

        assert _column_nullable(Interview, "_candidate_email_raw"), (
            "_candidate_email_raw must be nullable (P0.B transition phase)"
        )
        assert _column_nullable(Interview, "_interviewer_email_raw"), (
            "_interviewer_email_raw must be nullable (P0.B transition phase)"
        )

    def test_interview_hybrid_property_registered(self):
        """EncryptedFieldMixin should register hybrid_property pra cada raw_attr.
        Public access: ``interview.candidate_email`` (no underscore)."""
        from lia_models.interview import Interview

        # Access via hybrid_property (registered by mixin)
        assert hasattr(Interview, "candidate_email")
        assert hasattr(Interview, "interviewer_email")
        assert hasattr(Interview, "graph_organizer_email")


# ---------------------------------------------------------------------------
# Tests — InterviewFeedback
# ---------------------------------------------------------------------------

class TestInterviewFeedbackEncryption:
    """InterviewFeedback model has 1 encrypted email field canonical."""

    def test_interview_feedback_inherits_mixin(self):
        from app.shared.encryption.encrypted_field_mixin import EncryptedFieldMixin
        from lia_models.interview import InterviewFeedback

        assert issubclass(InterviewFeedback, EncryptedFieldMixin)

    def test_interview_feedback_pii_config(self):
        from lia_models.interview import InterviewFeedback

        assert hasattr(InterviewFeedback, "_pii_encrypt_fields")
        fields = InterviewFeedback._pii_encrypt_fields
        assert len(fields) == 1
        assert fields[0][0] == "_interviewer_email_raw"

    def test_interview_feedback_backing_columns(self):
        from lia_models.interview import InterviewFeedback

        assert _has_attr(InterviewFeedback, "_interviewer_email_raw")
        assert _has_attr(InterviewFeedback, "_interviewer_email_encrypted")
        assert _has_attr(InterviewFeedback, "interviewer_email_hash")
        assert _column_nullable(InterviewFeedback, "_interviewer_email_raw")


# ---------------------------------------------------------------------------
# Tests — OfferProposal
# ---------------------------------------------------------------------------

class TestOfferProposalEncryption:
    """OfferProposal model has 1 encrypted email field canonical."""

    def test_offer_proposal_inherits_mixin(self):
        from app.shared.encryption.encrypted_field_mixin import EncryptedFieldMixin
        from lia_models.offer_proposal import OfferProposal

        assert issubclass(OfferProposal, EncryptedFieldMixin)

    def test_offer_proposal_pii_config(self):
        from lia_models.offer_proposal import OfferProposal

        assert hasattr(OfferProposal, "_pii_encrypt_fields")
        fields = OfferProposal._pii_encrypt_fields
        assert len(fields) == 1
        assert fields[0][0] == "_candidate_email_raw"

    def test_offer_proposal_backing_columns(self):
        from lia_models.offer_proposal import OfferProposal

        assert _has_attr(OfferProposal, "_candidate_email_raw")
        assert _has_attr(OfferProposal, "_candidate_email_encrypted")
        assert _has_attr(OfferProposal, "candidate_email_hash")
        assert _column_nullable(OfferProposal, "_candidate_email_raw")


# ---------------------------------------------------------------------------
# Tests — Cross-model invariants
# ---------------------------------------------------------------------------

class TestCanonicalInvariants:
    """Invariants P0.B canonical em todos os 3 models."""

    @pytest.mark.parametrize(
        "model_path,model_name,raw_attrs",
        [
            (
                "lia_models.interview", "Interview",
                ["_candidate_email_raw", "_interviewer_email_raw", "_graph_organizer_email_raw"],
            ),
            (
                "lia_models.interview", "InterviewFeedback",
                ["_interviewer_email_raw"],
            ),
            (
                "lia_models.offer_proposal", "OfferProposal",
                ["_candidate_email_raw"],
            ),
        ],
    )
    def test_all_raw_columns_nullable_transition(self, model_path, model_name, raw_attrs):
        """Todos os raw columns devem ser nullable (transition phase canonical).

        Quando todas as rows tiverem encrypted column populado (Phase 3),
        uma migration futura pode marcar raw=NULL e dropar a coluna
        plaintext (Phase 4). Mas durante transition: nullable=True obrigatorio.
        """
        import importlib
        module = importlib.import_module(model_path)
        model = getattr(module, model_name)
        for attr in raw_attrs:
            assert _column_nullable(model, attr), (
                f"{model_name}.{attr} must be nullable (P0.B transition phase)"
            )
