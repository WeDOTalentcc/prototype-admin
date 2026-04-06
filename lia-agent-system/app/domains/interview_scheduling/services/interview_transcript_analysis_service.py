"""
Interview Transcript Analysis Service - Análise de transcrições de entrevistas com WSI determinístico.

Usa metodologia WSI com cálculo determinístico para:
1. Identificar competências demonstradas
2. Calcular scores por framework (CBI, Bloom, Dreyfus, Big Five)
3. Gerar parecer estruturado

Custo de transcrição Teams: $0 (incluído no Microsoft 365)
"""
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS E CONSTANTES
# ============================================================================

class BloomLevel(Enum):
    """Níveis da Taxonomia de Bloom (Revisada)."""
    REMEMBER = 1      # Lembrar - recall facts
    UNDERSTAND = 2    # Compreender - explain ideas
    APPLY = 3         # Aplicar - use in new situations
    ANALYZE = 4       # Analisar - draw connections
    EVALUATE = 5      # Avaliar - justify decisions
    CREATE = 6        # Criar - produce new work


class DreyfusStage(Enum):
    """Estágios do Modelo Dreyfus de aquisição de habilidades."""
    NOVICE = 1        # Seguidor de regras rígidas
    ADVANCED_BEGINNER = 2  # Reconhece situações
    COMPETENT = 3     # Planeja e prioriza
    PROFICIENT = 4    # Vê o quadro geral
    EXPERT = 5        # Age intuitivamente


class BigFiveTrait(Enum):
    """Traços do Big Five (OCEAN)."""
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"


# ============================================================================
# INDICADORES LINGUÍSTICOS (DETERMINÍSTICOS)
# ============================================================================

BLOOM_INDICATORS = {
    BloomLevel.REMEMBER: [
        "eu sei", "eu lembro", "aprendi", "conheço", "me lembro",
        "estudei", "li sobre", "ouvi falar", "básico", "fundamental",
        "decorei", "memorizei", "recordo", "tenho conhecimento"
    ],
    BloomLevel.UNDERSTAND: [
        "eu entendo", "compreendo", "significa", "porque", "então",
        "ou seja", "basicamente", "na prática", "explicando",
        "em outras palavras", "quer dizer", "o conceito é", "funciona assim"
    ],
    BloomLevel.APPLY: [
        "eu uso", "utilizo", "aplico", "implementei", "fiz",
        "trabalhei com", "desenvolvi", "executei", "resolvi",
        "coloquei em prática", "usei na prática", "apliquei isso"
    ],
    BloomLevel.ANALYZE: [
        "eu analiso", "comparando", "diferença entre", "por outro lado",
        "depende de", "considerando", "avaliando", "investigando",
        "analisando os dados", "quebrando em partes", "identificando padrões"
    ],
    BloomLevel.EVALUATE: [
        "eu avalio", "julgo", "prefiro", "melhor porque", "optei por",
        "recomendo", "critico", "justifiquei", "defendi",
        "na minha opinião", "avaliando criticamente", "a melhor abordagem"
    ],
    BloomLevel.CREATE: [
        "eu criei", "desenvolvi novo", "inovei", "propus", "arquitetei",
        "desenhei", "inventei", "fundei", "liderei a criação",
        "desenvolvi do zero", "criei uma solução", "minha criação"
    ]
}

DREYFUS_INDICATORS = {
    DreyfusStage.NOVICE: [
        "seguindo o manual", "como aprendi", "receita", "passo a passo",
        "não sei se", "perguntei", "me ensinaram", "seguindo instruções",
        "conforme o tutorial", "como me falaram", "ainda estou aprendendo"
    ],
    DreyfusStage.ADVANCED_BEGINNER: [
        "já vi isso antes", "parecido com", "reconheci", "similar a",
        "naquele projeto", "aquela vez", "me lembra de",
        "já passei por isso", "experiência anterior"
    ],
    DreyfusStage.COMPETENT: [
        "planejei", "priorizei", "organizei", "gerenciei", "coordenei",
        "estabeleci prioridades", "fiz o plano", "montei a estratégia",
        "defini os passos", "estruturei o projeto"
    ],
    DreyfusStage.PROFICIENT: [
        "olhando o todo", "visão geral", "impacto em", "consequências",
        "a longo prazo", "estrategicamente", "sistemicamente",
        "considerando o contexto", "entendendo o cenário completo"
    ],
    DreyfusStage.EXPERT: [
        "intuitivamente", "naturalmente", "simplesmente sei", "senti que",
        "experiência me diz", "já esperava", "previa que",
        "minha intuição", "sem precisar pensar", "automaticamente"
    ]
}

BIG_FIVE_INDICATORS = {
    BigFiveTrait.OPENNESS: {
        "high": [
            "curioso", "criativo", "inovador", "experimentar", "novo", 
            "diferente", "explorar", "alternativas", "fora da caixa",
            "novas ideias", "aberto a", "interessante"
        ],
        "low": [
            "tradicional", "convencional", "padrão", "rotina", 
            "estabelecido", "conservador", "familiar", "usual"
        ]
    },
    BigFiveTrait.CONSCIENTIOUSNESS: {
        "high": [
            "organizado", "planejado", "metódico", "cuidadoso", 
            "deadline", "meta", "objetivo", "responsável",
            "disciplinado", "pontual", "detalhista", "comprometido"
        ],
        "low": [
            "flexível", "adaptável", "espontâneo", "improvisado",
            "informal", "relaxado"
        ]
    },
    BigFiveTrait.EXTRAVERSION: {
        "high": [
            "equipe", "colaboração", "comunicação", "apresentação", 
            "networking", "pessoas", "reunião", "interação",
            "grupo", "social", "conversar", "compartilhar"
        ],
        "low": [
            "sozinho", "independente", "concentrado", "silêncio", 
            "foco", "individual", "reservado", "quieto"
        ]
    },
    BigFiveTrait.AGREEABLENESS: {
        "high": [
            "ajudar", "colaborar", "apoiar", "consenso", "harmonia", 
            "empatia", "compreensão", "cooperar", "gentil",
            "solidário", "acolhedor", "paciente"
        ],
        "low": [
            "desafiar", "questionar", "debater", "confrontar", 
            "competir", "crítico", "direto", "assertivo"
        ]
    },
    BigFiveTrait.NEUROTICISM: {
        "high": [
            "preocupado", "estressado", "ansioso", "nervoso", 
            "tensão", "pressão", "difícil", "desafiador",
            "angústia", "inseguro"
        ],
        "low": [
            "calmo", "tranquilo", "equilibrado", "relaxado", 
            "controlado", "sereno", "confiante", "estável",
            "seguro", "firme"
        ]
    }
}

CBI_STAR_INDICATORS = {
    "situation": [
        "quando", "uma vez", "no projeto", "na empresa", 
        "naquela situação", "contexto", "cenário", "momento",
        "aconteceu", "havia", "estávamos", "enfrentávamos"
    ],
    "task": [
        "minha tarefa", "meu objetivo", "eu precisava", 
        "responsabilidade", "missão", "meu papel", "minha função",
        "deveria", "tinha que", "era necessário", "esperavam que eu"
    ],
    "action": [
        "eu fiz", "tomei", "decidi", "implementei", "liderei", 
        "executei", "realizei", "desenvolvi", "criei", "organizei",
        "conversei", "propus", "apresentei", "negociei"
    ],
    "result": [
        "resultado foi", "consegui", "alcançamos", "entregamos", 
        "melhorou", "reduziu", "aumentou", "impacto foi",
        "obtivemos", "atingimos", "conquistamos", "finalizamos"
    ]
}

RED_FLAG_INDICATORS = [
    "nunca fiz", "não tenho experiência", "não sei", "não conheço",
    "é muito difícil", "impossível", "não gosto", "odeio",
    "conflito com", "briguei com", "discuti com", "problema com chefe",
    "fui demitido", "me mandaram embora", "saí por problemas",
    "mentira", "inventei", "exagerei", "não era bem assim"
]

STRENGTH_INDICATORS = [
    "consegui entregar", "superei expectativas", "recebi elogios",
    "fui promovido", "reconhecimento", "prêmio", "destaque",
    "melhor resultado", "referência", "especialista em",
    "certificação", "publicação", "palestrante"
]


# ============================================================================
# MODELOS DE DADOS
# ============================================================================

@dataclass
class CompetencyEvidence:
    """Evidência de competência identificada na transcrição."""
    competency_name: str
    category: str  # technical, behavioral, cultural
    evidence_text: str
    timestamp: str | None = None
    bloom_level: int | None = None
    dreyfus_stage: int | None = None
    cbi_components: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "competency_name": self.competency_name,
            "category": self.category,
            "evidence_text": self.evidence_text,
            "timestamp": self.timestamp,
            "bloom_level": self.bloom_level,
            "dreyfus_stage": self.dreyfus_stage,
            "cbi_components": self.cbi_components,
            "confidence": self.confidence
        }


@dataclass
class TranscriptAnalysisResult:
    """Resultado da análise de transcrição."""
    interview_id: str
    candidate_id: str
    job_vacancy_id: str | None
    
    # Scores WSI (0-5)
    technical_score: float
    behavioral_score: float
    cultural_score: float
    overall_wsi_score: float
    
    # Framework scores
    bloom_average: float
    dreyfus_average: float
    cbi_completeness: float
    big_five_profile: dict[str, float]
    
    # Evidências
    evidences: list[CompetencyEvidence]
    strengths: list[str]
    concerns: list[str]
    red_flags: list[str]
    
    # Parecer
    recommendation: str  # approve, reject, pending_review
    summary: str
    detailed_analysis: dict[str, Any]
    
    analyzed_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "interview_id": self.interview_id,
            "candidate_id": self.candidate_id,
            "job_vacancy_id": self.job_vacancy_id,
            "technical_score": self.technical_score,
            "behavioral_score": self.behavioral_score,
            "cultural_score": self.cultural_score,
            "overall_wsi_score": self.overall_wsi_score,
            "bloom_average": self.bloom_average,
            "dreyfus_average": self.dreyfus_average,
            "cbi_completeness": self.cbi_completeness,
            "big_five_profile": self.big_five_profile,
            "evidences": [e.to_dict() for e in self.evidences],
            "strengths": self.strengths,
            "concerns": self.concerns,
            "red_flags": self.red_flags,
            "recommendation": self.recommendation,
            "summary": self.summary,
            "detailed_analysis": self.detailed_analysis,
            "analyzed_at": self.analyzed_at.isoformat()
        }


class InterviewTranscriptAnalysisService:
    """
    Service for deterministic WSI analysis of interview transcripts.
    
    Uses linguistic indicators to calculate scores without LLM dependency.
    All scoring is based on keyword/pattern matching for consistency and speed.
    """
    
    def __init__(self):
        self.min_transcript_length = 500
        self.competency_keywords: dict[str, list[str]] = self._build_competency_keywords()
    
    def _build_competency_keywords(self) -> dict[str, list[str]]:
        """Build dictionary of common competency keywords."""
        return {
            "python": ["python", "django", "flask", "fastapi", "pandas", "numpy"],
            "javascript": ["javascript", "js", "node", "react", "vue", "angular", "typescript"],
            "java": ["java", "spring", "maven", "gradle", "jvm"],
            "cloud": ["aws", "azure", "gcp", "cloud", "kubernetes", "docker", "k8s"],
            "database": ["sql", "postgresql", "mysql", "mongodb", "redis", "database"],
            "devops": ["ci/cd", "jenkins", "github actions", "terraform", "ansible"],
            "machine_learning": ["machine learning", "ml", "deep learning", "tensorflow", "pytorch"],
            "data": ["data", "analytics", "etl", "pipeline", "spark", "airflow"],
            "leadership": ["liderança", "liderei", "coordenei", "gerenciei", "equipe"],
            "communication": ["comunicação", "apresentei", "expliquei", "negociei", "stakeholder"],
            "problem_solving": ["resolvi", "solucionei", "diagnostiquei", "analisei", "identifiquei"],
            "teamwork": ["equipe", "colaborei", "trabalhei junto", "parceria", "time"],
            "agile": ["scrum", "kanban", "agile", "sprint", "retrospectiva", "daily"],
            "architecture": ["arquitetura", "design", "padrões", "microserviços", "api"]
        }
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for analysis."""
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text
    
    def _count_indicator_matches(self, text: str, indicators: list[str]) -> int:
        """Count how many indicators are found in text."""
        text_lower = text.lower()
        count = 0
        for indicator in indicators:
            if indicator.lower() in text_lower:
                count += 1
        return count
    
    def _extract_sentences_with_indicators(
        self, 
        text: str, 
        indicators: list[str]
    ) -> list[str]:
        """Extract sentences containing any of the indicators."""
        sentences = re.split(r'[.!?]+', text)
        matches = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            sentence_lower = sentence.lower()
            for indicator in indicators:
                if indicator.lower() in sentence_lower:
                    matches.append(sentence)
                    break
        
        return matches
    
    def analyze_transcript(
        self,
        transcript_text: str,
        interview_id: str,
        candidate_id: str,
        job_vacancy_id: str | None = None,
        job_competencies: list[dict] | None = None
    ) -> TranscriptAnalysisResult:
        """
        Analyze interview transcript using WSI deterministic methodology.
        
        Args:
            transcript_text: Full transcript text (from Teams VTT parsed)
            interview_id: Interview UUID
            candidate_id: Candidate UUID
            job_vacancy_id: Optional job vacancy UUID
            job_competencies: Optional list of required competencies from job
            
        Returns:
            TranscriptAnalysisResult with scores and recommendation
        """
        if len(transcript_text) < self.min_transcript_length:
            logger.warning(f"Transcript too short: {len(transcript_text)} chars")
        
        normalized_text = self._normalize_text(transcript_text)
        
        # Calculate framework scores
        bloom_score, bloom_level = self._calculate_bloom_score(normalized_text)
        dreyfus_score, dreyfus_level = self._calculate_dreyfus_score(normalized_text)
        cbi_score, cbi_components = self._calculate_cbi_completeness(normalized_text)
        big_five = self._calculate_big_five_profile(normalized_text)
        
        # Extract evidences
        competencies = job_competencies or []
        evidences = self._extract_evidences(transcript_text, competencies)
        
        # Calculate competency match score
        competency_match = self._calculate_competency_match(normalized_text, competencies)
        
        # Detect strengths, concerns, and red flags
        strengths = self._detect_strengths(transcript_text)
        concerns = self._detect_concerns(transcript_text, bloom_level, dreyfus_level)
        red_flags = self._detect_red_flags(transcript_text)
        
        # Calculate category scores
        technical_score = self._calculate_technical_score(
            normalized_text, competencies, bloom_level, dreyfus_level
        )
        behavioral_score = self._calculate_behavioral_score(
            big_five, cbi_score, evidences
        )
        cultural_score = self._calculate_cultural_score(big_five, evidences)
        
        # Calculate overall WSI
        overall_wsi = self._calculate_overall_wsi(
            bloom_score, dreyfus_score, cbi_score, competency_match
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            overall_wsi, red_flags, len(evidences)
        )
        
        # Build result
        result = TranscriptAnalysisResult(
            interview_id=interview_id,
            candidate_id=candidate_id,
            job_vacancy_id=job_vacancy_id,
            technical_score=round(technical_score, 2),
            behavioral_score=round(behavioral_score, 2),
            cultural_score=round(cultural_score, 2),
            overall_wsi_score=overall_wsi,
            bloom_average=round(bloom_score, 2),
            dreyfus_average=round(dreyfus_score, 2),
            cbi_completeness=round(cbi_score, 2),
            big_five_profile=big_five,
            evidences=evidences,
            strengths=strengths,
            concerns=concerns,
            red_flags=red_flags,
            recommendation=recommendation,
            summary="",
            detailed_analysis={
                "bloom_level": bloom_level,
                "dreyfus_stage": dreyfus_level,
                "cbi_components_found": cbi_components,
                "competency_match": round(competency_match, 2),
                "transcript_length": len(transcript_text),
                "evidence_count": len(evidences)
            }
        )
        
        # Generate summary
        result.summary = self._generate_summary(result)
        
        logger.info(
            f"Transcript analysis completed for candidate {candidate_id}: "
            f"WSI={overall_wsi}, recommendation={recommendation}"
        )
        
        return result
    
    def _calculate_bloom_score(self, text: str) -> tuple[float, int]:
        """
        Calculate Bloom taxonomy score from text indicators.
        
        Returns:
            Tuple of (normalized_score 0-5, highest_level 1-6)
        """
        level_scores = {}
        
        for level, indicators in BLOOM_INDICATORS.items():
            count = self._count_indicator_matches(text, indicators)
            level_scores[level] = count
        
        if not any(level_scores.values()):
            return 2.0, BloomLevel.UNDERSTAND.value
        
        # Find highest level with significant matches
        highest_level = BloomLevel.REMEMBER
        for level in reversed(list(BloomLevel)):
            if level_scores.get(level, 0) >= 2:
                highest_level = level
                break
        
        # Calculate weighted score
        total_weight = 0
        weighted_sum = 0
        
        for level, count in level_scores.items():
            if count > 0:
                weight = count * level.value
                weighted_sum += weight
                total_weight += count
        
        if total_weight == 0:
            avg_level = 2.0
        else:
            avg_level = weighted_sum / total_weight
        
        # Normalize to 0-5 scale (Bloom is 1-6)
        normalized_score = (avg_level / 6) * 5
        
        return normalized_score, highest_level.value
    
    def _calculate_dreyfus_score(self, text: str) -> tuple[float, int]:
        """
        Calculate Dreyfus stage from text indicators.
        
        Returns:
            Tuple of (normalized_score 0-5, stage 1-5)
        """
        stage_scores = {}
        
        for stage, indicators in DREYFUS_INDICATORS.items():
            count = self._count_indicator_matches(text, indicators)
            stage_scores[stage] = count
        
        if not any(stage_scores.values()):
            return 2.5, DreyfusStage.COMPETENT.value
        
        # Find highest stage with matches
        highest_stage = DreyfusStage.NOVICE
        for stage in reversed(list(DreyfusStage)):
            if stage_scores.get(stage, 0) >= 2:
                highest_stage = stage
                break
        
        # Calculate weighted average
        total_weight = 0
        weighted_sum = 0
        
        for stage, count in stage_scores.items():
            if count > 0:
                weight = count * stage.value
                weighted_sum += weight
                total_weight += count
        
        if total_weight == 0:
            avg_stage = 3.0
        else:
            avg_stage = weighted_sum / total_weight
        
        # Already on 1-5 scale, just normalize
        normalized_score = avg_stage
        
        return normalized_score, highest_stage.value
    
    def _calculate_cbi_completeness(self, text: str) -> tuple[float, dict[str, bool]]:
        """
        Calculate CBI STAR completeness score.
        
        Returns:
            Tuple of (completeness_score 0-1, components_found dict)
        """
        components_found = {}
        
        for component, indicators in CBI_STAR_INDICATORS.items():
            count = self._count_indicator_matches(text, indicators)
            components_found[component] = count >= 2
        
        # Calculate completeness (0-1)
        found_count = sum(1 for v in components_found.values() if v)
        completeness = found_count / 4.0
        
        # Bonus for having all STAR components
        if all(components_found.values()):
            completeness = min(1.0, completeness + 0.1)
        
        return completeness, components_found
    
    def _calculate_big_five_profile(self, text: str) -> dict[str, float]:
        """
        Calculate Big Five profile from text indicators.
        
        Returns:
            Dict with trait scores from -1 (low) to +1 (high)
        """
        profile = {}
        
        for trait in BigFiveTrait:
            indicators = BIG_FIVE_INDICATORS[trait]
            high_count = self._count_indicator_matches(text, indicators["high"])
            low_count = self._count_indicator_matches(text, indicators["low"])
            
            total = high_count + low_count
            if total == 0:
                score = 0.0
            else:
                # Calculate normalized score (-1 to +1)
                score = (high_count - low_count) / max(total, 1)
            
            profile[trait.value] = round(score, 2)
        
        return profile
    
    def _extract_evidences(
        self, 
        text: str, 
        competencies: list[dict]
    ) -> list[CompetencyEvidence]:
        """Extract competency evidences from transcript."""
        evidences = []
        sentences = re.split(r'[.!?]+', text)
        
        # Build competency lookup
        comp_keywords = {}
        for comp in competencies:
            name = comp.get("name", "").lower()
            keywords = comp.get("keywords", [])
            if not keywords:
                keywords = self.competency_keywords.get(name, [name])
            comp_keywords[comp.get("name", "")] = keywords
        
        # Also check built-in competency keywords
        for comp_name, keywords in self.competency_keywords.items():
            if comp_name not in [c.get("name", "").lower() for c in competencies]:
                comp_keywords[comp_name] = keywords
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            sentence_lower = sentence.lower()
            
            for comp_name, keywords in comp_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in sentence_lower:
                        # Calculate confidence based on CBI presence
                        cbi_count = 0
                        for component, indicators in CBI_STAR_INDICATORS.items():
                            if any(ind.lower() in sentence_lower for ind in indicators):
                                cbi_count += 1
                        
                        confidence = min(1.0, 0.3 + (cbi_count * 0.2))
                        
                        # Determine category
                        category = "technical"
                        if comp_name in ["leadership", "communication", "teamwork", "problem_solving"]:
                            category = "behavioral"
                        
                        evidence = CompetencyEvidence(
                            competency_name=comp_name,
                            category=category,
                            evidence_text=sentence[:200],
                            bloom_level=self._get_sentence_bloom_level(sentence),
                            dreyfus_stage=self._get_sentence_dreyfus_stage(sentence),
                            cbi_components=self._get_sentence_cbi_components(sentence),
                            confidence=confidence
                        )
                        evidences.append(evidence)
                        break
        
        # Deduplicate by competency (keep highest confidence)
        unique_evidences = {}
        for ev in evidences:
            key = ev.competency_name
            if key not in unique_evidences or ev.confidence > unique_evidences[key].confidence:
                unique_evidences[key] = ev
        
        return list(unique_evidences.values())
    
    def _get_sentence_bloom_level(self, sentence: str) -> int | None:
        """Get Bloom level for a specific sentence."""
        sentence_lower = sentence.lower()
        for level in reversed(list(BloomLevel)):
            if any(ind.lower() in sentence_lower for ind in BLOOM_INDICATORS[level]):
                return level.value
        return None
    
    def _get_sentence_dreyfus_stage(self, sentence: str) -> int | None:
        """Get Dreyfus stage for a specific sentence."""
        sentence_lower = sentence.lower()
        for stage in reversed(list(DreyfusStage)):
            if any(ind.lower() in sentence_lower for ind in DREYFUS_INDICATORS[stage]):
                return stage.value
        return None
    
    def _get_sentence_cbi_components(self, sentence: str) -> list[str]:
        """Get CBI components present in a sentence."""
        components = []
        sentence_lower = sentence.lower()
        for component, indicators in CBI_STAR_INDICATORS.items():
            if any(ind.lower() in sentence_lower for ind in indicators):
                components.append(component)
        return components
    
    def _calculate_competency_match(
        self, 
        text: str, 
        competencies: list[dict]
    ) -> float:
        """Calculate competency match score (0-1)."""
        if not competencies:
            return 0.7  # Default when no competencies specified
        
        matched = 0
        total = len(competencies)
        
        for comp in competencies:
            name = comp.get("name", "").lower()
            keywords = comp.get("keywords", [])
            if not keywords:
                keywords = self.competency_keywords.get(name, [name])
            
            for keyword in keywords:
                if keyword.lower() in text:
                    matched += 1
                    break
        
        return matched / total if total > 0 else 0.7
    
    def _detect_strengths(self, text: str) -> list[str]:
        """Detect candidate strengths from transcript."""
        strengths = []
        text_lower = text.lower()
        
        strength_patterns = {
            "Entrega de resultados mensuráveis": ["resultado", "entrega", "meta", "objetivo"],
            "Experiência em liderança": ["liderei", "coordenei", "gerenciei", "equipe"],
            "Capacidade de resolver problemas": ["resolvi", "solucionei", "problema", "desafio"],
            "Boa comunicação": ["apresentei", "comuniquei", "expliquei", "negociei"],
            "Conhecimento técnico profundo": ["arquitetura", "design", "especialista", "expert"],
            "Trabalho em equipe": ["colaboração", "equipe", "time", "parceria"],
            "Proatividade": ["propus", "sugeri", "iniciei", "criei"],
            "Adaptabilidade": ["adaptei", "mudança", "novo contexto", "flexível"]
        }
        
        for strength, keywords in strength_patterns.items():
            if any(kw in text_lower for kw in keywords):
                strengths.append(strength)
        
        return strengths[:5]  # Max 5 strengths
    
    def _detect_concerns(
        self, 
        text: str, 
        bloom_level: int, 
        dreyfus_stage: int
    ) -> list[str]:
        """Detect potential concerns."""
        concerns = []
        
        if bloom_level <= 2:
            concerns.append("Respostas em nível básico (Bloom 1-2), sem demonstração de aplicação prática")
        
        if dreyfus_stage <= 1:
            concerns.append("Indicadores de nível iniciante (Dreyfus 1), dependência de instruções")
        
        if len(text) < 1000:
            concerns.append("Transcrição curta, pode indicar respostas superficiais")
        
        text_lower = text.lower()
        if "não sei" in text_lower or "não conheço" in text_lower:
            concerns.append("Candidato demonstrou desconhecimento em alguns temas")
        
        if "nunca fiz" in text_lower:
            concerns.append("Falta de experiência prática em áreas mencionadas")
        
        return concerns
    
    def _detect_red_flags(self, text: str) -> list[str]:
        """Detect red flags in transcript."""
        red_flags = []
        text_lower = text.lower()
        
        for indicator in RED_FLAG_INDICATORS:
            if indicator.lower() in text_lower:
                sentences = self._extract_sentences_with_indicators(text, [indicator])
                if sentences:
                    red_flags.append(f"Indicador detectado: '{indicator}' - '{sentences[0][:100]}...'")
        
        # Check for inconsistencies
        if "anos de experiência" in text_lower:
            years_mentions = re.findall(r'(\d+)\s*anos?\s*(?:de\s*)?experiência', text_lower)
            if len(set(years_mentions)) > 1:
                red_flags.append("Inconsistência no tempo de experiência mencionado")
        
        return red_flags[:5]  # Max 5 red flags
    
    def _calculate_technical_score(
        self,
        text: str,
        competencies: list[dict],
        bloom_level: int,
        dreyfus_stage: int
    ) -> float:
        """Calculate technical competency score (0-5)."""
        technical_comps = [c for c in competencies if c.get("type") == "technical"]
        
        if not technical_comps:
            # Use detected technical keywords
            tech_keywords = []
            for name, keywords in self.competency_keywords.items():
                if name not in ["leadership", "communication", "teamwork", "problem_solving"]:
                    tech_keywords.extend(keywords)
            
            matches = self._count_indicator_matches(text, tech_keywords)
            base_score = min(4.0, 2.0 + (matches * 0.2))
        else:
            match_score = self._calculate_competency_match(text, technical_comps)
            base_score = match_score * 5
        
        # Adjust based on Bloom/Dreyfus
        bloom_modifier = (bloom_level - 3) * 0.2
        dreyfus_modifier = (dreyfus_stage - 3) * 0.2
        
        final_score = base_score + bloom_modifier + dreyfus_modifier
        
        return max(0.0, min(5.0, final_score))
    
    def _calculate_behavioral_score(
        self,
        big_five: dict[str, float],
        cbi_score: float,
        evidences: list[CompetencyEvidence]
    ) -> float:
        """Calculate behavioral competency score (0-5)."""
        # CBI completeness contributes 40%
        cbi_contribution = cbi_score * 5 * 0.4
        
        # Big Five positive traits contribute 40%
        positive_traits = [
            big_five.get("conscientiousness", 0),
            big_five.get("agreeableness", 0),
            big_five.get("openness", 0)
        ]
        trait_avg = sum(positive_traits) / len(positive_traits)
        trait_contribution = ((trait_avg + 1) / 2) * 5 * 0.4
        
        # Behavioral evidences contribute 20%
        behavioral_evidences = [e for e in evidences if e.category == "behavioral"]
        evidence_contribution = min(1.0, len(behavioral_evidences) / 3) * 5 * 0.2
        
        return cbi_contribution + trait_contribution + evidence_contribution
    
    def _calculate_cultural_score(
        self,
        big_five: dict[str, float],
        evidences: list[CompetencyEvidence]
    ) -> float:
        """Calculate cultural fit score (0-5)."""
        # Extraversion and agreeableness indicate cultural adaptability
        cultural_traits = [
            big_five.get("extraversion", 0),
            big_five.get("agreeableness", 0),
            big_five.get("openness", 0)
        ]
        
        trait_avg = sum(cultural_traits) / len(cultural_traits)
        base_score = ((trait_avg + 1) / 2) * 5
        
        # Low neuroticism is positive for cultural fit
        neuroticism = big_five.get("neuroticism", 0)
        neuroticism_modifier = -neuroticism * 0.5
        
        return max(0.0, min(5.0, base_score + neuroticism_modifier))
    
    def _calculate_overall_wsi(
        self,
        bloom: float,
        dreyfus: float,
        cbi: float,
        competency_match: float
    ) -> float:
        """
        Calculate overall WSI score using deterministic formula.
        
        Weights:
        - Bloom (cognitive level): 25%
        - Dreyfus (expertise stage): 25%
        - CBI completeness: 30%
        - Competency match: 20%
        """
        weights = {
            "bloom": 0.25,
            "dreyfus": 0.25,
            "cbi": 0.30,
            "competency": 0.20
        }
        
        # Normalize to 0-5 scale
        score = (
            bloom * weights["bloom"] +
            dreyfus * weights["dreyfus"] +
            cbi * 5 * weights["cbi"] +
            competency_match * 5 * weights["competency"]
        )
        
        return round(min(5.0, max(0.0, score)), 2)
    
    def _generate_recommendation(
        self,
        wsi_score: float,
        red_flags: list[str],
        evidence_count: int
    ) -> str:
        """Generate recommendation based on scores."""
        if len(red_flags) >= 3:
            return "reject"
        
        if wsi_score >= 4.0 and evidence_count >= 5 and len(red_flags) == 0:
            return "approve"
        
        if wsi_score >= 3.5 and evidence_count >= 3:
            return "approve"
        
        if wsi_score >= 3.0:
            return "pending_review"
        
        if wsi_score < 2.5:
            return "reject"
        
        return "pending_review"
    
    def _generate_summary(self, result: "TranscriptAnalysisResult") -> str:
        """Generate human-readable summary in Portuguese."""
        # Classification based on WSI
        if result.overall_wsi_score >= 4.0:
            classification = "Excelente"
            classification_desc = "O candidato demonstrou alto nível de competência"
        elif result.overall_wsi_score >= 3.5:
            classification = "Bom"
            classification_desc = "O candidato apresentou bom desempenho"
        elif result.overall_wsi_score >= 3.0:
            classification = "Satisfatório"
            classification_desc = "O candidato atendeu expectativas básicas"
        elif result.overall_wsi_score >= 2.5:
            classification = "Regular"
            classification_desc = "O candidato apresentou desempenho abaixo do esperado"
        else:
            classification = "Insuficiente"
            classification_desc = "O candidato não atendeu os requisitos mínimos"
        
        # Build summary
        summary_parts = []
        
        # Header
        summary_parts.append(f"**Parecer de Triagem WSI - {classification}**")
        summary_parts.append(f"\nScore WSI Geral: {result.overall_wsi_score}/5.0")
        summary_parts.append(f"\n{classification_desc}.")
        
        # Scores breakdown
        summary_parts.append("\n\n**Scores por Dimensão:**")
        summary_parts.append(f"- Técnico: {result.technical_score}/5.0")
        summary_parts.append(f"- Comportamental: {result.behavioral_score}/5.0")
        summary_parts.append(f"- Cultural: {result.cultural_score}/5.0")
        
        # Frameworks
        summary_parts.append("\n\n**Análise por Framework:**")
        summary_parts.append(f"- Bloom (nível cognitivo): {result.bloom_average}/5.0")
        summary_parts.append(f"- Dreyfus (estágio expertise): {result.dreyfus_average}/5.0")
        summary_parts.append(f"- CBI (completude STAR): {result.cbi_completeness * 100:.0f}%")
        
        # Strengths
        if result.strengths:
            summary_parts.append("\n\n**Pontos Fortes Identificados:**")
            for strength in result.strengths[:3]:
                summary_parts.append(f"- {strength}")
        
        # Concerns
        if result.concerns:
            summary_parts.append("\n\n**Pontos de Atenção:**")
            for concern in result.concerns[:3]:
                summary_parts.append(f"- {concern}")
        
        # Red flags
        if result.red_flags:
            summary_parts.append("\n\n**⚠️ Alertas Detectados:**")
            for flag in result.red_flags[:2]:
                summary_parts.append(f"- {flag}")
        
        # Evidence count
        summary_parts.append(f"\n\n**Evidências Coletadas:** {len(result.evidences)}")
        
        # Recommendation
        rec_map = {
            "approve": "✅ Aprovado para próxima fase",
            "reject": "❌ Não recomendado para continuidade",
            "pending_review": "🔍 Requer revisão manual do recrutador"
        }
        summary_parts.append(f"\n\n**Recomendação:** {rec_map.get(result.recommendation, result.recommendation)}")
        
        return "\n".join(summary_parts)
    
    def parse_vtt_to_text(self, vtt_content: str) -> str:
        """
        Parse VTT (WebVTT) transcript format to plain text.
        
        Args:
            vtt_content: Raw VTT content from Teams transcript
            
        Returns:
            Plain text transcript
        """
        lines = vtt_content.split('\n')
        text_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip VTT headers and timestamps
            if line.startswith('WEBVTT') or line.startswith('NOTE'):
                continue
            if re.match(r'^\d{2}:\d{2}:\d{2}', line):
                continue
            if line.startswith('<v '):
                # Extract speaker name and text: <v Speaker Name>text</v>
                match = re.match(r'<v ([^>]+)>(.+)</v>', line)
                if match:
                    speaker, text = match.groups()
                    text_lines.append(f"{speaker}: {text}")
                else:
                    # Just remove the tags
                    clean = re.sub(r'<[^>]+>', '', line)
                    if clean.strip():
                        text_lines.append(clean.strip())
            elif line and not line.isdigit():
                text_lines.append(line)
        
        return ' '.join(text_lines)


# Singleton instance
interview_transcript_analysis_service = InterviewTranscriptAnalysisService()
