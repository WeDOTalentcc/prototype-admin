"""
Multi-modal Analysis Service - Video, Image, and Document analysis for LIA.

Provides:
- Image analysis using Claude Vision (Anthropic)
- Video analysis using Gemini (Google)
- Document/PDF analysis with structure extraction
- Resume visual analysis with layout scoring

P1.AIC2 (2026-05-22): migrated from raw httpx → Anthropic / Google GenAI SDKs.
The `app.shared.llm_bootstrap` monkey-patches both SDKs' message primitives so
the ai_credit_gate fires transitively here, closing the bypass identified by
the Wave 3 audit (~/Documents/wedotalent_audit_2026-05-21/audit_ai_credits_templates.md).
"""
import base64
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class MultimodalServiceError(Exception):
    """Base exception for multimodal service errors."""
    pass


class ImageAnalysisError(MultimodalServiceError):
    """Error during image analysis."""
    pass


class VideoAnalysisError(MultimodalServiceError):
    """Error during video analysis."""
    pass


class DocumentAnalysisError(MultimodalServiceError):
    """Error during document analysis."""
    pass


ANALYSIS_PROMPTS = {
    "general": """Analyze this image and provide a detailed description including:
1. Main subjects and objects visible
2. Colors, composition, and visual style
3. Any text visible in the image
4. Overall quality and clarity
5. Any notable details or observations

Provide your analysis in a structured format.""",

    "resume": """Analyze this resume image and extract:
1. Layout quality (1-10 score with reasoning)
2. Visual organization and readability
3. Use of whitespace and formatting
4. Font choices and consistency
5. Any visible sections (education, experience, skills, etc.)
6. Professional appearance assessment
7. Any visible photos and their professionalism

Provide structured feedback on the resume's visual presentation.""",

    "document": """Analyze this document image and extract:
1. Document type (letter, report, form, etc.)
2. Text content and structure
3. Sections and headings identified
4. Any logos, headers, or footers
5. Formatting quality and consistency
6. Key information extracted

Provide a structured analysis of the document.""",

    "professional_photo": """Analyze this professional photo and evaluate:
1. Photo quality (lighting, resolution, clarity)
2. Background appropriateness
3. Subject's appearance (professional attire, posture)
4. Facial expression and approachability
5. Overall professionalism score (1-10)
6. Recommendations for improvement if any

Provide honest, constructive feedback on the professional photo.""",

    "interview_video": """Analyze this interview video and evaluate:
1. Body language and posture
2. Eye contact and engagement
3. Speaking clarity and pace
4. Confidence level displayed
5. Professional appearance
6. Notable positive moments
7. Areas for improvement
8. Overall interview presence score (1-10)

Provide structured feedback on the candidate's interview performance.""",

    "presentation_video": """Analyze this presentation video and evaluate:
1. Speaker's presence and confidence
2. Presentation structure and flow
3. Use of visual aids (if visible)
4. Engagement and energy level
5. Speaking pace and clarity
6. Key points communicated
7. Overall presentation effectiveness (1-10)

Provide structured feedback on the presentation."""
}


class MultimodalService:
    """Service for multi-modal analysis - video, images, documents."""

    SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "gif", "webp"]
    SUPPORTED_DOCUMENT_FORMATS = ["pdf", "jpg", "jpeg", "png", "webp"]

    DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
    DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"

    def __init__(self):
        self.anthropic_key = os.getenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.google_key = os.getenv("AI_INTEGRATIONS_GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        # SDK clients are lazily constructed on first use so the bootstrap
        # monkey-patches have a chance to install before instantiation.
        self._anthropic_client = None
        self._genai_client = None

    async def _get_anthropic_client(self):
        """Lazy-build Anthropic client via canonical factory (W3-027)."""
        if self._anthropic_client is None:
            from app.shared.providers.llm_factory import get_provider_for_tenant
            from app.shared.providers.llm_provider import LLMProviderABC
            container = get_provider_for_tenant(primary_provider="claude")
            self._anthropic_client = container.get("claude")
        return self._anthropic_client

    async def _get_genai_client(self):
        """Lazy-build Gemini client via canonical factory (W3-027)."""
        if self._genai_client is None:
            from app.shared.providers.llm_factory import get_provider_for_tenant
            container = get_provider_for_tenant(primary_provider="gemini")
            self._genai_client = container.get("gemini")
        return self._genai_client

    async def close(self):
        """Compatibility shim — SDK clients manage their own pools."""
        self._anthropic_client = None
        self._genai_client = None

    def _detect_image_format(self, image_data: bytes, filename: str | None = None) -> str:
        """Detect image format from file header or filename."""
        if filename:
            ext = filename.lower().split(".")[-1]
            if ext in self.SUPPORTED_IMAGE_FORMATS:
                return ext

        if image_data[:8] == b'\x89PNG\r\n\x1a\n':
            return "png"
        if image_data[:2] == b'\xff\xd8':
            return "jpeg"
        if image_data[:6] in (b'GIF87a', b'GIF89a'):
            return "gif"
        if image_data[:4] == b'RIFF' and image_data[8:12] == b'WEBP':
            return "webp"
        if image_data[:4] == b'%PDF':
            return "pdf"

        return "jpeg"

    def _get_media_type(self, format: str) -> str:
        """Get MIME type for image format."""
        media_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
            "pdf": "application/pdf"
        }
        return media_types.get(format, "image/jpeg")

    async def analyze_image(
        self,
        image_data: bytes,
        analysis_type: str = "general",
        prompt: str | None = None,
        filename: str | None = None
    ) -> dict[str, Any]:
        """
        Analyze an image using Claude Vision via Anthropic SDK.

        P1.AIC2: gate transitive via llm_bootstrap monkey-patch on
        AsyncAnthropic.messages.create.

        Args:
            image_data: Raw image bytes
            analysis_type: Type of analysis ('general', 'resume', 'document', 'professional_photo')
            prompt: Custom prompt to use (overrides analysis_type prompt)
            filename: Optional filename for format detection

        Returns:
            {
                "analysis": "detailed analysis text",
                "extracted_text": "any text found",
                "confidence": 0.95,
                "metadata": {...}
            }

        Raises:
            ImageAnalysisError: If analysis fails
        """
        if not image_data:
            raise ImageAnalysisError("No image data provided")

        if not self.anthropic_key:
            raise ImageAnalysisError(
                "Anthropic API key not configured. Please set AI_INTEGRATIONS_ANTHROPIC_API_KEY or ANTHROPIC_API_KEY."
            )

        image_format = self._detect_image_format(image_data, filename)
        if image_format not in self.SUPPORTED_IMAGE_FORMATS:
            raise ImageAnalysisError(f"Unsupported image format: {image_format}")

        media_type = self._get_media_type(image_format)
        image_base64 = base64.standard_b64encode(image_data).decode("utf-8")

        analysis_prompt = prompt or ANALYSIS_PROMPTS.get(analysis_type, ANALYSIS_PROMPTS["general"])

        client = await self._get_anthropic_client()

        # Defense-in-depth: inline credit gate (see voice_service helpers).
        await _credit_gate_multimodal_text("vision_image", analysis_prompt)

        try:
            response = await client.messages.create(
                model=self.DEFAULT_ANTHROPIC_MODEL,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": analysis_prompt,
                            },
                        ],
                    }
                ],
            )

            analysis_text = ""
            for block in response.content or []:
                # Anthropic SDK returns typed blocks; text block has .text
                if getattr(block, "type", None) == "text":
                    analysis_text += getattr(block, "text", "") or ""

            extracted_text = self._extract_text_from_analysis(analysis_text)

            usage = {}
            if getattr(response, "usage", None) is not None:
                try:
                    usage = response.usage.model_dump()  # type: ignore[attr-defined]
                except Exception:
                    usage = {
                        "input_tokens": getattr(response.usage, "input_tokens", None),
                        "output_tokens": getattr(response.usage, "output_tokens", None),
                    }

            return {
                "analysis": analysis_text,
                "extracted_text": extracted_text,
                "confidence": 0.95,
                "analysis_type": analysis_type,
                "metadata": {
                    "model": getattr(response, "model", self.DEFAULT_ANTHROPIC_MODEL),
                    "image_format": image_format,
                    "usage": usage,
                },
            }

        except ImageAnalysisError:
            raise
        except Exception as e:
            # AICreditExhausted (from bootstrap gate) bubbles up before reaching here
            # when caller hasn't caught it explicitly; we re-raise unchanged.
            from app.shared.services.ai_credit_gate import AICreditExhausted
            if isinstance(e, AICreditExhausted):
                raise
            logger.error(f"Image analysis error: {e}")
            raise ImageAnalysisError(f"Image analysis failed: {e}")

    def _extract_text_from_analysis(self, analysis: str) -> str:
        """Extract any quoted or identified text from the analysis."""
        import re

        quoted_texts = re.findall(r'"([^"]+)"', analysis)

        text_markers = ["text visible:", "text found:", "text content:", "reads:"]
        for marker in text_markers:
            if marker in analysis.lower():
                idx = analysis.lower().find(marker)
                end_idx = analysis.find("\n", idx + len(marker))
                if end_idx == -1:
                    end_idx = len(analysis)
                extracted = analysis[idx + len(marker):end_idx].strip()
                if extracted:
                    return extracted

        return " | ".join(quoted_texts[:5]) if quoted_texts else ""

    async def analyze_video(
        self,
        video_url: str,
        analysis_type: str = "interview",
        extract_audio: bool = True
    ) -> dict[str, Any]:
        """
        Analyze a video for interview insights using Gemini via google.genai SDK.

        P1.AIC2: gate transitive via llm_bootstrap monkey-patch on
        genai.Client.aio.models.generate_content.

        Args:
            video_url: URL of the video to analyze
            analysis_type: Type of analysis ('interview', 'presentation', 'general')
            extract_audio: Whether to analyze audio/speech (placeholder)

        Returns:
            {
                "duration_seconds": 120,
                "key_moments": [...],
                "body_language_analysis": {...},
                "speech_patterns": {...},
                "transcript": "...",
                "overall_assessment": "..."
            }

        Raises:
            VideoAnalysisError: If analysis fails
        """
        if not video_url:
            raise VideoAnalysisError("No video URL provided")

        if not self.google_key:
            raise VideoAnalysisError(
                "Google API key not configured. Please set AI_INTEGRATIONS_GEMINI_API_KEY or GOOGLE_API_KEY."
            )

        prompt = ANALYSIS_PROMPTS.get(
            f"{analysis_type}_video",
            ANALYSIS_PROMPTS.get("interview_video"),
        )

        try:
            from google.genai import types as genai_types  # W3-027-EXEMPT: google.genai.types for type building only — client via _get_genai_client()
        except ImportError:
            logger.error("google-genai not installed; cannot run video analysis")
            return self._generate_video_analysis_placeholder(video_url, analysis_type)

        client = await self._get_genai_client()

        # Defense-in-depth: inline credit gate for Gemini video analysis.
        await _credit_gate_multimodal_text("vision_video", prompt)

        try:
            response = await client.aio.models.generate_content(
                model=self.DEFAULT_GEMINI_MODEL,
                contents=[
                    genai_types.Part.from_uri(file_uri=video_url, mime_type="video/mp4"),
                    prompt,
                ],
                config=genai_types.GenerateContentConfig(
                    temperature=0.4,
                    max_output_tokens=4096,
                ),
            )

            analysis_text = (getattr(response, "text", None) or "").strip()
            if not analysis_text:
                return self._generate_video_analysis_placeholder(video_url, analysis_type)

            return self._parse_video_analysis(analysis_text, analysis_type)

        except Exception as e:
            # AICreditExhausted bubbles up unchanged.
            from app.shared.services.ai_credit_gate import AICreditExhausted
            if isinstance(e, AICreditExhausted):
                raise
            logger.error(f"Video analysis error: {e}")
            return self._generate_video_analysis_placeholder(video_url, analysis_type)

    def _generate_video_analysis_placeholder(
        self,
        video_url: str,
        analysis_type: str
    ) -> dict[str, Any]:
        """Generate a placeholder response when video analysis fails."""
        return {
            "duration_seconds": None,
            "key_moments": [],
            "body_language_analysis": {
                "status": "unavailable",
                "message": "Video analysis requires direct video file access. Please ensure the video URL is accessible."
            },
            "speech_patterns": {
                "status": "unavailable",
                "message": "Audio transcription not available for this video."
            },
            "transcript": "",
            "overall_assessment": f"Video analysis for '{analysis_type}' could not be completed. The video URL may not be directly accessible or the format is not supported.",
            "analysis_type": analysis_type,
            "video_url": video_url,
            "error": "Video could not be analyzed. For best results, use a publicly accessible video URL."
        }

    def _parse_video_analysis(self, analysis_text: str, analysis_type: str) -> dict[str, Any]:
        """Parse video analysis text into structured format."""
        return {
            "duration_seconds": None,
            "key_moments": [],
            "body_language_analysis": {
                "summary": self._extract_section(analysis_text, ["body language", "posture", "gestures"]),
                "details": {}
            },
            "speech_patterns": {
                "summary": self._extract_section(analysis_text, ["speaking", "speech", "voice", "clarity"]),
                "details": {}
            },
            "transcript": "",
            "overall_assessment": analysis_text,
            "analysis_type": analysis_type,
            "confidence": 0.85,
            "metadata": {
                "model": self.DEFAULT_GEMINI_MODEL,
            }
        }

    def _extract_section(self, text: str, keywords: list[str]) -> str:
        """Extract relevant section from analysis text based on keywords."""
        lines = text.split("\n")
        relevant_lines = []
        capturing = False

        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords):
                capturing = True
                relevant_lines.append(line)
            elif capturing and line.strip():
                if line.startswith(("1.", "2.", "-", "*", "•")):
                    relevant_lines.append(line)
                elif any(marker in line_lower for marker in ["score", "overall", "summary"]):
                    relevant_lines.append(line)
                    capturing = False

        return "\n".join(relevant_lines[:10]) if relevant_lines else ""

    async def analyze_document(
        self,
        document_data: bytes,
        document_type: str = "pdf",
        extract_structure: bool = True,
        filename: str | None = None
    ) -> dict[str, Any]:
        """
        Analyze document layout and content.

        For PDFs, sends to Claude as a `document` block. For images, analyzes
        directly via `analyze_image`.

        P1.AIC2: gate transitive via Anthropic SDK monkey-patch.
        """
        if not document_data:
            raise DocumentAnalysisError("No document data provided")

        detected_format = self._detect_image_format(document_data, filename)

        if detected_format == "pdf":
            return await self._analyze_pdf_document(document_data, extract_structure)
        elif detected_format in self.SUPPORTED_IMAGE_FORMATS:
            image_analysis = await self.analyze_image(
                document_data,
                analysis_type="document",
                filename=filename
            )

            return {
                "text_content": image_analysis.get("extracted_text", ""),
                "structure": {
                    "sections": [],
                    "format": detected_format
                },
                "formatting_quality": 0.8,
                "visual_elements": [],
                "extracted_data": {},
                "analysis": image_analysis.get("analysis", ""),
                "confidence": image_analysis.get("confidence", 0.85)
            }
        else:
            raise DocumentAnalysisError(f"Unsupported document format: {detected_format}")

    async def _analyze_pdf_document(
        self,
        pdf_data: bytes,
        extract_structure: bool
    ) -> dict[str, Any]:
        """Analyze PDF document via Claude Vision (document block)."""
        if not self.anthropic_key:
            raise DocumentAnalysisError(
                "Anthropic API key not configured for PDF analysis."
            )

        pdf_base64 = base64.standard_b64encode(pdf_data).decode("utf-8")

        structure_instruction = ""
        if extract_structure:
            structure_instruction = """
Also extract the document structure including:
- Main sections and their hierarchy
- Headers and subheaders
- Lists and bullet points
- Tables (if any)
- Key data points"""

        client = await self._get_anthropic_client()

        # Defense-in-depth: inline credit gate.
        await _credit_gate_multimodal_text("vision_pdf", structure_instruction or "pdf")

        try:
            response = await client.messages.create(
                model=self.DEFAULT_ANTHROPIC_MODEL,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": pdf_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": f"""Analyze this PDF document and extract:
1. All text content in reading order
2. Document type and purpose
3. Formatting quality assessment (1-10)
4. Visual elements (logos, images, charts)
5. Key information and data points
{structure_instruction}

Provide a structured analysis.""",
                            },
                        ],
                    }
                ],
            )

            analysis_text = ""
            for block in response.content or []:
                if getattr(block, "type", None) == "text":
                    analysis_text += getattr(block, "text", "") or ""

            return self._parse_document_analysis(analysis_text)

        except DocumentAnalysisError:
            raise
        except Exception as e:
            from app.shared.services.ai_credit_gate import AICreditExhausted
            if isinstance(e, AICreditExhausted):
                raise
            logger.error(f"PDF analysis error: {e}")
            raise DocumentAnalysisError(f"PDF analysis failed: {e}")

    def _parse_document_analysis(self, analysis_text: str) -> dict[str, Any]:
        """Parse document analysis into structured format."""
        import re

        quality_match = re.search(r'(?:quality|score)[:\s]*(\d+)(?:/10)?', analysis_text.lower())
        formatting_quality = float(quality_match.group(1)) / 10 if quality_match else 0.7

        sections = []
        section_markers = re.findall(r'^(?:#{1,3}|[0-9]+\.|\*\*)[^\n]+', analysis_text, re.MULTILINE)
        for marker in section_markers[:10]:
            sections.append(marker.strip("# *").strip())

        return {
            "text_content": analysis_text,
            "structure": {
                "sections": sections,
                "has_hierarchy": len(sections) > 0
            },
            "formatting_quality": formatting_quality,
            "visual_elements": [],
            "extracted_data": {},
            "confidence": 0.85,
            "metadata": {
                "model": self.DEFAULT_ANTHROPIC_MODEL,
            }
        }

    async def analyze_resume_visual(
        self,
        resume_data: bytes,
        file_type: str = "pdf",
        filename: str | None = None
    ) -> dict[str, Any]:
        """
        Specialized resume analysis including visual presentation.

        P1.AIC2: gate transitive via Anthropic SDK monkey-patch.
        """
        if not resume_data:
            raise DocumentAnalysisError("No resume data provided")

        if not self.anthropic_key:
            raise DocumentAnalysisError(
                "Anthropic API key not configured for resume analysis."
            )

        detected_format = self._detect_image_format(resume_data, filename)

        if detected_format == "pdf":
            resume_base64 = base64.standard_b64encode(resume_data).decode("utf-8")
            media_type = "application/pdf"
            content_type = "document"
        elif detected_format in self.SUPPORTED_IMAGE_FORMATS:
            resume_base64 = base64.standard_b64encode(resume_data).decode("utf-8")
            media_type = self._get_media_type(detected_format)
            content_type = "image"
        else:
            raise DocumentAnalysisError(f"Unsupported resume format: {detected_format}")

        resume_prompt = """Analyze this resume thoroughly and extract:

1. **Candidate Information**:
   - Full name
   - Contact information (email, phone, location if visible)
   - LinkedIn or other professional profiles if visible

2. **Photo Analysis** (if a photo is present):
   - Photo quality and professionalism
   - Appropriate for professional use (yes/no with reasoning)
   - Recommendations for improvement

3. **Layout Assessment** (score 1-10):
   - Visual organization and hierarchy
   - Use of whitespace and margins
   - Section clarity and flow
   - Overall readability

4. **Formatting Quality**:
   - Font choices and consistency
   - Use of bold, italics, bullets appropriately
   - Date and information formatting
   - Overall professional appearance

5. **Content Structure**:
   - Sections identified (education, experience, skills, etc.)
   - Information completeness
   - Relevant keywords and skills visible

6. **Improvement Suggestions**:
   - Top 3-5 actionable recommendations
   - Priority areas to address

Provide your analysis in a structured format with clear sections."""

        client = await self._get_anthropic_client()

        # Defense-in-depth: inline credit gate for resume vision.
        await _credit_gate_multimodal_text("vision_resume", resume_prompt)

        try:
            response = await client.messages.create(
                model=self.DEFAULT_ANTHROPIC_MODEL,
                max_tokens=4096,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": content_type,
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": resume_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": resume_prompt,
                            },
                        ],
                    }
                ],
            )

            analysis_text = ""
            for block in response.content or []:
                if getattr(block, "type", None) == "text":
                    analysis_text += getattr(block, "text", "") or ""

            return self._parse_resume_analysis(analysis_text)

        except DocumentAnalysisError:
            raise
        except Exception as e:
            from app.shared.services.ai_credit_gate import AICreditExhausted
            if isinstance(e, AICreditExhausted):
                raise
            logger.error(f"Resume analysis error: {e}")
            raise DocumentAnalysisError(f"Resume analysis failed: {e}")

    def _parse_resume_analysis(self, analysis_text: str) -> dict[str, Any]:
        """Parse resume analysis into structured format."""
        import re

        name_match = re.search(r'(?:name|candidat[eo])[:\s]*([A-Z][a-zA-Z\s]+?)(?:\n|,|$)', analysis_text, re.IGNORECASE)
        candidate_name = name_match.group(1).strip() if name_match else None

        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', analysis_text)
        phone_match = re.search(r'[\+]?[\d\s\(\)\-]{10,}', analysis_text)

        contact_info = {}
        if email_match:
            contact_info["email"] = email_match.group(0)
        if phone_match:
            contact_info["phone"] = phone_match.group(0).strip()

        layout_match = re.search(r'layout[^0-9]*(\d+)(?:/10)?', analysis_text.lower())
        layout_score = float(layout_match.group(1)) / 10 if layout_match else 0.7

        has_photo = any(phrase in analysis_text.lower() for phrase in [
            "photo", "photograph", "headshot", "picture", "image of candidate"
        ])

        photo_analysis = None
        if has_photo:
            photo_section = self._extract_section(analysis_text, ["photo", "photograph", "headshot"])
            photo_analysis = {
                "present": True,
                "analysis": photo_section or "Photo detected in resume",
                "professional": "professional" in photo_section.lower() if photo_section else None
            }

        suggestions = []
        suggestion_patterns = [
            r'(?:recommend|suggest|improve|consider)[:\s]*([^\n]+)',
            r'(?:\d+\.|\-|\*)\s*([^\n]+(?:improve|recommend|suggest|should|could)[^\n]*)',
        ]
        for pattern in suggestion_patterns:
            matches = re.findall(pattern, analysis_text, re.IGNORECASE)
            suggestions.extend(m.strip() for m in matches[:5])

        return {
            "candidate_name": candidate_name,
            "contact_info": contact_info,
            "photo_analysis": photo_analysis,
            "layout_score": layout_score,
            "formatting_quality": {
                "score": layout_score,
                "details": self._extract_section(analysis_text, ["formatting", "font", "style"])
            },
            "content_analysis": {
                "full_analysis": analysis_text,
                "sections_found": self._extract_section(analysis_text, ["section", "education", "experience", "skills"])
            },
            "improvement_suggestions": suggestions[:5],
            "confidence": 0.85,
            "metadata": {
                "model": self.DEFAULT_ANTHROPIC_MODEL,
            }
        }

    def is_available(self) -> dict[str, bool]:
        """Check which multimodal services are available."""
        return {
            "image_analysis_anthropic": bool(self.anthropic_key),
            "video_analysis_gemini": bool(self.google_key),
            "document_analysis": bool(self.anthropic_key),
            "resume_analysis": bool(self.anthropic_key),
            "any_image": bool(self.anthropic_key),
            "any_video": bool(self.google_key),
            "any_document": bool(self.anthropic_key)
        }


multimodal_service = MultimodalService()


# ----------------------------------------------------------------------
# Inline credit-gate helper (P1.AIC2 defense-in-depth, 2026-05-22)
# ----------------------------------------------------------------------
# Mirrors `_estimate_tokens_anthropic` in `llm_bootstrap.py` for inline use
# so mocked-SDK contract tests exercise the same ledger.

async def _credit_gate_multimodal_text(service_label: str, prompt: str) -> None:
    """Project a vision/document budget hit and call check_credit_budget.

    AICreditExhausted bubbles up unchanged. Other errors fail-safe ALLOW.
    """
    from app.middleware.auth_enforcement import _current_company_id
    from app.shared.services.ai_credit_gate import (
        AICreditExhausted,
        check_credit_budget,
    )

    company_id = _current_company_id.get("")
    if not company_id:
        return

    # ~4 chars per token + max_tokens budget (matches _estimate_tokens_anthropic)
    estimated_tokens = (len(prompt or "") // 4) + 4096

    try:
        from lia_config.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            await check_credit_budget(
                db,
                company_id,
                estimated_tokens=estimated_tokens,
                service=service_label,
            )
    except AICreditExhausted:
        raise
    except Exception as exc:
        logger.warning(
            "[MultimodalService] inline %s credit gate fail-safe ALLOW: %s",
            service_label, exc,
        )
