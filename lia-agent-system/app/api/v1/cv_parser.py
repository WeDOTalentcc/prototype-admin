"""
CV Parser API endpoints for uploading and parsing CVs.
"""
import logging
import re
import uuid
from datetime import date, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_service_or_user
from app.auth.models import User
from app.core.database import get_db
from app.domains.cv_screening.services.cv_parser import CVParserService, cv_parser_service, get_cv_parser_service
from app.domains.cv_screening.repositories.screening_repository import ScreeningRepository
from app.models.candidate import Candidate, CandidateEducation, CandidateExperience
from app.schemas.cv_parser import (
    CVConfirmRequest,
    CVConfirmResponse,
    CVParseTextRequest,
    CVUploadResponse,
    ParsedCV,
    SupportedFormatsResponse,
)
from app.utils.skill_classifier import classify_skills
from app.shared.security.require_company_id import require_company_id, require_company_id_strict_match

logger = logging.getLogger(__name__)

MAX_RAW_TEXT_RESPONSE_LENGTH = 5000

router = APIRouter(prefix="/cv", tags=["cv-parser"])


# TODO(phase2): extract to repository — CV parser result storage
def parse_date_of_birth(dob_string: str | None) -> date | None:
    """Parse date of birth from various formats."""
    if not dob_string:
        return None
    
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y",
    ]
    
    for fmt in formats:
        try:
            parsed = datetime.strptime(dob_string.strip(), fmt)
            return parsed.date()
        except ValueError:
            continue
    
    return None


def parse_location(location: str | None) -> tuple[str | None, str | None, str | None]:
    """
    Parse location string into city, state, country.
    
    Common formats:
    - "São Paulo, SP, Brasil"
    - "São Paulo - SP"
    - "Rio de Janeiro, RJ - Brasil"
    - "Belo Horizonte/MG"
    
    Returns: (city, state, country)
    """
    if not location:
        return None, None, None
    
    location = location.strip()
    
    location = re.sub(r'[–—]', '-', location)
    location = re.sub(r'\s*[/\-,]\s*', ', ', location)
    
    parts = [p.strip() for p in location.split(',') if p.strip()]
    
    brazilian_states = {
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
        'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
        'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO'
    }
    
    city = None
    state = None
    country = None
    
    if len(parts) >= 3:
        city = parts[0]
        if parts[1].upper() in brazilian_states:
            state = parts[1].upper()
            country = parts[2]
        else:
            state = parts[1]
            country = parts[2]
    elif len(parts) == 2:
        city = parts[0]
        if parts[1].upper() in brazilian_states:
            state = parts[1].upper()
            country = "Brasil"
        elif parts[1].lower() in ['brasil', 'brazil']:
            country = parts[1]
        else:
            state = parts[1]
    elif len(parts) == 1:
        city = parts[0]
    
    return city, state, country


def calculate_years_of_experience(experiences: list) -> int | None:
    """
    Calculate total years of experience from experience list.
    
    Parses start_date and end_date to calculate actual duration.
    Handles formats like: "Jan 2020", "2020-01", "Janeiro 2020", "2020"
    """
    if not experiences:
        return None
    
    total_months = 0
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    month_map = {
        'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
        'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12,
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6,
        'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12,
        'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    
    def parse_date(date_str: str | None, is_end: bool = False) -> tuple[int, int]:
        if not date_str:
            return (current_year, current_month) if is_end else (0, 0)
        
        date_str = date_str.lower().strip()
        
        if any(x in date_str for x in ['atual', 'present', 'current', 'hoje', 'now']):
            return (current_year, current_month)
        
        year_match = re.search(r'(19|20)\d{2}', date_str)
        year = int(year_match.group()) if year_match else 0
        
        month = 1
        for m_name, m_num in month_map.items():
            if m_name in date_str:
                month = m_num
                break
        
        month_num_match = re.match(r'(\d{1,2})[/\-](\d{4})', date_str)
        if month_num_match:
            month = int(month_num_match.group(1))
            year = int(month_num_match.group(2))
        
        return (year, month)
    
    for exp in experiences:
        start_date = getattr(exp, 'start_date', None) if hasattr(exp, 'start_date') else exp.get('start_date')
        end_date = getattr(exp, 'end_date', None) if hasattr(exp, 'end_date') else exp.get('end_date')
        is_current = getattr(exp, 'is_current', False) if hasattr(exp, 'is_current') else exp.get('is_current', False)
        
        start_year, start_month = parse_date(start_date, is_end=False)
        
        if is_current or not end_date:
            end_year, end_month = current_year, current_month
        else:
            end_year, end_month = parse_date(end_date, is_end=True)
        
        if start_year > 0 and end_year > 0:
            months = (end_year - start_year) * 12 + (end_month - start_month)
            total_months += max(0, months)
    
    if total_months == 0 and experiences:
        return len(experiences) * 2
    
    return max(1, round(total_months / 12)) if total_months > 0 else None


def _truncate_raw_text_for_response(parsed_cv: ParsedCV) -> ParsedCV:
    """Truncate raw_text to prevent large responses that cause frontend crashes."""
    if parsed_cv.raw_text and len(parsed_cv.raw_text) > MAX_RAW_TEXT_RESPONSE_LENGTH:
        truncated = parsed_cv.raw_text[:MAX_RAW_TEXT_RESPONSE_LENGTH]
        parsed_cv.raw_text = truncated + f"\n\n... [Truncado: {len(parsed_cv.raw_text) - MAX_RAW_TEXT_RESPONSE_LENGTH} caracteres omitidos]"
    return parsed_cv


CV_UPLOAD_DIR = Path("uploads/cvs")
CV_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload", response_model=CVUploadResponse)
async def upload_and_parse_cv(
    file: UploadFile = File(..., description="CV file (PDF, DOCX, DOC, or TXT)"),
    current_user: User = Depends(get_service_or_user),
    db: AsyncSession = Depends(get_db)
,
    cv_parser_svc: CVParserService = Depends(get_cv_parser_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Upload a CV file and extract structured candidate information.
    
    Supported formats: PDF, DOCX, DOC, TXT
    Maximum file size: 5MB
    
    Returns parsed CV data with AI-extracted information:
    - Contact info (name, email, phone, LinkedIn)
    - Work experiences
    - Education
    - Skills and languages
    
    The uploaded file is saved and its path is included in the response.
    Also checks for duplicate candidates and returns a warning if found.
    Requires authentication.
    """
    try:
        logger.info(f"Parsing CV: {file.filename}")
        
        file_content = await file.read()
        file_size = len(file_content)
        await file.seek(0)
        
        Path(file.filename).suffix.lower() if file.filename else ".pdf"
        safe_filename = re.sub(r'[^\w\-.]', '_', file.filename or "cv")
        unique_filename = f"{uuid.uuid4().hex[:12]}_{safe_filename}"
        file_path = CV_UPLOAD_DIR / unique_filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        file_url = f"/uploads/cvs/{unique_filename}"
        
        logger.info(f"CV file saved: {file_path}")
        
        parsed_cv = await cv_parser_svc.parse_cv(file)
        
        parsed_cv.file_url = file_url
        parsed_cv.file_size_bytes = file_size
        
        duplicate_check = await cv_parser_svc.check_duplicate(parsed_cv, db)
        
        duplicate_warning = None
        if duplicate_check.is_duplicate:
            duplicate_warning = {
                "message": f"Potential duplicate found ({duplicate_check.match_type})",
                "existing_candidate_id": str(duplicate_check.existing_candidate_id),
                "existing_candidate_name": duplicate_check.existing_candidate_name,
                "match_type": duplicate_check.match_type,
                "similarity_score": duplicate_check.similarity_score
            }
            logger.info(f"Duplicate candidate detected: {duplicate_check.existing_candidate_id}")
        
        _truncate_raw_text_for_response(parsed_cv)
        
        return CVUploadResponse(
            success=True,
            message="CV parsed successfully",
            parsed_cv=parsed_cv,
            duplicate_warning=duplicate_warning,
            candidate_id=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV upload failed: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/parse-text", response_model=CVUploadResponse)
async def parse_cv_text(
    request: CVParseTextRequest,
    current_user: User = Depends(get_service_or_user),
    db: AsyncSession = Depends(get_db)
,
    cv_parser_svc: CVParserService = Depends(get_cv_parser_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Parse plain text CV content and extract structured information.
    
    Use this endpoint when you already have the CV text (e.g., from copy-paste).
    Minimum text length: 50 characters.
    Requires authentication.
    """
    try:
        logger.info(f"Parsing CV text ({len(request.text)} chars)")
        
        parsed_cv = await cv_parser_svc.extract_with_ai(request.text)
        parsed_cv.raw_text = request.text
        parsed_cv.file_type = "text"
        
        duplicate_check = await cv_parser_svc.check_duplicate(parsed_cv, db)
        
        duplicate_warning = None
        if duplicate_check.is_duplicate:
            duplicate_warning = {
                "message": f"Potential duplicate found ({duplicate_check.match_type})",
                "existing_candidate_id": str(duplicate_check.existing_candidate_id),
                "existing_candidate_name": duplicate_check.existing_candidate_name,
                "match_type": duplicate_check.match_type,
                "similarity_score": duplicate_check.similarity_score
            }
        
        _truncate_raw_text_for_response(parsed_cv)
        
        return CVUploadResponse(
            success=True,
            message="CV text parsed successfully",
            parsed_cv=parsed_cv,
            duplicate_warning=duplicate_warning,
            candidate_id=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CV text parsing failed: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.post("/confirm", response_model=CVConfirmResponse)
async def confirm_cv_and_create_candidate(
    request: CVConfirmRequest,
    current_user: User = Depends(get_service_or_user),
    db: AsyncSession = Depends(get_db)
,
    cv_parser_svc: CVParserService = Depends(get_cv_parser_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Confirm parsed CV data and create a new candidate in the database.
    
    - Review and optionally modify the parsed CV data before confirming
    - Set override_duplicate=true to create even if duplicate found
    - Add tags and notes to the new candidate
    - Optionally link to a job vacancy
    - Creates CandidateExperience records for each work experience
    Requires authentication.
    """
    try:
        parsed_cv = request.parsed_cv
        
        duplicate_check = await cv_parser_svc.check_duplicate(parsed_cv, db)
        
        if duplicate_check.is_duplicate and not request.override_duplicate:
            return CVConfirmResponse(
                success=False,
                message=f"Duplicate candidate found ({duplicate_check.match_type}). Set override_duplicate=true to create anyway.",
                was_duplicate=True,
                merged_with_id=duplicate_check.existing_candidate_id
            )
        
        current_title = parsed_cv.current_title
        current_company = None
        
        if parsed_cv.experiences:
            current_exp = parsed_cv.experiences[0]
            if not current_title:
                current_title = current_exp.title
            current_company = current_exp.company
        
        years_of_experience = calculate_years_of_experience(parsed_cv.experiences)
        
        city, state, country = parse_location(parsed_cv.location)
        
        technical_skills, soft_skills = classify_skills(parsed_cv.skills if parsed_cv.skills else [])
        
        if hasattr(parsed_cv, 'soft_skills') and parsed_cv.soft_skills:
            for ss in parsed_cv.soft_skills:
                if ss not in soft_skills:
                    soft_skills.append(ss)
        
        languages_dict = {}
        for lang in parsed_cv.languages:
            if '(' in lang and ')' in lang:
                lang_name = lang.split('(')[0].strip()
                level = lang.split('(')[1].replace(')', '').strip()
                languages_dict[lang_name] = level
            else:
                languages_dict[lang] = "Não especificado"
        
        candidate_id = uuid.uuid4()
        
        candidate = Candidate(
            id=candidate_id,
            name=parsed_cv.full_name,
            email=parsed_cv.email or f"unknown_{uuid.uuid4().hex[:8]}@placeholder.com",
            phone=parsed_cv.phone,
            linkedin_url=parsed_cv.linkedin,
            github_url=parsed_cv.github,
            portfolio_url=parsed_cv.portfolio,
            current_title=current_title,
            current_company=current_company,
            years_of_experience=years_of_experience,
            self_introduction=parsed_cv.summary,
            technical_skills=technical_skills,
            soft_skills=soft_skills,
            seniority_level=getattr(parsed_cv, 'seniority_level', None),
            interests=getattr(parsed_cv, 'interests', []) if hasattr(parsed_cv, 'interests') else [],
            languages=languages_dict,
            certifications=parsed_cv.certifications if parsed_cv.certifications else [],
            date_of_birth=parse_date_of_birth(getattr(parsed_cv, 'date_of_birth', None)),
            location_city=city,
            location_state=state,
            location_country=country or "Brasil",
            resume_url=parsed_cv.file_url,
            resume_text=parsed_cv.raw_text[:50000] if parsed_cv.raw_text else None,
            source="cv_upload",
            status="new",
            tags=request.tags or [],
            notes=request.notes,
            lia_insights={
                "cv_parsing": {
                    "confidence_score": parsed_cv.confidence_score,
                    "extraction_notes": parsed_cv.extraction_notes,
                    "parsed_at": parsed_cv.parsed_at.isoformat(),
                    "file_name": parsed_cv.file_name,
                    "file_type": parsed_cv.file_type,
                },
                "experiences_count": len(parsed_cv.experiences),
                "education_count": len(parsed_cv.education),
            },
            additional_data={
                "education": [edu.model_dump() for edu in parsed_cv.education],
                "job_vacancy_id": str(request.job_vacancy_id) if request.job_vacancy_id else None
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        experiences = [
            CandidateExperience(
                id=uuid.uuid4(),
                candidate_id=candidate_id,
                company_name=exp.company,
                title=exp.title,
                start_date=exp.start_date,
                end_date=exp.end_date if not exp.is_current else "Atual",
                is_current=exp.is_current,
                description=exp.description,
                location=exp.location,
                sequence_order=idx,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for idx, exp in enumerate(parsed_cv.experiences)
        ]
        educations = [
            CandidateEducation(
                id=uuid.uuid4(),
                candidate_id=candidate_id,
                institution=edu.institution,
                degree=edu.degree,
                field_of_study=edu.field_of_study,
                start_date=edu.start_date,
                end_date=edu.end_date,
                is_completed=edu.is_completed,
                description=edu.description if hasattr(edu, 'description') else None,
                sequence_order=idx,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            for idx, edu in enumerate(parsed_cv.education)
        ]

        repo = ScreeningRepository(db)
        candidate = await repo.add_candidate_with_experiences_and_education(
            candidate, experiences, educations
        )
        
        # pii-logs ok: PII (nome/email candidate ou recruiter) mascarado em runtime via PIIMaskingFilter (LGPD Art.46)
        logger.info(f"Candidate created from CV: {candidate.id} - {candidate.id} (with {len(parsed_cv.experiences)} experiences)")
        
        return CVConfirmResponse(
            success=True,
            message="Candidate created successfully from CV",
            candidate_id=candidate.id,  # type: ignore[union-attr]
            candidate_name=str(candidate.name) if candidate.name else None,  # type: ignore[union-attr]
            candidate_email=str(candidate.email) if candidate.email else None,  # type: ignore[union-attr]
            was_duplicate=duplicate_check.is_duplicate,
            merged_with_id=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"CV confirmation failed: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")


@router.get("/formats", response_model=SupportedFormatsResponse)
async def get_supported_formats(
    cv_parser_svc: CVParserService = Depends(get_cv_parser_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Get list of supported CV file formats and size limits.
    """
    formats_info = cv_parser_svc.get_supported_formats()
    return SupportedFormatsResponse(**formats_info)


@router.get("/health", response_model=None)
async def health_check(company_id: str = Depends(require_company_id)):
    # multi-tenancy: public endpoint (health) — no tenant data
    """
    Check if CV Parser service is properly configured.
    """
    return {
        "service": "CV Parser",
        "status": "operational",
        "supported_formats": ["PDF", "DOCX", "DOC", "TXT"],
        "max_file_size_mb": 5,
        "ai_extraction": "Claude (Anthropic)"
    }


@router.post("/upload-and-screen", response_model=None)
async def upload_and_screen_cv(
    file: UploadFile | None = File(None),
    cv_text: str | None = Form(None),
    vacancy_title: str | None = Form(None),
    vacancy_id: str | None = Form(None),
    run_bars: bool = Form(True),
    company_id: str | None = Form(None),
    user_id: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_service_or_user),
    parser: CVParserService = Depends(get_cv_parser_service),
_company_gate: str = Depends(require_company_id_strict_match("form.company_id"))):
    # multi-tenancy: function already calls _require_company_id or equivalent (sensor false positive)
    """
    Full CV flow: parse → create Candidate → add to vacancy → BARS score.
    
    Accepts either a file upload or raw CV text.
    Returns structured result with candidate_id, BARS score, and messages.
    """

    try:
        # Determine company_id from JWT or form field
        resolved_company = company_id or getattr(current_user, "company_id", None)
        if not resolved_company:
            raise HTTPException(status_code=400, detail="company_id is required")
        resolved_user = user_id or getattr(current_user, "id", "system")

        # Extract CV text
        if file:
            raw_text = ""
            if file.content_type == "application/pdf" or (file.filename or "").endswith(".pdf"):
                content_bytes = await file.read()
                raw_text = await parser.extract_text_from_pdf(content_bytes)
            else:
                raw_bytes = await file.read()
                raw_text = raw_bytes.decode("utf-8", errors="ignore")
        elif cv_text:
            raw_text = cv_text
        else:
            raise HTTPException(status_code=400, detail="Either file or cv_text is required")

        # Build execution context

        class _MockContext:
            company_id = resolved_company
            user_id = resolved_user

        ctx = _MockContext()

        # Call create_and_screen_candidate tool
        from app.domains.cv_screening.tools.cv_upload_tool import create_and_screen_candidate
from app.shared.errors import LIAError

        result = await create_and_screen_candidate(
            cv_text=raw_text,
            vacancy_title=vacancy_title,
            vacancy_id=vacancy_id,
            run_bars=run_bars,
            run_wsi=False,
            context=ctx,
        )

        return {
            "success": result.get("success", False),
            "candidate_id": result.get("candidate_id"),
            "candidate_name": result.get("candidate_name"),
            "job_id": result.get("job_id"),
            "job_title": result.get("job_title"),
            "match_score": result.get("match_score"),
            "recommendation": result.get("recommendation"),
            "message": result.get("message", ""),
            "parsed": result.get("steps", {}).get("parse_create", {}).get("parsed", {}),
            "error": result.get("error"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"upload-and-screen error: {e}", exc_info=True)
        raise LIAError(message="Erro interno do servidor")
