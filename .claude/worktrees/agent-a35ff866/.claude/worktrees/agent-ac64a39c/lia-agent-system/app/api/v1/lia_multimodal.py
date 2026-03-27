"""
LIA Multimodal endpoints — extracted from lia_assistant.py (Sprint E).
Router is included by lia_assistant.router, so all routes resolve under /lia/multimodal/...
"""
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
import logging

from app.services.multimodal_service import (
    multimodal_service,
    MultimodalServiceError,
    ImageAnalysisError,
    VideoAnalysisError,
    DocumentAnalysisError,
)

logger = logging.getLogger(__name__)

multimodal_router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────────

class VideoAnalysisRequest(BaseModel):
    video_url: str
    analysis_type: str = "interview"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@multimodal_router.post("/multimodal/analyze-image")
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    analysis_type: str = Query("general", description="Type of analysis: general, resume, document, professional_photo"),
    prompt: Optional[str] = Query(None, description="Custom prompt for analysis")
) -> Dict:
    """Analyze an image using Claude Vision AI."""
    try:
        valid_types = ["general", "resume", "document", "professional_photo"]
        if analysis_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis_type. Must be one of: {', '.join(valid_types)}"
            )
        image_data = await file.read()
        if not image_data:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        result = await multimodal_service.analyze_image(
            image_data=image_data,
            analysis_type=analysis_type,
            prompt=prompt,
            filename=file.filename
        )
        return {"success": True, "analysis_type": analysis_type, "filename": file.filename, **result}
    except ImageAnalysisError as e:
        logger.error(f"Image analysis error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to analyze image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@multimodal_router.post("/multimodal/analyze-video")
async def analyze_video_endpoint(request: VideoAnalysisRequest) -> Dict:
    """Analyze a video for interview or presentation insights using Gemini."""
    try:
        valid_types = ["interview", "presentation", "general"]
        if request.analysis_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis_type. Must be one of: {', '.join(valid_types)}"
            )
        if not request.video_url:
            raise HTTPException(status_code=400, detail="video_url is required")
        result = await multimodal_service.analyze_video(
            video_url=request.video_url,
            analysis_type=request.analysis_type,
            extract_audio=True
        )
        return {"success": True, "analysis_type": request.analysis_type, "video_url": request.video_url, **result}
    except VideoAnalysisError as e:
        logger.error(f"Video analysis error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to analyze video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@multimodal_router.post("/multimodal/analyze-document")
async def analyze_document_endpoint(
    file: UploadFile = File(...),
    document_type: str = Query("auto", description="Document type: auto, pdf, image"),
    extract_structure: bool = Query(True, description="Extract document structure and sections")
) -> Dict:
    """Analyze a document for content and structure."""
    try:
        document_data = await file.read()
        if not document_data:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        result = await multimodal_service.analyze_document(
            document_data=document_data,
            document_type=document_type,
            extract_structure=extract_structure,
            filename=file.filename
        )
        return {"success": True, "document_type": document_type, "filename": file.filename, **result}
    except DocumentAnalysisError as e:
        logger.error(f"Document analysis error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to analyze document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@multimodal_router.post("/multimodal/analyze-resume")
async def analyze_resume_visual_endpoint(
    file: UploadFile = File(...),
    include_photo_analysis: bool = Query(True, description="Include analysis of candidate photo if present")
) -> Dict:
    """Specialized resume analysis with visual components."""
    try:
        resume_data = await file.read()
        if not resume_data:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        file_ext = ""
        if file.filename:
            file_ext = file.filename.lower().split(".")[-1]
        result = await multimodal_service.analyze_resume_visual(
            resume_data=resume_data,
            file_type=file_ext or "pdf",
            filename=file.filename
        )
        if not include_photo_analysis and "photo_analysis" in result:
            result["photo_analysis"] = {"included": False, "reason": "Excluded by request"}
        return {"success": True, "filename": file.filename, **result}
    except DocumentAnalysisError as e:
        logger.error(f"Resume analysis error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to analyze resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@multimodal_router.get("/multimodal/status")
async def get_multimodal_status() -> Dict:
    """Check which multimodal services are available."""
    try:
        availability = multimodal_service.is_available()
        services = []

        for svc_key, svc_name, provider, capabilities, missing_reason in [
            ("image_analysis_anthropic", "Image Analysis", "Anthropic Claude",
             ["general", "resume", "document", "professional_photo"], "ANTHROPIC_API_KEY not configured"),
            ("video_analysis_gemini", "Video Analysis", "Google Gemini",
             ["interview", "presentation", "general"], "GEMINI_API_KEY not configured"),
            ("document_analysis", "Document Analysis", "Anthropic Claude",
             ["pdf", "image", "structure_extraction"], "ANTHROPIC_API_KEY not configured"),
            ("resume_analysis", "Resume Visual Analysis", "Anthropic Claude",
             ["layout_scoring", "photo_analysis", "content_extraction", "suggestions"], "ANTHROPIC_API_KEY not configured"),
        ]:
            if availability.get(svc_key):
                services.append({"name": svc_name, "provider": provider, "status": "available", "capabilities": capabilities})
            else:
                services.append({"name": svc_name, "provider": provider, "status": "unavailable", "reason": missing_reason})

        all_available = all(s["status"] == "available" for s in services)
        any_available = any(s["status"] == "available" for s in services)
        return {
            "success": True,
            "overall_status": "fully_operational" if all_available else ("partial" if any_available else "unavailable"),
            "services": services,
            "availability_summary": availability
        }
    except Exception as e:
        logger.error(f"Failed to get multimodal status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
