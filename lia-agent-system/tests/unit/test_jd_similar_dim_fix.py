"""Test: JD_EMBEDDING_DIM = 768 aligns with DB Vector(768) columns.

A1 — P0 fix: the constant was 1536 which caused every JD embedding to be
silently discarded (len(embedding) != JD_EMBEDDING_DIM guard).
"""
import pytest
from app.domains.job_creation.services.jd_similar_service import JD_EMBEDDING_DIM


def test_jd_embedding_dim_is_768():
    """JD_EMBEDDING_DIM must match the DB Vector(768) column and OpenAI 768-dim output."""
    assert JD_EMBEDDING_DIM == 768, (
        f"JD_EMBEDDING_DIM={JD_EMBEDDING_DIM} — must be 768 to match Vector(768) cols. "
        "Was 1536, which caused every JD embedding to be silently dropped."
    )


def test_valid_768_dim_vector_passes_guard():
    """A 768-dim vector should pass the dim-check guard (len == JD_EMBEDDING_DIM)."""
    vector = [0.1] * 768
    assert len(vector) == JD_EMBEDDING_DIM


def test_invalid_1536_dim_vector_fails_guard():
    """A 1536-dim vector should fail the dim-check guard (stale OpenAI full-dim output)."""
    vector = [0.1] * 1536
    assert len(vector) != JD_EMBEDDING_DIM


def test_invalid_512_dim_vector_fails_guard():
    """A 512-dim vector should fail the dim-check guard."""
    vector = [0.1] * 512
    assert len(vector) != JD_EMBEDDING_DIM
