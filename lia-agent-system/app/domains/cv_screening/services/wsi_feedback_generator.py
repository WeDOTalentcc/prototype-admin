"""
WSI Feedback Generator — Feedback construtivo pós-triagem para candidatos.

Gera relatório de feedback baseado nas scores WSI, calibrado por nível de seniority.
Conforme: EU AI Act (Art. 14), LGPD Art. 20, EEOC guidelines.

REGRAS DE FAIRNESS (imutáveis):
  - Sem score numérico (nunca expor wsi_final_score ao candidato)
  - Sem classificação (aprovado / reprovado / aguardando)
  - Sem red flags (informação interna apenas)
  - Sem comparação com outros candidatos
  - Bloom/Dreyfus como linguagem natural, nunca como número/rótulo duro
  - Big Five excluído (risco legal: neuroticism → ADA, disparate impact)
  - Foco em comportamentos observáveis, não traços de personalidade
  - Aviso de geração por IA no rodapé de todos os canais
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Language tables
# ---------------------------------------------------------------------------

BLOOM_STRENGTH_PHRASES: dict[int, str] = {
    1: "demonstrou familiaridade com conceitos fundamentais da área",
    2: "explicou com clareza os princípios envolvidos em suas experiências",
    3: "aplicou o conhecimento de forma concreta em situações reais",
    4: "analisou cenários com visão crítica e perspectiva comparativa",
    5: "avaliou trade-offs e defendeu suas escolhas com solidez e consistência",
    6: "propôs abordagens originais e demonstrou pensamento sistêmico avançado",
}

BLOOM_DEVELOPMENT_PHRASES: dict[int, str] = {
    1: "aprofundar a compreensão teórica para além do nível introdutório",
    2: "buscar mais oportunidades de aplicação prática dos conceitos",
    3: "desenvolver análise crítica para comparar abordagens e identificar trade-offs",
    4: "praticar a tomada de decisão em cenários complexos com justificativa sólida",
    5: "explorar projetos que exijam criação de soluções originais e inovadoras",
    6: "continuar liderando iniciativas de impacto crescente e compartilhar o aprendizado",
}

DREYFUS_DEVELOPMENT_PHRASES: dict[int, str] = {
    1: "construir base prática com projetos guiados (primeiros 6–12 meses)",
    2: "ampliar repertório com projetos reais de complexidade crescente",
    3: "assumir responsabilidades com maior autonomia e menos supervisão direta",
    4: "explorar contextos de alta ambiguidade e liderar decisões de maior impacto",
    5: "atuar como referência técnica e mentor na área",
}

SENIORITY_TONE: dict[str, dict[str, Any]] = {
    "estagiario": {
        "tone": "encorajador",
        "intro_opener": "Ficamos muito felizes com sua participação!",
        "bloom_expectation": 2,
        "dreyfus_expectation": 1,
    },
    "junior": {
        "tone": "orientador",
        "intro_opener": "Obrigado pela sua participação na triagem!",
        "bloom_expectation": 3,
        "dreyfus_expectation": 2,
    },
    "pleno": {
        "tone": "equilibrado",
        "intro_opener": "Agradecemos sua participação!",
        "bloom_expectation": 3,
        "dreyfus_expectation": 3,
    },
    "senior": {
        "tone": "peer-level",
        "intro_opener": "Agradecemos seu tempo e sua participação.",
        "bloom_expectation": 4,
        "dreyfus_expectation": 4,
    },
    "lead": {
        "tone": "consultivo",
        "intro_opener": "Foi um prazer conhecer sua experiência.",
        "bloom_expectation": 5,
        "dreyfus_expectation": 4,
    },
    "principal": {
        "tone": "consultivo",
        "intro_opener": "Foi um prazer conhecer sua trajetória.",
        "bloom_expectation": 5,
        "dreyfus_expectation": 5,
    },
    "diretor": {
        "tone": "executivo",
        "intro_opener": "Agradecemos sua participação.",
        "bloom_expectation": 5,
        "dreyfus_expectation": 5,
    },
    "vp_clevel": {
        "tone": "executivo",
        "intro_opener": "Agradecemos sua participação.",
        "bloom_expectation": 6,
        "dreyfus_expectation": 5,
    },
}

DIMENSION_META: dict[str, dict[str, str]] = {
    "technical_skills": {
        "title": "Conhecimento Técnico",
        "icon": "💡",
    },
    "interpersonal_skills": {
        "title": "Competências Comportamentais",
        "icon": "🤝",
    },
    "self_assessment": {
        "title": "Competências Comportamentais",
        "icon": "🤝",
    },
    "problem_solving": {
        "title": "Raciocínio e Solução de Problemas",
        "icon": "🔍",
    },
    "motivation": {
        "title": "Alinhamento com a Posição",
        "icon": "🎯",
    },
    "cultural_fit": {
        "title": "Alinhamento com a Posição",
        "icon": "🎯",
    },
    "_communication": {
        "title": "Clareza da Comunicação",
        "icon": "💬",
    },
}

PRACTICAL_SUGGESTIONS: dict[str, dict[int, str]] = {
    "technical_skills": {
        1: "Explore cursos práticos em plataformas como Alura, Coursera ou Udemy para ganhar experiência hands-on com as ferramentas da área.",
        2: "Desenvolva projetos pessoais ou contribua para projetos open source — transformar teoria em prática é o caminho mais eficaz.",
        3: "Aprofunde-se em design patterns e boas práticas de revisão de código para elevar a qualidade técnica.",
        4: "Explore arquiteturas de sistemas e decisões de trade-off em projetos de maior escala.",
        5: "Mentore outros profissionais e contribua com artigos ou talks técnicos para consolidar sua liderança intelectual.",
        6: "Continue publicando e compartilhando sua perspectiva — referências técnicas fazem a diferença para comunidades inteiras.",
    },
    "interpersonal_skills": {
        1: "Pratique dar e receber feedback em ambientes seguros, como grupos de estudo ou comunidades profissionais.",
        2: "Busque projetos colaborativos para exercitar comunicação e resolução de conflitos na prática.",
        3: "Leia sobre inteligência emocional (sugestão: 'Inteligência Emocional', de Daniel Goleman) para aprofundar a autoconsciência.",
        4: "Desenvolva habilidades de facilitação: conduzir reuniões e workshops fortalece muito a liderança interpessoal.",
        5: "Invista no desenvolvimento de equipes e na criação de ambientes psicologicamente seguros.",
        6: "Compartilhe seu aprendizado em liderança — ensinar é a melhor forma de consolidar conhecimento.",
    },
    "problem_solving": {
        1: "Estude frameworks de resolução de problemas como PDCA, 5 Porquês ou Design Thinking.",
        2: "Resolva desafios práticos: hackathons, estudos de caso ou problemas reais do seu contexto atual.",
        3: "Pratique analisar situações sob múltiplas perspectivas antes de propor soluções.",
        4: "Trabalhe em problemas com restrições reais (tempo, orçamento, pessoas) para desenvolver análise pragmática.",
        5: "Desenvolva a habilidade de simplificar problemas complexos para audiências não-técnicas — isso multiplica seu impacto.",
        6: "Continue criando frameworks e metodologias — sua capacidade de estruturar o pensamento é um diferencial raro.",
    },
    "motivation": {
        1: "Reflita sobre seus valores profissionais e como eles se conectam com seu propósito de carreira.",
        2: "Busque mentorias com profissionais mais experientes para clarificar sua trajetória.",
        3: "Documente suas conquistas e o impacto que gerou — isso fortalece sua narrativa de carreira.",
        4: "Conecte seu trabalho diário a objetivos maiores — isso mantém a motivação diante de desafios complexos.",
        5: "Invista em projetos de impacto ou comunidades alinhadas aos seus valores.",
        6: "Continue inspirando outras pessoas com sua visão — liderança com propósito é transformadora.",
    },
    "_communication": {
        1: "Pratique estruturar suas respostas com o método STAR (Situação, Tarefa, Ação, Resultado) para comunicar ideias com mais clareza.",
        2: "Experimente narrar experiências com início, meio e fim bem definidos — isso torna suas respostas mais memoráveis.",
        3: "Grave suas respostas (vídeo ou áudio) e revise: perceber seus padrões de comunicação acelera muito o desenvolvimento.",
        4: "Trabalhe sínteses: tente explicar conceitos complexos em 1–2 frases para diferentes audiências.",
        5: "Sua comunicação é sólida. Continue refinando a habilidade de adaptar o tom e nível de detalhe para cada contexto.",
        6: "Você comunica com clareza e impacto — continue elevando o padrão ao engajar audiências cada vez mais diversas.",
    },
}


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class WSIFeedbackGenerator:
    """
    Gera relatório de feedback construtivo pós-triagem WSI.
    Entrada: response_scores com competency + block_index enriquecidos.
    Saída: Dict com dimensions, intro, closing, plain_text, whatsapp_text, chat_text.
    """

    def generate(
        self,
        response_scores: list[dict[str, Any]],
        job_title: str,
        seniority_level: str,
        candidate_name: str,
    ) -> dict[str, Any]:
        seniority = (seniority_level or "junior").lower().strip()
        if seniority not in SENIORITY_TONE:
            # Fuzzy match fallbacks
            for key in ["estagiario", "junior", "pleno", "senior", "lead", "diretor", "vp_clevel"]:
                if key in seniority or seniority in key:
                    seniority = key
                    break
            else:
                seniority = "junior"

        tone_cfg = SENIORITY_TONE[seniority]
        first_name = (candidate_name or "candidato(a)").split()[0]

        groups = self._group_by_competency(response_scores)

        dimensions: list[dict[str, Any]] = []

        # 1 — Clareza da Comunicação (meta: todos os blocos)
        dimensions.append(
            self._make_communication_dim(response_scores, tone_cfg)
        )

        # 2 — Conhecimento Técnico (block_type=technical / competency=technical_skills)
        tech = groups.get("technical_skills", [])
        if tech:
            dimensions.append(self._make_dim("technical_skills", tech, tone_cfg))

        # 3 — Raciocínio e Solução de Problemas (problem_solving)
        prob = groups.get("problem_solving", [])
        if prob:
            dimensions.append(self._make_dim("problem_solving", prob, tone_cfg))

        # 4 — Competências Comportamentais (interpersonal + self_assessment)
        behav = groups.get("interpersonal_skills", []) + groups.get("self_assessment", [])
        if behav:
            dimensions.append(self._make_dim("interpersonal_skills", behav, tone_cfg))

        # 5 — Alinhamento com a Posição (motivation + cultural_fit)
        align = groups.get("motivation", []) + groups.get("cultural_fit", [])
        if align:
            dimensions.append(self._make_dim("motivation", align, tone_cfg))

        intro = self._intro(first_name, job_title, tone_cfg)
        closing = self._closing(first_name)

        report: dict[str, Any] = {
            "candidate_name": candidate_name,
            "first_name": first_name,
            "job_title": job_title,
            "seniority_level": seniority,
            "tone": tone_cfg["tone"],
            "dimensions": dimensions,
            "intro": intro,
            "closing": closing,
        }

        report["plain_text"] = self._plain_text(report)
        report["whatsapp_text"] = self._whatsapp_text(report)
        report["chat_text"] = self._chat_text(report)

        logger.info(
            f"[WSIFeedback] Generated for '{candidate_name}' | job='{job_title}' | "
            f"seniority={seniority} | dims={len(dimensions)}"
        )
        return report

    # ------------------------------------------------------------------
    # Grouping
    # ------------------------------------------------------------------

    def _group_by_competency(self, scores: list[dict]) -> dict[str, list[dict]]:
        groups: dict[str, list[dict]] = {}
        for s in scores:
            key = s.get("competency", "general")
            groups.setdefault(key, []).append(s)
        return groups

    # ------------------------------------------------------------------
    # Dimension builders
    # ------------------------------------------------------------------

    def _make_dim(self, competency: str, scores: list[dict], tone_cfg: dict) -> dict[str, Any]:
        meta = DIMENSION_META.get(competency, DIMENSION_META["_communication"])
        bloom = self._avg(scores, "bloom_level", default=2)
        dreyfus = self._avg(scores, "dreyfus_level", default=2)
        expected_bloom = tone_cfg["bloom_expectation"]

        evidences = [ev for s in scores for ev in s.get("evidences", [])[:2]]

        return {
            "title": meta["title"],
            "icon": meta["icon"],
            "strength": self._strength_phrase(bloom, dreyfus, evidences),
            "development": self._development_phrase(bloom, dreyfus, expected_bloom),
            "suggestion": self._suggestion(competency, bloom),
        }

    def _make_communication_dim(self, all_scores: list[dict], tone_cfg: dict) -> dict[str, Any]:
        meta = DIMENSION_META["_communication"]
        bloom = self._avg(all_scores, "bloom_level", default=2)
        dreyfus = self._avg(all_scores, "dreyfus_level", default=2)
        expected_bloom = tone_cfg["bloom_expectation"]

        return {
            "title": meta["title"],
            "icon": meta["icon"],
            "strength": self._strength_phrase(bloom, dreyfus, []),
            "development": self._development_phrase(bloom, dreyfus, expected_bloom),
            "suggestion": self._suggestion("_communication", bloom),
        }

    # ------------------------------------------------------------------
    # Phrase builders
    # ------------------------------------------------------------------

    def _strength_phrase(self, bloom: int, dreyfus: int, evidences: list[str]) -> str:
        base = BLOOM_STRENGTH_PHRASES.get(bloom, BLOOM_STRENGTH_PHRASES[2])

        if dreyfus >= 4:
            suffix = " com visão estratégica e experiência consolidada"
        elif dreyfus == 3:
            suffix = " com boa autonomia operacional"
        elif dreyfus == 2:
            suffix = " com capacidade crescente de aplicação prática"
        else:
            suffix = " e demonstra potencial claro de desenvolvimento"

        phrase = f"Você {base}{suffix}."

        if evidences:
            ev = evidences[0][:110].rstrip(".,!?")
            phrase += f" Isso ficou evidente quando {ev}."

        return phrase

    def _development_phrase(self, bloom: int, dreyfus: int, expected: int) -> str:
        if bloom >= expected:
            next_b = min(bloom + 1, 6)
            dev = BLOOM_DEVELOPMENT_PHRASES.get(next_b, BLOOM_DEVELOPMENT_PHRASES[6])
            return f"Para continuar evoluindo, explore como {dev}."
        else:
            dev = BLOOM_DEVELOPMENT_PHRASES.get(bloom + 1, BLOOM_DEVELOPMENT_PHRASES[3])
            dreyfus_tip = DREYFUS_DEVELOPMENT_PHRASES.get(dreyfus, DREYFUS_DEVELOPMENT_PHRASES[2])
            return f"Uma área de crescimento é {dev}. Em paralelo, {dreyfus_tip} pode acelerar essa evolução."

    def _suggestion(self, competency: str, bloom: int) -> str:
        table = PRACTICAL_SUGGESTIONS.get(competency, PRACTICAL_SUGGESTIONS["_communication"])
        bloom_key = min(max(bloom, 1), 6)
        return table.get(bloom_key, table[3])

    # ------------------------------------------------------------------
    # Intros / closings
    # ------------------------------------------------------------------

    def _intro(self, first_name: str, job_title: str, tone_cfg: dict) -> str:
        opener = tone_cfg["intro_opener"]
        return (
            f"Olá, {first_name}! {opener}\n\n"
            f"Preparamos este feedback sobre sua participação na triagem para a vaga de {job_title}. "
            f"Nosso objetivo é compartilhar observações construtivas sobre sua performance — "
            f"não para julgar, mas para apoiar o seu desenvolvimento profissional continuado."
        )

    def _closing(self, first_name: str) -> str:
        return (
            f"Independentemente do resultado deste processo, {first_name}, esperamos que este "
            f"feedback seja útil para sua jornada. Continue se desenvolvendo — cada experiência "
            f"é um passo importante na construção de uma carreira sólida.\n\n"
            f"Se você tiver dúvidas sobre este feedback ou quiser solicitar uma revisão humana, "
            f"basta responder diretamente a este e-mail."
        )

    # ------------------------------------------------------------------
    # Text renderers
    # ------------------------------------------------------------------

    def _plain_text(self, r: dict) -> str:
        parts = [r["intro"], ""]
        for d in r["dimensions"]:
            parts += [
                f"## {d['title']}",
                f"✅ Ponto forte: {d['strength']}",
                f"🌱 Desenvolvimento: {d['development']}",
                f"💡 Sugestão prática: {d['suggestion']}",
                "",
            ]
        parts += [r["closing"], "", "---",
                  "Este feedback foi gerado por IA e pode ser revisado mediante solicitação."]
        return "\n".join(parts)

    def _whatsapp_text(self, r: dict) -> str:
        """Condensed (~600 chars) para WhatsApp — referencia o e-mail para detalhes."""
        lines = [
            f"Olá, {r['first_name']}! 👋",
            "",
            f"Aqui está um resumo do seu feedback da triagem para *{r['job_title']}*:",
            "",
        ]
        for d in r["dimensions"][:3]:
            short_strength = d["strength"][:90].rstrip(".,") + ("…" if len(d["strength"]) > 90 else ".")
            lines += [f"*{d['icon']} {d['title']}*", short_strength, ""]

        lines += [
            "O feedback completo foi enviado para o seu e-mail. 📧",
            "",
            "_Feedback gerado por IA · Solicite revisão humana pelo e-mail recebido._",
        ]
        return "\n".join(lines)

    def _chat_text(self, r: dict) -> str:
        """Markdown para última mensagem da LIA no chat web."""
        lines = [
            "---",
            f"**📋 Feedback da sua triagem — {r['job_title']}**",
            "",
            r["intro"].split("\n\n")[1] if "\n\n" in r["intro"] else "",
            "",
        ]
        for d in r["dimensions"]:
            lines += [
                f"**{d['icon']} {d['title']}**",
                f"*Ponto forte:* {d['strength']}",
                f"*Para desenvolver:* {d['development']}",
                "",
            ]
        lines += [
            "---",
            "_Feedback gerado por IA · O relatório completo foi enviado para seu e-mail._",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _avg(scores: list[dict], key: str, default: int = 2) -> int:
        vals = [s[key] for s in scores if key in s]
        return round(sum(vals) / len(vals)) if vals else default


# Module-level singleton
_feedback_generator: WSIFeedbackGenerator | None = None


def get_feedback_generator() -> WSIFeedbackGenerator:
    global _feedback_generator
    if _feedback_generator is None:
        _feedback_generator = WSIFeedbackGenerator()
    return _feedback_generator
