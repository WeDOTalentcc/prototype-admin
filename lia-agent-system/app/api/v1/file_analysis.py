"""
File Analysis API - Endpoints for analyzing uploaded documents.
"""
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.domains.cv_screening.services.cv_parser import CVParserService, cv_parser_service, get_cv_parser_service
from app.shared.security.require_company_id import require_company_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["file-analysis"])


class FileAnalysisResponse(BaseModel):
    """Response from file analysis."""
    success: bool
    filename: str
    extractedText: str | None = None
    keywords: list[str] = []
    summary: str | None = None
    entities: dict | None = None
    candidate_id: str | None = None
    error: str | None = None


@router.post("/file", response_model=FileAnalysisResponse)
async def analyze_file(file: UploadFile = File(...),
    cv_parser_svc: CVParserService = Depends(get_cv_parser_service),
company_id: str = Depends(require_company_id)):
    # multi-tenancy: gated via Depends(require_company_id) + Postgres RLS runtime (Task #1143)
    """
    Analyze an uploaded file and extract relevant information.
    
    Supports PDF, DOC, DOCX, TXT, XLS, XLSX files.
    Uses AI to extract keywords, entities, and generate summaries.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    filename = file.filename.lower()
    
    try:
        # Read file content
        content = await file.read()
        
        # Check file type
        if filename.endswith(('.pdf', '.doc', '.docx')):
            # Use CV parser for document analysis
            await file.seek(0)
            parsed = await cv_parser_svc.parse_cv(file)
            
            if parsed:
                keywords = []
                if parsed.skills:
                    keywords.extend(parsed.skills[:10])
                if parsed.technical_skills:
                    keywords.extend(parsed.technical_skills[:5])
                if parsed.current_title:
                    keywords.append(parsed.current_title)
                
                # Remove duplicates while preserving order
                seen = set()
                unique_keywords = []
                for k in keywords:
                    if k.lower() not in seen:
                        seen.add(k.lower())
                        unique_keywords.append(k)
                
                # Extract candidate_id if already in DB
                candidate_id_found = getattr(parsed, 'candidate_id', None)

                # Parse location into city/state if available
                location_city = None
                location_state = None
                if parsed.location:
                    parts = [p.strip() for p in str(parsed.location).split(",")]
                    if len(parts) >= 2:
                        location_city = parts[0]
                        location_state = parts[1]
                    else:
                        location_city = parts[0]

                # Derive education_level from education list
                education_level = None
                if parsed.education:
                    edu = parsed.education[0]
                    education_level = getattr(edu, 'degree', None) or getattr(edu, 'level', None)

                # Derive current_company from most recent experience
                current_company = None
                if parsed.experiences:
                    current_company = getattr(parsed.experiences[0], 'company', None)

                entities = {
                    # Contact/profile fields mapped to frontend expected keys
                    "email": parsed.email,
                    "phone": parsed.phone,
                    "current_title": parsed.current_title,
                    "current_company": current_company,
                    "location_city": location_city,
                    "location_state": location_state,
                    "linkedin_url": parsed.linkedin,
                    "education_level": education_level,
                    "languages": ", ".join(parsed.languages) if parsed.languages else None,
                    # Legacy fields kept for backward compat
                    "skills": parsed.skills or [],
                    "job_titles": [parsed.current_title] if parsed.current_title else [],
                    "companies": [exp.company for exp in (parsed.experiences or []) if hasattr(exp, 'company') and exp.company][:5],
                    "locations": [parsed.location] if parsed.location else [],
                    "experience_years": getattr(parsed, 'years_of_experience', None),
                }
                # Remove None values so frontend hasFields check works correctly
                entities = {k: v for k, v in entities.items() if v is not None and v != [] and v != ""}
                
                years_exp = getattr(parsed, 'years_of_experience', None)
                summary = f"Documento analisado: {parsed.current_title or 'Profissional'}"
                if years_exp:
                    summary += f" com {years_exp} anos de experiência"
                if parsed.location:
                    summary += f" em {parsed.location}"
                
                return FileAnalysisResponse(
                    success=True,
                    filename=file.filename,
                    extractedText=parsed.summary or "",
                    keywords=unique_keywords[:15],
                    summary=summary,
                    entities=entities,
                    candidate_id=candidate_id_found,
                )
        
        elif filename.endswith('.txt'):
            # Plain text file
            text = content.decode('utf-8', errors='ignore')
            keywords = extract_keywords_from_text(text)
            
            return FileAnalysisResponse(
                success=True,
                filename=file.filename,
                extractedText=text[:2000],
                keywords=keywords,
                summary=f"Arquivo de texto com {len(text)} caracteres",
            )
        
        elif filename.endswith(('.xls', '.xlsx')):
            # Excel file - extract basic info
            return FileAnalysisResponse(
                success=True,
                filename=file.filename,
                extractedText="Planilha Excel detectada",
                keywords=["Excel", "Dados", "Planilha"],
                summary="Planilha Excel para importação de dados",
            )
        
        else:
            return FileAnalysisResponse(
                success=False,
                filename=file.filename,
                error=f"Tipo de arquivo não suportado: {filename.split('.')[-1]}",
            )
            
    except Exception as e:
        logger.error(f"Error analyzing file {file.filename}: {e}")
        return FileAnalysisResponse(
            success=False,
            filename=file.filename or "unknown",
            error=str(e),
        )


def extract_keywords_from_text(text: str) -> list[str]:
    """Extract keywords from plain text using simple heuristics."""
    # Common tech keywords to look for
    tech_keywords = [
        'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
        'node', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'sql', 'postgresql',
        'mongodb', 'redis', 'kafka', 'spark', 'airflow', 'terraform', 'ci/cd',
        'machine learning', 'data science', 'devops', 'agile', 'scrum',
        'backend', 'frontend', 'fullstack', 'api', 'microservices',
    ]
    
    text_lower = text.lower()
    found = []
    
    for keyword in tech_keywords:
        if keyword in text_lower:
            found.append(keyword.title())
    
    return found[:15]
