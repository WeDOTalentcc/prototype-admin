"""
Stages 7-10 — Publication, candidate search, calibration, and active search handlers.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def handle_pre_publish() -> str:
    """Handle stage 7: platform selection for publication."""
    return """**Plataformas de Publicação**

Escolha onde publicar sua vaga:

🔗 **LinkedIn** - Maior rede profissional
📋 **Indeed** - Alto volume de candidatos
🌐 **Página de Carreiras** - Candidatos qualificados
📱 **WhatsApp** - Divulgação rápida

Selecione as plataformas desejadas e clique em "Publicar Vaga"."""


def handle_candidate_search(suggestions_data: Optional[dict] = None) -> tuple:
    """Handle stage 8: candidate search initiation.

    C.3.3: Sets calibration_offered flag and appends calibration offer to message.

    Returns:
        (lia_message, suggestions_data)
    """
    if suggestions_data is None:
        suggestions_data = {}

    lia_message = """**Busca de Candidatos**

Agora que a vaga está ativa, vou buscar candidatos compatíveis.

🔍 Buscando na base de talentos...
🔍 Analisando perfis do LinkedIn...
🔍 Verificando candidatos similares...

Em breve você verá os primeiros candidatos sugeridos."""

    # C.3.3: Calibration offer after publication
    lia_message += (
        "\n\n✅ Vaga publicada! Quer calibrar a busca agora "
        "(te mostro candidatos para dar 👍/👎) ou prefere fazer isso depois no funil de talentos?"
    )
    suggestions_data.setdefault('stage_meta', {})['calibration_offered'] = True

    return lia_message, suggestions_data


def handle_calibration() -> str:
    """Handle stage 9: candidate calibration."""
    return """**Calibração de Candidatos**

Vou apresentar alguns candidatos para você avaliar.
Sua avaliação ajuda a LIA a entender melhor o perfil ideal.

Para cada candidato:
• ✅ Aprovar - Perfil adequado
• ❌ Reprovar - Não adequado
• 💬 Comentar - Adicionar observações

Vamos começar?"""


def handle_active_search() -> str:
    """Handle stage 10: active search with refined criteria."""
    return """**Busca Ativa**

Com base na calibração, vou intensificar a busca por candidatos ideais.

🎯 Critérios refinados aplicados
📧 Outreach automatizado ativo
📊 Monitorando respostas

Você será notificado quando houver novos candidatos compatíveis."""
