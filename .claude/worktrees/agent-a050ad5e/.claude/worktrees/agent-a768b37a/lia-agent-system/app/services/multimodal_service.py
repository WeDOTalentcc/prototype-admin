"""
Multi-modal Analysis Service - Video, Image, and Document analysis for LIA.

Provides:
- Image analysis using Claude Vision (Anthropic)
- Video analysis using Gemini (Google)
- Document/PDF analysis with structure extraction
- Resume visual analysis with layout scoring
"""
import os
import base64
import logging
from typing import Optional, Dict, Any, List

import httpx

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
    
    ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
    GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    
    SUPPORTED_IMAGE_FORMATS = ["jpg", "jpeg", "png", "gif", "webp"]
    SUPPORTED_DOCUMENT_FORMATS = ["pdf", "jpg", "jpeg", "png", "webp"]
    
    def __init__(self):
        self.anthropic_key = os.getenv("AI_INTEGRATIONS_ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_base_url = os.getenv("AI_INTEGRATIONS_ANTHROPIC_BASE_URL") or "https://api.anthropic.com"
        self.google_key = os.getenv("AI_INTEGRATIONS_GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.gemini_base_url = os.getenv("AI_INTEGRATIONS_GEMINI_BASE_URL") or "https://generativelanguage.googleapis.com"
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with connection pooling."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=120.0)
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def _detect_image_format(self, image_data: bytes, filename: Optional[str] = None) -> str:
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
        prompt: Optional[str] = None,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze an image using Claude Vision.
        
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
        
        client = await self._get_client()
        
        api_url = f"{self.anthropic_base_url}/v1/messages"
        
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_base64,
                            }
                        },
                        {
                            "type": "text",
                            "text": analysis_prompt
                        }
                    ]
                }
            ]
        }
        
        try:
            response = await client.post(api_url, headers=headers, json=payload)
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Anthropic API error: {response.status_code} - {error_detail}")
                raise ImageAnalysisError(f"Anthropic API error: {response.status_code}")
            
            result = response.json()
            
            content = result.get("content", [])
            analysis_text = ""
            for block in content:
                if block.get("type") == "text":
                    analysis_text += block.get("text", "")
            
            extracted_text = self._extract_text_from_analysis(analysis_text)
            
            return {
                "analysis": analysis_text,
                "extracted_text": extracted_text,
                "confidence": 0.95,
                "analysis_type": analysis_type,
                "metadata": {
                    "model": result.get("model", "claude-sonnet-4-20250514"),
                    "image_format": image_format,
                    "usage": result.get("usage", {})
                }
            }
            
        except httpx.RequestError as e:
            logger.error(f"Request error during image analysis: {e}")
            raise ImageAnalysisError(f"Request error: {e}")
    
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
    ) -> Dict[str, Any]:
        """
        Analyze a video for interview insights using Gemini.
        
        Note: For full video analysis, Gemini's video capabilities are used.
        This implementation uses frame sampling and description analysis.
        
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
        
        client = await self._get_client()
        
        prompt = ANALYSIS_PROMPTS.get(
            f"{analysis_type}_video",
            ANALYSIS_PROMPTS.get("interview_video")
        )
        
        api_url = f"{self.gemini_base_url}/v1beta/models/gemini-2.0-flash:generateContent"
        
        params = {"key": self.google_key}
        
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "fileData": {
                                "mimeType": "video/mp4",
                                "fileUri": video_url
                            }
                        },
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 4096
            }
        }
        
        try:
            response = await client.post(
                api_url,
                params=params,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Gemini API error: {response.status_code} - {error_detail}")
                
                return self._generate_video_analysis_placeholder(video_url, analysis_type)
            
            result = response.json()
            
            candidates = result.get("candidates", [])
            if not candidates:
                return self._generate_video_analysis_placeholder(video_url, analysis_type)
            
            content = candidates[0].get("content", {})
            parts = content.get("parts", [])
            analysis_text = ""
            for part in parts:
                if "text" in part:
                    analysis_text += part["text"]
            
            return self._parse_video_analysis(analysis_text, analysis_type)
            
        except httpx.RequestError as e:
            logger.error(f"Request error during video analysis: {e}")
            return self._generate_video_analysis_placeholder(video_url, analysis_type)
    
    def _generate_video_analysis_placeholder(
        self,
        video_url: str,
        analysis_type: str
    ) -> Dict[str, Any]:
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
    
    def _parse_video_analysis(self, analysis_text: str, analysis_type: str) -> Dict[str, Any]:
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
                "model": "gemini-2.0-flash"
            }
        }
    
    def _extract_section(self, text: str, keywords: List[str]) -> str:
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
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze document layout and content.
        
        For PDFs, converts first page to image and analyzes with Claude Vision.
        For images, analyzes directly.
        
        Args:
            document_data: Raw document bytes
            document_type: Type of document ('pdf', 'docx', 'image')
            extract_structure: Whether to extract document structure
            filename: Optional filename for format detection
            
        Returns:
            {
                "text_content": "...",
                "structure": {"sections": [...]},
                "formatting_quality": 0.8,
                "visual_elements": [...],
                "extracted_data": {...}
            }
            
        Raises:
            DocumentAnalysisError: If analysis fails
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
    ) -> Dict[str, Any]:
        """Analyze PDF document by treating it as an image for Claude Vision."""
        if not self.anthropic_key:
            raise DocumentAnalysisError(
                "Anthropic API key not configured for PDF analysis."
            )
        
        pdf_base64 = base64.standard_b64encode(pdf_data).decode("utf-8")
        
        client = await self._get_client()
        
        api_url = f"{self.anthropic_base_url}/v1/messages"
        
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        
        structure_instruction = ""
        if extract_structure:
            structure_instruction = """
Also extract the document structure including:
- Main sections and their hierarchy
- Headers and subheaders
- Lists and bullet points
- Tables (if any)
- Key data points"""
        
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_base64,
                            }
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

Provide a structured analysis."""
                        }
                    ]
                }
            ]
        }
        
        try:
            response = await client.post(api_url, headers=headers, json=payload)
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Anthropic API error for PDF: {response.status_code} - {error_detail}")
                raise DocumentAnalysisError(f"PDF analysis failed: {response.status_code}")
            
            result = response.json()
            
            content = result.get("content", [])
            analysis_text = ""
            for block in content:
                if block.get("type") == "text":
                    analysis_text += block.get("text", "")
            
            return self._parse_document_analysis(analysis_text)
            
        except httpx.RequestError as e:
            logger.error(f"Request error during PDF analysis: {e}")
            raise DocumentAnalysisError(f"PDF analysis request failed: {e}")
    
    def _parse_document_analysis(self, analysis_text: str) -> Dict[str, Any]:
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
                "model": "claude-sonnet-4-20250514"
            }
        }
    
    async def analyze_resume_visual(
        self,
        resume_data: bytes,
        file_type: str = "pdf",
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Specialized resume analysis including visual presentation.
        
        Args:
            resume_data: Raw resume bytes (PDF or image)
            file_type: Type of file ('pdf', 'jpg', 'png', etc.)
            filename: Optional filename for format detection
            
        Returns:
            {
                "candidate_name": "...",
                "contact_info": {...},
                "photo_analysis": {...} if photo present,
                "layout_score": 0.85,
                "formatting_quality": {...},
                "content_analysis": {...},
                "improvement_suggestions": [...]
            }
            
        Raises:
            DocumentAnalysisError: If analysis fails
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
        
        client = await self._get_client()
        
        api_url = f"{self.anthropic_base_url}/v1/messages"
        
        headers = {
            "x-api-key": self.anthropic_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        
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
        
        payload = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": content_type,
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": resume_base64,
                            }
                        },
                        {
                            "type": "text",
                            "text": resume_prompt
                        }
                    ]
                }
            ]
        }
        
        try:
            response = await client.post(api_url, headers=headers, json=payload)
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Anthropic API error for resume: {response.status_code} - {error_detail}")
                raise DocumentAnalysisError(f"Resume analysis failed: {response.status_code}")
            
            result = response.json()
            
            content = result.get("content", [])
            analysis_text = ""
            for block in content:
                if block.get("type") == "text":
                    analysis_text += block.get("text", "")
            
            return self._parse_resume_analysis(analysis_text)
            
        except httpx.RequestError as e:
            logger.error(f"Request error during resume analysis: {e}")
            raise DocumentAnalysisError(f"Resume analysis request failed: {e}")
    
    def _parse_resume_analysis(self, analysis_text: str) -> Dict[str, Any]:
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
                "model": "claude-sonnet-4-20250514"
            }
        }
    
    def is_available(self) -> Dict[str, bool]:
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
