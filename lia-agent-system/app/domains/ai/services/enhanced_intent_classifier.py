"""
EnhancedIntentClassifier - Classificador de intenções com extração rica de entidades.

Melhorias sobre o IntentClassifier básico:
- Extrai TODAS as entidades mencionadas pelo usuário
- Detecta contexto específico (vaga afirmativa, benefícios, idiomas, etc.)
- Usa prompt mais inteligente para o LLM
- Fallback inteligente com sugestões
"""
import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any

from app.prompts import PromptLoader
from app.domains.ai.services.llm import llm_service
from app.shared.prompts.loader import PromptLoader

logger = logging.getLogger(__name__)


class EnhancedIntentType(StrEnum):
    CREATE_JOB = "CREATE_JOB"
    UPDATE_FIELD = "UPDATE_FIELD"
    QUESTION = "QUESTION"
    CORRECTION = "CORRECTION"
    NAVIGATION = "NAVIGATION"
    REUSE_VACANCY = "REUSE_VACANCY"
    CONFIRM = "CONFIRM"
    REJECT = "REJECT"
    HELP = "HELP"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


@dataclass
class ExtractedEntities:
    """Todas as entidades extraídas da mensagem do usuário."""
    cargo: str | None = None
    area: str | None = None
    senioridade: str | None = None
    
    salario_min: float | None = None
    salario_max: float | None = None
    bonus: str | None = None
    
    modelo_trabalho: str | None = None
    localizacao: str | None = None
    tipo_contrato: str | None = None
    
    skills_tecnicas: list[str] = field(default_factory=list)
    skills_comportamentais: list[str] = field(default_factory=list)
    idiomas: list[str] = field(default_factory=list)
    
    beneficios: list[str] = field(default_factory=list)
    
    is_afirmativa: bool = False
    criterio_afirmativo_primario: str | None = None
    criterio_afirmativo_secundario: str | None = None
    
    gestor: str | None = None
    gestor_email: str | None = None
    recrutador: str | None = None
    
    prazo: str | None = None
    urgencia: str | None = None
    
    filtro_busca: dict[str, Any] = field(default_factory=dict)
    
    raw_entities: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário, excluindo valores None e listas vazias."""
        result = {}
        for key, value in self.__dict__.items():
            if value is None:
                continue
            if isinstance(value, list) and len(value) == 0:
                continue
            if isinstance(value, dict) and len(value) == 0:
                continue
            result[key] = value
        return result


@dataclass
class EnhancedClassificationResult:
    """Resultado completo da classificação."""
    intent_type: EnhancedIntentType
    confidence: float
    entities: ExtractedEntities
    original_text: str
    reasoning: str | None = None
    suggested_actions: list[str] = field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: str | None = None


class EnhancedIntentClassifierService:
    """
    Classificador de intenções aprimorado com extração rica de entidades.
    """
    
    CLASSIFICATION_PROMPT = PromptLoader.get_domain_prompt("intent_classification")

    AFFIRMATIVE_PATTERNS = [
        (r"\b(pcd|pcds|pessoa com defici[eê]ncia|deficientes?)\b", "PCD"),
        (r"\b(mulher|mulheres|feminino|feminina)\b", "Mulheres"),
        (r"\b(negro|negra|negros|negras|afrodescendente|preto|preta)\b", "Pessoas Negras"),
        (r"\b(lgbtqia\+?|lgbt\+?|lgbtq\+?|lgbti\+?)\b", "LGBTQIA+"),
        (r"\b(50\+|mais de 50|acima de 50|terceira idade|idoso|idosa)\b", "50+"),
        (r"\b(ind[ií]gena|povos origin[aá]rios)\b", "Indígena"),
        (r"\b(trans|transg[eê]nero|transexual)\b", "Pessoas Trans"),
        (r"\b(inclusiv[ao]|diversidade|a[çc][aã]o afirmativa)\b", "Diversidade"),
    ]
    
    BENEFIT_PATTERNS = [
        r"\b(vr|vale[- ]?refei[çc][aã]o)\b",
        r"\b(va|vale[- ]?alimenta[çc][aã]o)\b",
        r"\b(vt|vale[- ]?transporte)\b",
        r"\b(plano de sa[úu]de|conv[eê]nio m[ée]dico)\b",
        r"\b(plano odontol[óo]gico|conv[eê]nio odonto)\b",
        r"\b(gympass|totalpass|academia)\b",
        r"\b(ppr|plr|participa[çc][aã]o nos lucros)\b",
        r"\b(home[- ]?office|trabalho remoto)\b",
        r"\b(aux[ií]lio creche|creche)\b",
        r"\b(seguro de vida)\b",
        r"\b(previd[eê]ncia privada)\b",
        r"\b(day[- ]?off|folga anivers[aá]rio)\b",
        r"\b(stock options|a[çc][oõ]es)\b",
        r"\b(b[oô]nus|bonifica[çc][aã]o)\b",
    ]
    
    LANGUAGE_PATTERNS = [
        (r"\b(ingl[eê]s|english)\b", "Inglês"),
        (r"\b(espanhol|spanish|castelhano)\b", "Espanhol"),
        (r"\b(franc[eê]s|french)\b", "Francês"),
        (r"\b(alem[aã]o|german)\b", "Alemão"),
        (r"\b(italiano|italian)\b", "Italiano"),
        (r"\b(mandarim|chin[eê]s|chinese)\b", "Mandarim"),
        (r"\b(japon[eê]s|japanese)\b", "Japonês"),
        (r"\b(coreano|korean)\b", "Coreano"),
    ]
    
    TECH_SKILLS = [
        "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "C#",
        "React", "Angular", "Vue", "Node", "Next.js", "Nuxt", "Django", "Flask", "FastAPI",
        "Spring", "Rails", "Laravel", "Express", "NestJS",
        "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
        "Kafka", "RabbitMQ", "GraphQL", "REST", "gRPC",
        "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
        "Figma", "Sketch", "Adobe", "UI/UX", "Product Design",
        "Scrum", "Kanban", "Agile", "Jira", "Confluence",
        "Git", "CI/CD", "Jenkins", "GitHub Actions", "GitLab CI",
        "Power BI", "Tableau", "Data Analysis", "SQL", "Excel avançado",
        "SAP", "Salesforce", "HubSpot", "Dynamics",
    ]
    
    SOFT_SKILLS = [
        "liderança", "comunicação", "trabalho em equipe", "proatividade",
        "organização", "gestão de tempo", "resolução de problemas",
        "pensamento crítico", "criatividade", "adaptabilidade",
        "inteligência emocional", "negociação", "apresentação",
        "gestão de conflitos", "mentoria", "feedback",
        "ownership", "accountability", "autonomia", "iniciativa",
    ]

    QUICK_PATTERNS = {
        "correction": ["na verdade", "não é", "errei", "corrijo", "correção", "esqueci", "não era"],
        "navigation": ["pula", "próximo", "voltar", "anterior", "skip", "next", "back"],
        "confirm": ["sim", "ok", "pode ser", "confirmo", "isso", "exato", "correto", "isso mesmo"],
        "reject": ["não", "cancela", "não quero", "errado", "negativo"],
        "help": ["ajuda", "help", "como funciona", "o que fazer", "explica"],
        "reuse": [
            "últimas vagas", "ultimas vagas", "vagas criadas", "buscar vaga", 
            "listar vagas", "mostrar vagas", "vagas anteriores", "copiar vaga",
            "reutilizar", "fast track", "vaga anterior"
        ],
    }

    def __init__(self):
        self._llm_service = llm_service

    def _quick_classify(self, text: str) -> tuple[EnhancedIntentType | None, float]:
        """Classificação rápida por regras para casos óbvios."""
        text_lower = text.lower().strip()
        
        for pattern in self.QUICK_PATTERNS["correction"]:
            if pattern in text_lower:
                return EnhancedIntentType.CORRECTION, 0.9
        
        for pattern in self.QUICK_PATTERNS["reuse"]:
            if pattern in text_lower:
                return EnhancedIntentType.REUSE_VACANCY, 0.9
        
        for pattern in self.QUICK_PATTERNS["navigation"]:
            if pattern in text_lower and not text_lower.endswith("?"):
                return EnhancedIntentType.NAVIGATION, 0.85
        
        if text_lower in ["sim", "ok", "s", "yes", "pode"]:
            return EnhancedIntentType.CONFIRM, 0.95
        
        if text_lower in ["não", "nao", "n", "no", "cancela"]:
            return EnhancedIntentType.REJECT, 0.95
        
        for pattern in self.QUICK_PATTERNS["help"]:
            if pattern in text_lower:
                return EnhancedIntentType.HELP, 0.85
        
        if text.strip().endswith("?"):
            return EnhancedIntentType.QUESTION, 0.8
        
        return None, 0.0

    def _extract_entities_regex(self, text: str) -> ExtractedEntities:
        """Extrai entidades usando regex (fallback e complemento ao LLM)."""
        entities = ExtractedEntities()
        text_lower = text.lower()
        
        for pattern, criteria in self.AFFIRMATIVE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                entities.is_afirmativa = True
                if not entities.criterio_afirmativo_primario:
                    entities.criterio_afirmativo_primario = criteria
                elif not entities.criterio_afirmativo_secundario:
                    entities.criterio_afirmativo_secundario = criteria
        
        for pattern in self.BENEFIT_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            entities.beneficios.extend(matches)
        
        for pattern, language in self.LANGUAGE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                if language not in entities.idiomas:
                    entities.idiomas.append(language)
        
        for skill in self.TECH_SKILLS:
            if re.search(rf"\b{re.escape(skill)}\b", text, re.IGNORECASE):
                if skill not in entities.skills_tecnicas:
                    entities.skills_tecnicas.append(skill)
        
        for skill in self.SOFT_SKILLS:
            if skill.lower() in text_lower:
                if skill not in entities.skills_comportamentais:
                    entities.skills_comportamentais.append(skill)
        
        salary_patterns = [
            r"(\d+(?:\.\d+)?)\s*[kK]",
            r"R\$?\s*(\d+(?:\.\d{3})*(?:,\d{2})?)",
            r"(\d+)\s*(?:mil|reais)",
        ]
        for pattern in salary_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    value = float(match.replace(".", "").replace(",", "."))
                    if value < 100:
                        value *= 1000
                    if not entities.salario_min:
                        entities.salario_min = value
                    elif not entities.salario_max and value != entities.salario_min:
                        entities.salario_max = value
                except Exception:
                    pass
        
        work_model_match = re.search(r"\b(remoto|híbrido|hibrido|presencial|home\s*office)\b", text_lower)
        if work_model_match:
            model = work_model_match.group(1)
            if "home" in model or model == "remoto":
                entities.modelo_trabalho = "Remoto"
            elif "híbrido" in model or "hibrido" in model:
                entities.modelo_trabalho = "Híbrido"
            else:
                entities.modelo_trabalho = "Presencial"
        
        seniority_match = re.search(r"\b(júnior|junior|jr|pleno|pl|sênior|senior|sr|lead|staff|principal)\b", text_lower)
        if seniority_match:
            sen = seniority_match.group(1).lower()
            if sen in ["júnior", "junior", "jr"]:
                entities.senioridade = "Júnior"
            elif sen in ["pleno", "pl"]:
                entities.senioridade = "Pleno"
            elif sen in ["sênior", "senior", "sr"]:
                entities.senioridade = "Sênior"
            elif sen == "lead":
                entities.senioridade = "Lead"
            elif sen == "staff":
                entities.senioridade = "Staff"
            elif sen == "principal":
                entities.senioridade = "Principal"
        
        contract_match = re.search(r"\b(clt|pj|est[aá]gio|tempor[aá]rio|freelancer)\b", text_lower)
        if contract_match:
            contract = contract_match.group(1).lower()
            if contract == "clt":
                entities.tipo_contrato = "CLT"
            elif contract == "pj":
                entities.tipo_contrato = "PJ"
            elif "estag" in contract:
                entities.tipo_contrato = "Estágio"
            elif "tempor" in contract:
                entities.tipo_contrato = "Temporário"
            else:
                entities.tipo_contrato = "Freelancer"
        
        urgency_match = re.search(r"\b(urgente|urg[eê]ncia|prioridade alta|muito urgente|asap)\b", text_lower)
        if urgency_match:
            entities.urgencia = "Alta"
        
        return entities

    async def classify(
        self,
        user_input: str,
        stage: int = 1,
        filled_fields: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None
    ) -> EnhancedClassificationResult:
        """
        Classifica a intenção do usuário e extrai todas as entidades.
        
        Args:
            user_input: Texto do usuário
            stage: Estágio atual do wizard (1-5)
            filled_fields: Campos já preenchidos
            context: Contexto adicional
            
        Returns:
            EnhancedClassificationResult com intent, entidades e sugestões
        """
        quick_intent, quick_confidence = self._quick_classify(user_input)
        
        regex_entities = self._extract_entities_regex(user_input)
        
        if quick_intent and quick_confidence >= 0.9:
            return EnhancedClassificationResult(
                intent_type=quick_intent,
                confidence=quick_confidence,
                entities=regex_entities,
                original_text=user_input,
                reasoning="Classificação rápida por padrão conhecido"
            )
        
        try:
            filled_str = ", ".join(filled_fields.keys()) if filled_fields else "nenhum"
            
            prompt = self.CLASSIFICATION_PROMPT.format(
                stage=stage,
                filled_fields=filled_str,
                user_input=user_input
            )
            
            response = await self._llm_service.generate(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.1
            )
            
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                result = json.loads(json_match.group())
                
                intent_str = result.get("intent", "CREATE_JOB")
                try:
                    intent = EnhancedIntentType(intent_str)
                except ValueError:
                    intent = EnhancedIntentType.CREATE_JOB
                
                llm_entities = result.get("entities", {})
                
                merged_entities = self._merge_entities(regex_entities, llm_entities)
                
                return EnhancedClassificationResult(
                    intent_type=intent,
                    confidence=result.get("confidence", 0.8),
                    entities=merged_entities,
                    original_text=user_input,
                    reasoning=result.get("reasoning"),
                    needs_clarification=result.get("needs_clarification", False),
                    clarification_question=result.get("clarification_question")
                )
        
        except Exception as e:
            logger.error(
                f"LLM intent classification failed [{type(e).__name__}]: {e} — "
                f"degradando para fallback regex (qualidade reduzida)"
            )
            # metrics.increment("intent_classifier.llm_fallback")  # habilitar quando métricas estiverem disponíveis
        
        intent = quick_intent or EnhancedIntentType.CREATE_JOB
        confidence = quick_confidence or 0.5  # Reduzido para sinalizar qualidade menor
        
        return EnhancedClassificationResult(
            intent_type=intent,
            confidence=confidence,
            entities=regex_entities,
            original_text=user_input,
            reasoning="Fallback regex (LLM indisponível — qualidade reduzida)"
        )

    def _merge_entities(self, regex_entities: ExtractedEntities, llm_entities: dict[str, Any]) -> ExtractedEntities:
        """Mescla entidades do regex com as do LLM, priorizando LLM quando disponível."""
        merged = ExtractedEntities()
        
        simple_fields = [
            "cargo", "area", "senioridade", "salario_min", "salario_max", "bonus",
            "modelo_trabalho", "localizacao", "tipo_contrato", "gestor", "gestor_email",
            "recrutador", "prazo", "urgencia", "is_afirmativa",
            "criterio_afirmativo_primario", "criterio_afirmativo_secundario"
        ]
        
        for field in simple_fields:
            llm_value = llm_entities.get(field)
            regex_value = getattr(regex_entities, field, None)
            
            if llm_value is not None and llm_value != "" and llm_value != []:
                setattr(merged, field, llm_value)
            elif regex_value is not None:
                setattr(merged, field, regex_value)
        
        list_fields = ["skills_tecnicas", "skills_comportamentais", "idiomas", "beneficios"]
        
        for field in list_fields:
            llm_list = llm_entities.get(field, [])
            regex_list = getattr(regex_entities, field, [])
            
            combined = list(set(llm_list + regex_list))
            setattr(merged, field, combined)
        
        if llm_entities.get("filtro_busca"):
            merged.filtro_busca = llm_entities["filtro_busca"]
        
        merged.raw_entities = llm_entities
        
        return merged


enhanced_intent_classifier = EnhancedIntentClassifierService()
