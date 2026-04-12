"""
Transcription Service — Transcribes audio/video recordings using Gemini API.

Supports:
- Audio files (mp3, wav, ogg, m4a, webm)
- Video files (mp4, webm, mov)
- URLs to remote files (downloaded first)
- Fallback: text extraction from pre-existing transcript fields

Cost: Gemini audio/video input pricing (much cheaper than dedicated STT).
"""
import asyncio
import ipaddress
import logging
import os
import socket
import tempfile
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

SUPPORTED_AUDIO_TYPES = {
    ".mp3": "audio/mp3",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".m4a": "audio/mp4",
    ".webm": "audio/webm",
    ".flac": "audio/flac",
}

SUPPORTED_VIDEO_TYPES = {
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
}

TRANSCRIPTION_PROMPT = """Transcreva o áudio/vídeo a seguir de forma completa e fiel.

REGRAS:
1. Transcreva TODO o conteúdo falado, sem resumir
2. Identifique os diferentes interlocutores quando possível (ex: "Entrevistador:", "Candidato:")
3. Mantenha o idioma original da fala
4. Inclua pausas significativas como [pausa]
5. Inclua marcadores de tempo aproximados a cada 2-3 minutos [HH:MM]
6. NÃO adicione interpretações ou análises — apenas a transcrição

Retorne APENAS a transcrição, sem comentários adicionais."""

LANGUAGE_DETECT_PROMPT = """Identifique o idioma principal desta transcrição.
Retorne APENAS o código BCP-47 (ex: pt-BR, en-US, es-ES). Nada mais."""


MAX_DOWNLOAD_SIZE = 500 * 1024 * 1024  # 500 MB
ALLOWED_URL_SCHEMES = {"https"}
BLOCKED_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "metadata.google.internal", "169.254.169.254"}


class TranscriptionService:
    def __init__(self):
        self._client = None

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in ALLOWED_URL_SCHEMES:
            raise ValueError(f"URL scheme '{parsed.scheme}' not allowed. Only HTTPS is accepted.")
        hostname = parsed.hostname or ""
        if not hostname:
            raise ValueError("Invalid URL: no hostname")
        if hostname in BLOCKED_HOSTS:
            raise ValueError(f"Blocked host: {hostname}")
        try:
            resolved = socket.getaddrinfo(hostname, None)
            for _, _, _, _, sockaddr in resolved:
                ip = ipaddress.ip_address(sockaddr[0])
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    raise ValueError(f"URL resolves to private/internal IP: {ip}")
        except socket.gaierror:
            raise ValueError(f"Cannot resolve hostname: {hostname}")

    def _get_client(self):
        if not self._client:
            # === Tenant-aware Gemini client (LGPD compliance) ===
            from app.shared.tenant_llm_context import get_gemini_client_for_tenant
            company_id = getattr(self, "_company_id", None)
            self._client = get_gemini_client_for_tenant(company_id)
        return self._client

    async def transcribe_from_url(
        self,
        recording_url: str,
        language_hint: str = "pt-BR",
        timeout_seconds: int = 120,
    ) -> dict[str, Any]:
        self._validate_url(recording_url)
        local_path = await self._download_file(recording_url)
        try:
            return await self.transcribe_from_file(
                local_path,
                language_hint=language_hint,
                timeout_seconds=timeout_seconds,
            )
        finally:
            try:
                os.unlink(local_path)
            except OSError:
                pass

    async def transcribe_from_file(
        self,
        file_path: str,
        language_hint: str = "pt-BR",
        timeout_seconds: int = 120,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        ext = os.path.splitext(file_path)[1].lower()
        mime = SUPPORTED_AUDIO_TYPES.get(ext) or SUPPORTED_VIDEO_TYPES.get(ext)
        if not mime:
            raise ValueError(
                f"Unsupported file type: {ext}. "
                f"Supported: {list(SUPPORTED_AUDIO_TYPES.keys()) + list(SUPPORTED_VIDEO_TYPES.keys())}"
            )

        client = self._get_client()

        uploaded_file = await asyncio.to_thread(
            client.files.upload,
            file=file_path,
        )
        logger.info("File uploaded to Gemini: %s (%s)", uploaded_file.name, mime)

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                transcript_text = await asyncio.wait_for(
                    self._generate_transcript(client, uploaded_file, language_hint),
                    timeout=timeout_seconds,
                )
                break
            except asyncio.TimeoutError:
                last_error = TimeoutError(f"Transcription timed out after {timeout_seconds}s")
                logger.warning("Transcription attempt %d/%d timed out", attempt, max_retries)
            except Exception as e:
                last_error = e
                logger.warning("Transcription attempt %d/%d failed: %s", attempt, max_retries, e)

            if attempt < max_retries:
                backoff = 2 ** attempt
                logger.info("Retrying transcription in %ds...", backoff)
                await asyncio.sleep(backoff)
        else:
            raise last_error  # type: ignore[misc]

        detected_language = await self._detect_language(client, transcript_text)

        word_count = len(transcript_text.split())
        estimated_duration = round(word_count / 150, 1)

        return {
            "transcript": transcript_text,
            "language": detected_language or language_hint,
            "source": "gemini",
            "word_count": word_count,
            "estimated_duration_minutes": estimated_duration,
            "transcribed_at": datetime.utcnow().isoformat(),
        }

    async def _generate_transcript(self, client, uploaded_file, language_hint: str) -> str:
        prompt = TRANSCRIPTION_PROMPT
        if language_hint and not language_hint.startswith("pt"):
            prompt += f"\n\nO idioma esperado é: {language_hint}"

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=[uploaded_file, prompt],
        )
        text = response.text or ""
        if not text.strip():
            raise ValueError("Gemini returned empty transcription")
        return text.strip()

    async def _detect_language(self, client, transcript_text: str) -> str | None:
        try:
            snippet = transcript_text[:500]
            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-2.5-flash",
                contents=[LANGUAGE_DETECT_PROMPT, snippet],
            )
            lang = (response.text or "").strip()
            if lang and len(lang) <= 10:
                return lang
        except Exception as e:
            logger.warning("Language detection failed: %s", e)
        return None

    async def _download_file(self, url: str) -> str:
        self._validate_url(url)

        async with httpx.AsyncClient(timeout=60.0, max_redirects=5) as http:
            head_resp = await http.head(url, follow_redirects=True)
            head_resp.raise_for_status()
            final_url = str(head_resp.url)
            if final_url != url:
                self._validate_url(final_url)

            async with http.stream("GET", final_url, follow_redirects=False) as response:
                response.raise_for_status()

                content_length = response.headers.get("content-length")
                if content_length and int(content_length) > MAX_DOWNLOAD_SIZE:
                    raise ValueError(f"File too large: {int(content_length)} bytes (max {MAX_DOWNLOAD_SIZE})")

                content_type = response.headers.get("content-type", "")
                ext = ".tmp"
                for e, m in {**SUPPORTED_AUDIO_TYPES, **SUPPORTED_VIDEO_TYPES}.items():
                    if m in content_type:
                        ext = e
                        break
                if ext == ".tmp":
                    parsed_path = urlparse(url).path
                    for e in list(SUPPORTED_AUDIO_TYPES.keys()) + list(SUPPORTED_VIDEO_TYPES.keys()):
                        if parsed_path.endswith(e):
                            ext = e
                            break

                fd, local_path = tempfile.mkstemp(suffix=ext)
                total_bytes = 0
                try:
                    with os.fdopen(fd, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=65536):
                            total_bytes += len(chunk)
                            if total_bytes > MAX_DOWNLOAD_SIZE:
                                raise ValueError(f"File too large during download (>{MAX_DOWNLOAD_SIZE} bytes)")
                            f.write(chunk)
                except Exception:
                    try:
                        os.unlink(local_path)
                    except OSError:
                        pass
                    raise

        logger.info("Downloaded recording: %s -> %s (%d bytes)", url, local_path, total_bytes)
        return local_path

    async def transcribe_and_persist(
        self,
        interview_id: str,
        recording_url: str,
        db: AsyncSession,
        language_hint: str = "pt-BR",
    ) -> dict[str, Any]:
        from sqlalchemy import select
        from app.models.interview import Interview

        stmt = select(Interview).where(Interview.id == interview_id)
        result = await db.execute(stmt)
        interview = result.scalar_one_or_none()
        if not interview:
            raise ValueError(f"Interview {interview_id} not found")

        interview.status = "transcribing"
        interview.recording_url = recording_url
        await db.flush()

        try:
            transcription = await self.transcribe_from_url(
                recording_url,
                language_hint=language_hint,
            )

            interview.transcript = transcription["transcript"]
            interview.transcript_language = transcription["language"]
            interview.transcript_source = transcription["source"]
            interview.transcribed_at = datetime.utcnow()
            interview.status = "transcribed"

            current_feedback = interview.feedback or {}
            current_feedback["transcript_text"] = transcription["transcript"]
            current_feedback["transcript_fetched_at"] = transcription["transcribed_at"]
            current_feedback["transcript_source"] = "gemini"
            current_feedback["word_count"] = transcription["word_count"]
            current_feedback["estimated_duration_minutes"] = transcription["estimated_duration_minutes"]
            interview.feedback = current_feedback

            await db.commit()

            await self._update_pipeline_metadata(db, interview, transcription)

            logger.info(
                "Transcription completed for interview %s: %d words, language=%s",
                interview_id,
                transcription["word_count"],
                transcription["language"],
            )
            return transcription

        except Exception as e:
            interview.status = "transcription_failed"
            current_feedback = interview.feedback or {}
            current_feedback["transcription_error"] = str(e)
            interview.feedback = current_feedback
            await db.commit()
            logger.error("Transcription failed for interview %s: %s", interview_id, e)
            raise


    @staticmethod
    async def _update_pipeline_metadata(
        db: AsyncSession,
        interview,
        transcription: dict[str, Any],
    ) -> None:
        if not interview.candidate_id or not interview.job_vacancy_id:
            logger.info(
                "Skipping pipeline update for interview %s: missing candidate_id or job_vacancy_id",
                interview.id,
            )
            return

        try:
            from sqlalchemy import select, update
            from libs.models.lia_models.candidate import VacancyCandidate

            stmt = select(VacancyCandidate).where(
                VacancyCandidate.candidate_id == interview.candidate_id,
                VacancyCandidate.vacancy_id == interview.job_vacancy_id,
            )
            result = await db.execute(stmt)
            vc = result.scalar_one_or_none()

            if not vc:
                logger.info(
                    "No VacancyCandidate found for candidate=%s vacancy=%s",
                    interview.candidate_id,
                    interview.job_vacancy_id,
                )
                return

            additional = vc.additional_data or {}
            additional["interview_transcript_available"] = True
            additional["interview_transcript_word_count"] = transcription.get("word_count", 0)
            additional["interview_transcript_language"] = transcription.get("language", "pt-BR")
            additional["interview_transcribed_at"] = transcription.get("transcribed_at")
            additional["interview_id"] = str(interview.id)
            vc.additional_data = additional

            await db.commit()

            logger.info(
                "Pipeline metadata updated for candidate=%s vacancy=%s",
                interview.candidate_id,
                interview.job_vacancy_id,
            )

        except Exception as e:
            logger.warning("Failed to update pipeline metadata: %s", e)


transcription_service = TranscriptionService()
