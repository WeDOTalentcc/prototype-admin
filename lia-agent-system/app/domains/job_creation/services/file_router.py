"""
Smart File Router — C.1 of Phase C.

Routes uploaded files to the correct processing pipeline:
  - CV (PDF/DOCX) → CV Screening pipeline
  - JD (PDF/DOCX) → Wizard intake (auto-start job creation)
  - Generic → file_analysis (LLM-based content analysis)

Detection uses:
  1. Filename heuristics
  2. Content-based LLM classification (if heuristics inconclusive)

Governance:
  - LGPD: Consent check before processing CV
  - Fairness: JD files go through fairness check in wizard
  - Audit: File processing tracked via LLM callbacks
"""

import logging
import re
from typing import Literal, Optional

logger = logging.getLogger(__name__)

FileType = Literal["cv", "jd", "generic"]

# Filename patterns for quick classification
CV_PATTERNS = re.compile(
    r'\b(?:curricul|cv|resume|curr[íi]culo|perfil|candidat)\b',
    re.IGNORECASE,
)
JD_PATTERNS = re.compile(
    r'\b(?:job.?desc|vaga|descri[cç][aã]o.?(?:da|de).?vaga|jd|requisitos|cargo|posi[cç][aã]o)\b',
    re.IGNORECASE,
)

# MIME type mapping
SUPPORTED_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/msword": "doc",
    "text/plain": "txt",
    "text/csv": "csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/json": "json",
    "image/png": "image",
    "image/jpeg": "image",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
}

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


def classify_file(
    filename: str,
    mime_type: Optional[str] = None,
    content_preview: Optional[str] = None,
) -> FileType:
    """Classify a file into CV, JD, or generic.

    Priority:
    1. Filename heuristics (fast, no LLM)
    2. Content preview heuristics (if available)
    3. Default to generic

    Args:
        filename: Original filename
        mime_type: MIME type (optional)
        content_preview: First ~500 chars of file content (optional)

    Returns:
        FileType: "cv", "jd", or "generic"
    """
    # 1. Filename heuristics
    name_lower = filename.lower()
    if CV_PATTERNS.search(name_lower):
        logger.info("[FileRouter] Classified as CV (filename): %s", filename)
        return "cv"
    if JD_PATTERNS.search(name_lower):
        logger.info("[FileRouter] Classified as JD (filename): %s", filename)
        return "jd"

    # 2. Content preview heuristics
    if content_preview:
        preview_lower = content_preview.lower()

        # CV indicators
        cv_indicators = [
            "experiência profissional", "experiencia profissional",
            "formação acadêmica", "formacao academica",
            "work experience", "professional experience",
            "education", "skills", "competências",
            "objetivo profissional", "resumo profissional",
        ]
        cv_score = sum(1 for ind in cv_indicators if ind in preview_lower)

        # JD indicators
        jd_indicators = [
            "responsabilidades", "responsibilities",
            "requisitos", "requirements",
            "benefícios", "benefits",
            "o que oferecemos", "what we offer",
            "perfil desejado", "qualificações",
            "modelo de trabalho", "faixa salarial",
        ]
        jd_score = sum(1 for ind in jd_indicators if ind in preview_lower)

        if cv_score >= 2 and cv_score > jd_score:
            logger.info("[FileRouter] Classified as CV (content): %s", filename)
            return "cv"
        if jd_score >= 2 and jd_score > cv_score:
            logger.info("[FileRouter] Classified as JD (content): %s", filename)
            return "jd"

    # 3. Default
    logger.info("[FileRouter] Classified as generic: %s", filename)
    return "generic"


def validate_file(
    filename: str,
    file_size: int,
    mime_type: Optional[str] = None,
) -> tuple[bool, Optional[str]]:
    """Validate file before processing.

    Returns:
        tuple of (is_valid, error_message)
    """
    if file_size > MAX_FILE_SIZE:
        return False, f"Arquivo muito grande ({file_size // (1024*1024)}MB). Maximo: 10MB."

    if file_size == 0:
        return False, "Arquivo vazio."

    # Check extension
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed_exts = {"pdf", "docx", "doc", "txt", "csv", "xlsx", "json", "png", "jpg", "jpeg", "pptx"}
    if ext not in allowed_exts:
        return False, f"Tipo de arquivo .{ext} nao suportado. Aceitos: {', '.join(sorted(allowed_exts))}"

    return True, None


def get_routing_action(file_type: FileType) -> dict:
    """Get the action to take for each file type.

    Returns:
        dict with routing instructions for the frontend/backend.
    """
    if file_type == "cv":
        return {
            "action": "cv_screening",
            "description": "Arquivo identificado como CV. Iniciando triagem...",
            "requires_consent": True,  # LGPD: consent before processing CV
            "pipeline": "useCvScreening",
        }
    elif file_type == "jd":
        return {
            "action": "wizard_intake",
            "description": "Arquivo identificado como JD. Iniciando criacao de vaga...",
            "requires_consent": False,
            "pipeline": "job_creation",
            "auto_start_wizard": True,
        }
    else:
        return {
            "action": "file_analysis",
            "description": "Analisando arquivo...",
            "requires_consent": False,
            "pipeline": "generic_analysis",
        }
