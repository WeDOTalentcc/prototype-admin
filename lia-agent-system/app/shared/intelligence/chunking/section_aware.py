"""Section-aware chunking strategy for CVs and job descriptions."""

import re
import logging

from app.shared.intelligence.chunking.base import Chunk, ChunkingStrategy

logger = logging.getLogger(__name__)

SECTION_PATTERNS_PT = [
    r"(?:resumo\s*profissional|perfil\s*profissional|sobre\s*mim|objetivo)",
    r"(?:experi[eê]ncia\s*(?:profissional)?|histórico\s*profissional)",
    r"(?:forma[çc][aã]o\s*(?:acad[eê]mica)?|educa[çc][aã]o|escolaridade)",
    r"(?:habilidades|compet[eê]ncias|skills|conhecimentos)",
    r"(?:idiomas|l[íi]nguas)",
    r"(?:certifica[çc][oõ]es|cursos|treinamentos)",
    r"(?:projetos|portf[oó]lio)",
    r"(?:premia[çc][oõ]es|conquistas|realiza[çc][oõ]es)",
    r"(?:dados\s*pessoais|informa[çc][oõ]es\s*(?:pessoais|de\s*contato)|contato)",
    r"(?:refer[eê]ncias)",
    r"(?:atividades\s*extracurriculares|voluntariado|trabalho\s*volunt[aá]rio)",
    r"(?:publica[çc][oõ]es|artigos)",
]

SECTION_PATTERNS_EN = [
    r"(?:professional\s*summary|summary|profile|objective|about\s*me)",
    r"(?:(?:work\s*)?experience|employment\s*history|professional\s*experience)",
    r"(?:education|academic\s*(?:background|qualifications)|schooling)",
    r"(?:skills|competencies|technical\s*skills|core\s*competencies)",
    r"(?:languages)",
    r"(?:certifications|courses|training)",
    r"(?:projects|portfolio)",
    r"(?:awards|achievements|accomplishments)",
    r"(?:personal\s*(?:information|details)|contact(?:\s*information)?)",
    r"(?:references)",
    r"(?:extracurricular\s*activities|volunteer(?:ing)?)",
    r"(?:publications|papers)",
]

JD_SECTION_PATTERNS_PT = [
    r"(?:descri[çc][aã]o\s*(?:da\s*vaga)?|sobre\s*a\s*vaga)",
    r"(?:responsabilidades|atribui[çc][oõ]es|atividades)",
    r"(?:requisitos|qualifica[çc][oõ]es|pr[eé]-requisitos)",
    r"(?:benef[ií]cios|o\s*que\s*oferecemos)",
    r"(?:local\s*(?:de\s*trabalho)?|localiza[çc][aã]o)",
    r"(?:sobre\s*(?:a\s*empresa|n[oó]s)|quem\s*somos)",
    r"(?:remunera[çc][aã]o|sal[aá]rio|faixa\s*salarial)",
    r"(?:hor[aá]rio|jornada|regime)",
    r"(?:diferenciais|desej[aá]vel|desej[aá]veis)",
]

JD_SECTION_PATTERNS_EN = [
    r"(?:job\s*description|about\s*(?:the\s*)?(?:role|position))",
    r"(?:responsibilities|duties|key\s*responsibilities)",
    r"(?:requirements|qualifications|(?:must|nice)\s*(?:have|to\s*have))",
    r"(?:benefits|perks|what\s*we\s*offer)",
    r"(?:location|work\s*(?:location|arrangement))",
    r"(?:about\s*(?:us|the\s*company)|who\s*we\s*are|company\s*overview)",
    r"(?:compensation|salary(?:\s*range)?)",
    r"(?:schedule|working\s*hours)",
    r"(?:preferred|nice\s*to\s*have|bonus\s*(?:points|qualifications))",
]

_MAX_CHUNK_SIZE = 2000
_MIN_CHUNK_SIZE = 20


def _build_section_regex(patterns: list[str]) -> re.Pattern:
    combined = "|".join(patterns)
    return re.compile(
        rf"^[\s]*(?:#{1,4}\s*)?(?:{combined})[\s]*[:：\-–—]?[\s]*$",
        re.IGNORECASE | re.MULTILINE,
    )


class SectionAwareChunker(ChunkingStrategy):
    """Splits documents by detected section headers (CV / JD aware, PT + EN)."""

    def __init__(self, document_type: str = "cv", max_chunk_size: int = _MAX_CHUNK_SIZE, overlap: int = 100):
        self._document_type = document_type
        self._max_chunk_size = max_chunk_size
        self._overlap = overlap

        if document_type == "job_description":
            patterns = JD_SECTION_PATTERNS_PT + JD_SECTION_PATTERNS_EN
        else:
            patterns = SECTION_PATTERNS_PT + SECTION_PATTERNS_EN

        self._section_re = _build_section_regex(patterns)

    @property
    def strategy_name(self) -> str:
        return "section_aware"

    def _detect_sections(self, text: str) -> list[tuple[str, int, int]]:
        matches = list(self._section_re.finditer(text))
        if not matches:
            return []

        sections: list[tuple[str, int, int]] = []
        for i, m in enumerate(matches):
            header = m.group().strip().rstrip(":：-–—").strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sections.append((header, start, end))

        if matches[0].start() > 0:
            preamble_text = text[: matches[0].start()].strip()
            if preamble_text:
                sections.insert(0, ("preamble", 0, matches[0].start()))

        return sections

    def _split_large_section(self, section_text: str, base_idx: int) -> list[Chunk]:
        from app.shared.intelligence.chunking.sliding_window import SlidingWindowChunker
        fallback = SlidingWindowChunker(chunk_size=self._max_chunk_size, overlap=self._overlap)
        sub_chunks = fallback.chunk(section_text)
        for c in sub_chunks:
            c.index = base_idx + c.index
        return sub_chunks

    def chunk(self, text: str, **kwargs) -> list[Chunk]:
        if not text:
            return []

        sections = self._detect_sections(text)

        if not sections:
            logger.debug("[SectionAwareChunker] No sections detected, falling back to sliding_window")
            from app.shared.intelligence.chunking.sliding_window import SlidingWindowChunker
            fallback = SlidingWindowChunker()
            return fallback.chunk(text)

        chunks: list[Chunk] = []
        idx = 0

        for header, start, end in sections:
            section_text = text[start:end].strip()

            if header != "preamble":
                prefixed_text = f"{header}\n{section_text}" if section_text else header
            else:
                prefixed_text = section_text

            if not section_text or len(section_text) < _MIN_CHUNK_SIZE:
                if chunks and header != "preamble":
                    chunks[-1].text += f"\n\n{prefixed_text}"
                    chunks[-1].metadata["merged_sections"] = chunks[-1].metadata.get("merged_sections", []) + [header]
                elif section_text:
                    chunks.append(Chunk(
                        text=prefixed_text,
                        index=idx,
                        metadata={"strategy": "section_aware", "section": header},
                    ))
                    idx += 1
                continue

            if len(prefixed_text) > self._max_chunk_size:
                sub_chunks = self._split_large_section(prefixed_text, idx)
                for sc in sub_chunks:
                    sc.metadata["section"] = header
                    sc.metadata["strategy"] = "section_aware"
                chunks.extend(sub_chunks)
                idx += len(sub_chunks)
            else:
                chunks.append(Chunk(
                    text=prefixed_text,
                    index=idx,
                    metadata={"strategy": "section_aware", "section": header},
                ))
                idx += 1

        return chunks
