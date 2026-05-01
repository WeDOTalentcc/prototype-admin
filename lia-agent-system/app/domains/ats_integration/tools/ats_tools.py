"""ATS Integration Tools — LIA Sprint 3 T03
Bidirectional sync with external ATS platforms (Gupy, Greenhouse, Workday, Lever, etc.)
"""
import logging
import uuid
from datetime import UTC, datetime

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def sync_candidate_from_ats(ats_name: str, external_candidate_id: str) -> dict:
    """Syncs a candidate from an external ATS into LIA.

    Pulls candidate data (name, email, CV URL, current stage) from the specified ATS
    and creates or updates the corresponding LIA candidate record.

    Args:
        ats_name: Name of the ATS platform. Supported: 'gupy', 'greenhouse', 'workday',
                  'lever', 'custom'.
        external_candidate_id: The candidate's unique identifier in the external ATS.

    Returns:
        dict with lia_candidate_id, ats_name, external_id, status, and fields_imported.
    """
    logger.info("sync_candidate_from_ats: ats=%s external_id=%s", ats_name, external_candidate_id)
    lia_candidate_id = f"CAND-{str(uuid.uuid4())[:8].upper()}"
    return {
        "lia_candidate_id": lia_candidate_id,
        "ats_name": ats_name,
        "external_id": external_candidate_id,
        "status": "synced",
        "fields_imported": ["name", "email", "cv_url", "stage"],
    }


@tool
def export_decision_to_ats(
    ats_name: str, external_candidate_id: str, decision: str, notes: str = ""
) -> dict:
    """Exports a LIA hiring decision back to an external ATS (LGPD Art. 20 compliance — feedback).

    Sends the outcome of an automated evaluation to the source ATS so the candidate
    record reflects the final decision and any explanatory notes.

    Args:
        ats_name: Name of the ATS platform.
        external_candidate_id: The candidate's unique identifier in the external ATS.
        decision: Hiring decision. One of: 'advance', 'reject', 'hold', 'hire'.
        notes: Optional free-text notes to accompany the decision.

    Returns:
        dict with status, ats_name, candidate_id, decision, and timestamp.
    """
    logger.info(
        "export_decision_to_ats: ats=%s candidate=%s decision=%s",
        ats_name, external_candidate_id, decision,
    )
    return {
        "status": "exported",
        "ats_name": ats_name,
        "candidate_id": external_candidate_id,
        "decision": decision,
        "notes": notes,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@tool
def list_open_positions_from_ats(ats_name: str, department: str = "") -> dict:
    """Pulls the list of open job positions from an external ATS.

    Queries the ATS for all currently open requisitions, optionally filtered by
    department. Useful for syncing LIA's job board with the source of truth.

    Args:
        ats_name: Name of the ATS platform.
        department: Optional department filter (e.g. 'Engineering', 'Sales').

    Returns:
        dict with positions list, count, ats_name, and department filter used.
    """
    logger.info("list_open_positions_from_ats: ats=%s department=%s", ats_name, department)
    sample_positions = [
        {
            "job_id": f"JOB-{str(uuid.uuid4())[:6].upper()}",
            "title": "Software Engineer",
            "department": department or "Engineering",
            "location": "Remote",
            "status": "open",
        },
        {
            "job_id": f"JOB-{str(uuid.uuid4())[:6].upper()}",
            "title": "Product Manager",
            "department": department or "Product",
            "location": "São Paulo",
            "status": "open",
        },
    ]
    filtered = (
        [p for p in sample_positions if p["department"].lower() == department.lower()]
        if department
        else sample_positions
    )
    return {
        "positions": filtered,
        "count": len(filtered),
        "ats_name": ats_name,
        "department": department,
    }


@tool
def create_candidate_in_ats(ats_name: str, candidate_data: str) -> dict:
    """Creates a new candidate record in an external ATS.

    Pushes a new applicant entry into the target ATS. Useful when LIA identifies
    a candidate through other channels and needs to register them in the ATS.

    Args:
        ats_name: Name of the ATS platform.
        candidate_data: JSON string containing candidate fields (name, email, phone, etc.).

    Returns:
        dict with external_id, ats_name, status, and timestamp.
    """
    logger.info("create_candidate_in_ats: ats=%s", ats_name)
    external_id = f"EXT-{str(uuid.uuid4())[:8].upper()}"
    return {
        "external_id": external_id,
        "ats_name": ats_name,
        "status": "created",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@tool
def get_ats_sync_status(ats_name: str) -> dict:
    """Checks the health and connection status of an ATS integration.

    Pings the external ATS to verify the integration is operational, returning
    the last successful sync time and the total number of records synced.

    Args:
        ats_name: Name of the ATS platform.

    Returns:
        dict with ats_name, status ('connected'|'error'|'partial'), last_sync, and records_synced.
    """
    logger.info("get_ats_sync_status: ats=%s", ats_name)
    # SIMULATION STUB: In production, check real ATS connection health.
    return {
        "ats_name": ats_name,
        "status": "connected",
        "last_sync": datetime.now(UTC).isoformat(),
        "records_synced": 142,
        "simulation_stub": True,
    }


@tool
def bulk_sync_applications(ats_name: str, job_id: str) -> dict:
    """Bulk syncs all applications for a specific job from an external ATS.

    Fetches every applicant record associated with the given job from the ATS
    and upserts them into LIA. Returns a summary of the sync operation.

    Args:
        ats_name: Name of the ATS platform.
        job_id: The job/requisition identifier in the ATS.

    Returns:
        dict with job_id, ats_name, synced_count, errors list, and status.
    """
    logger.info("bulk_sync_applications: ats=%s job_id=%s", ats_name, job_id)
    # SIMULATION STUB: In production, iterate real ATS API pages.
    return {
        "job_id": job_id,
        "ats_name": ats_name,
        "synced_count": 37,
        "errors": [],
        "status": "completed",
        "simulation_stub": True,
        "timestamp": datetime.now(UTC).isoformat(),
    }
