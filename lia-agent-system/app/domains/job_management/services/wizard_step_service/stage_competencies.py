"""
Stage 3 — Competencies handler for the wizard step service.
"""
import logging

logger = logging.getLogger(__name__)


async def handle_competencies(
    job_draft: dict,
    benchmarks: dict,
    suggestions_data: dict,
) -> tuple[str, dict]:
    """
    Handle stage 3: competencies suggestion.

    Returns:
        (lia_message, suggestions_data)
    """
    skills_benchmark = benchmarks.get("suggested_skills", {})
    skills_list = skills_benchmark.get("skills", [])

    skills_suggestion = ""
    if skills_list:
        tech_skills = [s["skill"] for s in skills_list if s.get("category") == "Técnico"][:6]
        if tech_skills:
            skills_suggestion = (
                "\n\n🎯 **Skills sugeridas** (baseado em vagas similares):\n• "
                + "\n• ".join(tech_skills)
            )

    lia_message = f"""Excelente! Agora vamos às **Competências**. 🎯
{skills_suggestion}

📊 **Fontes da minha análise:**
• Histórico de vagas similares na sua empresa
• Benchmark de mercado por área/senioridade
• Skills identificadas na descrição original

**Competências Técnicas:**
Sugiro as skills abaixo. Me diga quais ajustes deseja e eu aplico. Para cada skill, defina:
• **Nível** (Básico → Expert)
• **Peso** (1-5★) - impacto na Nota LIA
• **Obrigatório/Desejável**

**Competências Comportamentais:**
Aspectos sugeridos para este perfil:
• Comunicação • Trabalho em equipe
• Resolução de problemas • Proatividade

💡 *Recomendação: 5-8 competências técnicas e 3-5 comportamentais para triagem equilibrada.*

---

✅ **Próximo passo:** Após confirmar, vamos gerar as **perguntas de triagem WSI** baseadas nas competências selecionadas.

❓ *Quer que eu sugira competências específicas para este perfil? Pergunte!*"""

    suggestions_data["suggested_skills"] = skills_list

    return lia_message, suggestions_data
