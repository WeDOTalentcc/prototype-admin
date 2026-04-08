"""
Stages 7-10 — Publication, candidate search, calibration, and active search handlers.
"""
import logging

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


def handle_candidate_search() -> str:
    """Handle stage 8: candidate search initiation."""
    return """**Busca de Candidatos**

Agora que a vaga está ativa, vou buscar candidatos compatíveis.

🔍 Buscando na base de talentos...
🔍 Analisando perfis do LinkedIn...
🔍 Verificando candidatos similares...

Em breve você verá os primeiros candidatos sugeridos."""


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
