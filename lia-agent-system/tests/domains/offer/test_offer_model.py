"""
PR-B — test_offer_model.py

Smoke test: OfferProposal model importa sem erros e tem os campos esperados.
"""
import pytest


class TestOfferProposalModel:

    def test_model_importable(self):
        from lia_models.offer_proposal import OfferProposal
        assert OfferProposal.__tablename__ == "offer_proposals"

    def test_required_columns(self):
        """Sprint F.4 #42 canonical-remap: required columns now use canonical
        names (job_vacancy_id, salary, created_by) instead of legacy names
        (job_id, offered_salary, created_by_user_id)."""
        from lia_models.offer_proposal import OfferProposal
        cols = {c.name for c in OfferProposal.__table__.columns}
        required = {
            "id", "company_id", "candidate_id", "job_vacancy_id",
            "job_data_snapshot", "candidate_data_snapshot",
            "salary", "status",
            "created_by", "created_at", "updated_at",
        }
        assert required.issubset(cols), f"Missing columns: {required - cols}"

    def test_multi_tenant_company_id_indexed(self):
        from lia_models.offer_proposal import OfferProposal
        from sqlalchemy import inspect
        mapper = inspect(OfferProposal)
        col = OfferProposal.__table__.c["company_id"]
        assert col is not None
        assert not col.nullable

    def test_in_lia_models_init(self):
        from lia_models import OfferProposal
        assert OfferProposal is not None
