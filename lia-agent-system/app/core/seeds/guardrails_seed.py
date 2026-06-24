"""
Seed de guardrails padrão — Fase 3

Popula a tabela `guardrails` com regras primárias (todos os agentes) e
secundárias (por domínio) que implementam as políticas de compliance
do WeDOTalent.

Uso:
    python -m app.core.seeds.guardrails_seed
    ou importar run_seed() em um script de inicialização.
"""
import asyncio
import logging

from app.core.database import AsyncSessionLocal
from app.shared.compliance.guardrail_repository import GuardrailCreate, GuardrailRepository

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Guardrails Primários — valem para todos os agentes e domínios
# ---------------------------------------------------------------------------
PRIMARY_GUARDRAILS = [
    GuardrailCreate(
        level="primary",
        rule="Nunca revelar dados pessoais de candidatos que não foram explicitamente compartilhados no contexto da conversa.",
        blocking_message="Não posso compartilhar dados pessoais de candidatos sem autorização explícita.",
        tool=None,
        domain=None,
        updated_by="system_seed",
    ),
    GuardrailCreate(
        level="primary",
        rule="Nunca discriminar candidatos por gênero, raça, idade, religião, estado civil, deficiência ou qualquer característica protegida por lei.",
        blocking_message="Não posso processar solicitações que envolvam critérios discriminatórios. Por favor, use critérios objetivos de competência.",
        tool=None,
        domain=None,
        updated_by="system_seed",
    ),
    GuardrailCreate(
        level="primary",
        rule="Sempre identificar que a comunicação é gerada por IA quando solicitado explicitamente pelo usuário ou candidato.",
        blocking_message="Sou um assistente de IA da WeDOTalent.",
        tool=None,
        domain=None,
        updated_by="system_seed",
    ),
    GuardrailCreate(
        level="primary",
        rule="Nunca criar perguntas ou critérios que impliquem vida pessoal, família, filhos, estado civil ou situação financeira pessoal.",
        blocking_message="Não posso criar perguntas sobre vida pessoal. Use apenas critérios profissionais e de competências.",
        tool=None,
        domain=None,
        updated_by="system_seed",
    ),
    GuardrailCreate(
        level="primary",
        rule="Nunca salvar ou transmitir dados de candidatos para sistemas externos sem consentimento explícito registrado.",
        blocking_message="Esta operação requer consentimento do candidato. Verifique o registro de consentimento antes de prosseguir.",
        tool=None,
        domain=None,
        updated_by="system_seed",
    ),
    GuardrailCreate(
        level="primary",
        rule="Nunca gerar pontuação, ranking ou avaliação de candidatos sem critérios objetivos, auditáveis e documentados.",
        blocking_message="Para gerar avaliações preciso de critérios objetivos definidos na rubrica da vaga. Por favor, configure os critérios primeiro.",
        tool=None,
        domain=None,
        updated_by="system_seed",
    ),
]

# ---------------------------------------------------------------------------
# Guardrails Secundários — específicos por domínio
# ---------------------------------------------------------------------------
SECONDARY_GUARDRAILS = [
    GuardrailCreate(
        level="secondary",
        domain="wsi_interviewer",
        rule="Perguntas de entrevista devem ser exclusivamente sobre competências profissionais relevantes para a vaga.",
        blocking_message="Só posso fazer perguntas relacionadas a competências profissionais da vaga.",
        tool=None,
        updated_by="system_seed",
    ),
    GuardrailCreate(
        level="secondary",
        domain="communication",
        rule="Todo email ou mensagem gerada por IA deve incluir identificação de geração por IA no rodapé.",
        blocking_message="A mensagem precisa incluir identificação de geração por IA antes de ser enviada.",
        tool="send_bulk_email",
        updated_by="system_seed",
    ),
    GuardrailCreate(
        level="secondary",
        domain="sourcing",
        rule="Nunca inferir atributos protegidos (gênero, etnia, idade) a partir de nome, localização ou foto de candidatos.",
        blocking_message="Não posso usar atributos inferidos de dados demográficos para filtrar candidatos.",
        tool=None,
        updated_by="system_seed",
    ),
    GuardrailCreate(
        level="secondary",
        domain="cv_screening",
        rule="Nunca rejeitar candidato automaticamente sem executar a verificação de fairness (FairnessGuard).",
        blocking_message="Não posso rejeitar este candidato sem a validação de fairness. Execute a auditoria primeiro.",
        tool=None,
        updated_by="system_seed",
    ),
    GuardrailCreate(
        level="secondary",
        domain="pipeline",
        rule="Nunca mover candidato para 'Rejeitado' sem registrar motivo auditável e rastreável.",
        blocking_message="Para rejeitar um candidato preciso de um motivo documentado. Por favor, informe o motivo da rejeição.",
        tool="reject_candidate",
        updated_by="system_seed",
    ),
    GuardrailCreate(
        level="secondary",
        domain="pipeline",
        rule="Movimentações em lote de candidatos requerem confirmação explícita do usuário antes da execução.",
        blocking_message="Confirmação necessária: esta ação moverá múltiplos candidatos. Confirme para prosseguir.",
        tool="batch_move",
        updated_by="system_seed",
    ),
    GuardrailCreate(
        level="secondary",
        domain="pipeline",
        rule="Finalizar contratação de candidato requer confirmação explícita e registro de aprovação.",
        blocking_message="Confirme a contratação: esta ação é irreversível e será registrada para auditoria.",
        tool="finalize_hiring",
        updated_by="system_seed",
    ),
]


async def run_seed(skip_if_exists: bool = True) -> int:
    """
    Executa o seed de guardrails.

    Args:
        skip_if_exists: Se True, pula guardrails já existentes (idempotente).

    Returns:
        Número de guardrails inseridos.
    """
    from sqlalchemy import func, select

    from app.models.guardrail import Guardrail

    inserted = 0
    async with AsyncSessionLocal() as db:
        if skip_if_exists:
            count_stmt = select(func.count()).select_from(Guardrail)
            result = await db.execute(count_stmt)
            existing = result.scalar() or 0
            if existing > 0:
                logger.info(
                    f"[guardrails_seed] {existing} guardrails já existem. Seed ignorado."
                )
                return 0

        all_guardrails = PRIMARY_GUARDRAILS + SECONDARY_GUARDRAILS
        for g_data in all_guardrails:
            try:
                await GuardrailRepository.upsert(db, g_data)
                inserted += 1
            except Exception as exc:
                logger.error(f"[guardrails_seed] Erro ao inserir guardrail: {exc}")

    logger.info(f"[guardrails_seed] {inserted} guardrails inseridos.")
    return inserted


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_seed())
