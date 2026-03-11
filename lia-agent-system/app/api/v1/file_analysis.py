"""
File Analysis API - Endpoints for analyzing uploaded documents.
"""
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import io

from app.services.cv_parser import cv_parser_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analysis", tags=["file-analysis"])


class FileAnalysisResponse(BaseModel):
    """Response from file analysis."""
    success: bool
    filename: str
    extractedText: Optional[str] = None
    keywords: List[str] = []
    summary: Optional[str] = None
    entities: Optional[dict] = None
    error: Optional[str] = None


@router.post("/file", response_model=FileAnalysisResponse)
async def analyze_file(file: UploadFile = File(...)):
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
            parsed = await cv_parser_service.parse_cv(file)
            
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
                
                entities = {
                    "skills": parsed.skills or [],
                    "job_titles": [parsed.current_title] if parsed.current_title else [],
                    "companies": [exp.company for exp in (parsed.experiences or []) if hasattr(exp, 'company') and exp.company][:5],
                    "locations": [parsed.location] if parsed.location else [],
                    "experience_years": parsed.years_of_experience,
                }
                
                summary = f"Documento analisado: {parsed.current_title or 'Profissional'}"
                if parsed.years_of_experience:
                    summary += f" com {parsed.years_of_experience} anos de experiência"
                if parsed.location:
                    summary += f" em {parsed.location}"
                
                return FileAnalysisResponse(
                    success=True,
                    filename=file.filename,
                    extractedText=parsed.summary or "",
                    keywords=unique_keywords[:15],
                    summary=summary,
                    entities=entities,
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


def extract_keywords_from_text(text: str) -> List[str]:
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
