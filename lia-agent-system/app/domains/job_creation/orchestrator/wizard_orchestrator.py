"""Wizard Orchestrator — tool-calling agent loop (cérebro conversacional).

Strangler-fig migration (decisão Paulo 2026-05-31): substitui o pipeline
LangGraph rígido + 3 classifiers desconectados (supervisor / gate / meta-helper)
por UM cérebro state-aware por turno que vê a ficha viva completa, decide a
ação E gera a resposta, chamando as capacidades determinísticas
(:mod:`wizard_tools`) como tools.

## Por que isto resolve a "burrice"

O fluxo legado tinha 3 LLMs com visão de buraco de fechadura, nenhum vendo o
estado completo, com allowlists travadas por stage (impossível corrigir um
campo anterior mid-fluxo) e respostas canned para 90% dos turnos. Aqui:

  - **Um cérebro, estado completo**: o system prompt carrega a ficha viva
    (campos preenchidos/faltantes, JD, competências, modo). O modelo responde
    "faltam X e Y" com precisão, não spiel genérico.
  - **Navegação não-linear**: o modelo pode chamar ``set_job_fields`` para
    corrigir a senioridade a qualquer momento — não há jaula de stage.
  - **Determinismo onde importa**: multi-tenancy, validação e (increment 2)
    fairness/LGPD vivem nas tools, não na geração livre do LLM.

## Segurança

  - **FairnessGuard L1** roda sobre a mensagem do recrutador ANTES do loop.
  - **Multi-tenancy**: ``ToolContext.company_id`` (JWT) é a única fonte; tools
    rejeitam ``company_id`` vindo de args da LLM.
  - **Guard de iterações**: ``max_iterations`` impede loop infinito de tool_use.
  - **Fail-soft**: erro de tool vira ``tool_result`` com instrução de correção
    realimentada ao modelo (não derruba o turno). Erro de LLM → reply de
    fallback (nunca silent — loga + telemetria).

## Cliente LLM injetável

``process_turn(..., llm_client=...)`` aceita qualquer objeto com
``.messages.create(**kwargs)`` retornando ``.content`` (lista de blocks com
``.type`` ∈ {text, tool_use}) e ``.stop_reason``. Produção usa o SDK
``anthropic.Anthropic``; testes injetam um fake scriptado. Sem flag/env no
core — a decisão de ligar vive no caller (``LIA_WIZARD_ORCHESTRATOR``).
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Optional

from app.shared.llm_models import CANONICAL_SONNET_MODEL

from app.domains.job_creation.orchestrator.wizard_tools import (
    ToolContext,
    WizardTool,
    build_tool_registry,
)

logger = logging.getLogger(__name__)


# Anti-silent-degradation sensor (harness, 2026-06-05): canary counter para o
# caso em que o LLM produz ZERO texto em TODAS as iterações do turno e o reply
# cai no fallback genérico ("Certo! Como deseja seguir?"). Esse era um defeito
# INVISÍVEL — o turno respondia HTTP 200 com texto plausível enquanto o painel
# não abria e o recrutador via uma resposta sem sentido (custou um debug longo).
# Agora a anomalia é OBSERVÁVEL: WARNING sempre + (quando prometheus_client está
# disponível) counter ``wizard_empty_reply_fallback_total`` para alarme.
# Mesmo pattern canonical de lia_voice_wsi_persist_total (wsi_pipeline.py).
try:
    from prometheus_client import REGISTRY as _PROM_REGISTRY
    from prometheus_client import Counter as _PromCounter

    _EMPTY_REPLY_METRIC_NAME = "wizard_empty_reply_fallback_total"
    _existing_empty_reply = getattr(
        _PROM_REGISTRY, "_names_to_collectors", {}
    ).get(_EMPTY_REPLY_METRIC_NAME)
    if _existing_empty_reply is not None:
        _EMPTY_REPLY_COUNTER = _existing_empty_reply
    else:
        _EMPTY_REPLY_COUNTER = _PromCounter(
            _EMPTY_REPLY_METRIC_NAME,
            "WizardOrchestrator turns whose LLM produced no text across all "
            "iterations and fell back to the generic reply (harness 2026-06-05).",
        )
    _EMPTY_REPLY_METRICS_AVAILABLE = True
except (ImportError, ValueError):  # pragma: no cover — prometheus opcional
    _EMPTY_REPLY_COUNTER = None
    _EMPTY_REPLY_METRICS_AVAILABLE = False


_DEFAULT_MODEL = os.environ.get("LIA_WIZARD_ORCHESTRATOR_MODEL", CANONICAL_SONNET_MODEL)


def _get_timeout_s() -> float:
    try:
        return float(os.environ.get("LIA_WIZARD_ORCHESTRATOR_TIMEOUT_S", "20"))
    except (TypeError, ValueError):
        return 20.0


def _get_max_iterations() -> int:
    try:
        return max(1, int(os.environ.get("LIA_WIZARD_ORCHESTRATOR_MAX_ITERS", "6")))
    except (TypeError, ValueError):
        return 6


_SYSTEM_PROMPT_BASE = (
    "Você é a LIA, assistente de IA de recrutamento da WeDoTalent, conduzindo "
    "a criação de uma vaga em uma conversa natural com o recrutador.\n\n"
    "## Seu objetivo\n"
    "Coletar e confirmar as informações da vaga (título, senioridade, modelo de "
    "trabalho, departamento, gestor, competências, modo de triagem), gerar uma "
    "descrição de qualidade e preparar a vaga para publicação — de forma "
    "conversacional e inteligente, não como um formulário rígido.\n\n"
    "## Como agir\n"
    "- VEJA o estado real da vaga (ficha viva) que receberá abaixo. Responda com "
    "precisão: se o recrutador perguntar 'o que falta?', liste exatamente os "
    "campos faltantes da ficha.\n"
    "- Use as TOOLS para registrar dados (set_job_fields), definir modo "
    "(set_screening_mode), confirmar competências (confirm_competencies) e "
    "consultar status (get_wizard_status). Chame a tool assim que o recrutador "
    "fornecer um dado — não apenas reconheça verbalmente.\n"
    "- O recrutador pode CORRIGIR algo a qualquer momento (ex.: mudar a "
    "senioridade depois de já ter dado o título). Chame set_job_fields para "
    "atualizar — nunca diga que não pode.\n"
    "- Salário: etapa OBRIGATÓRIA e PROATIVA. Assim que os campos básicos "
    "estiverem preenchidos (título, senioridade, modelo, departamento, "
    "gestor, contrato) e ANTES de avançar para competências/triagem, OFEREÇA "
    "proativamente a faixa de mercado chamando suggest_salary (sempre informe "
    "a fonte). NÃO pule essa etapa nem a adie para depois da triagem. Se o "
    "recrutador informar/ajustar valores, use set_salary; se ele optar por "
    "seguir SEM divulgar a faixa, registre com set_salary(decline_to_disclose"
    "=true). Só trate o salário como resolvido após uma dessas ações.\n"
    "- Benefícios e remuneração variável: após confirmar o salário, OFEREÇA "
    "proativamente os benefícios chamando suggest_benefits e também chame "
    "suggest_variable_compensation para oferecer remuneração variável ao "
    "recrutador. Ambos buscam o catálogo da empresa e "
    "preenchem a vaga automaticamente — o recrutador só confirma ou remove "
    "itens. Se o catálogo estiver vazio, oriente o recrutador a informar "
    "manualmente via chat.\n"
    "- Vaga afirmativa: se o recrutador mencionar ação afirmativa, PcD, "
    "mulheres, pessoas negras, LGBTQIA+, 50+, indígenas, refugiados, ou "
    "similarés, OU se o state já tiver is_affirmative=True (detectado pelo "
    "intake via NLP), chame set_affirmative_fields com o critério correto. "
    "Isso ativa o FairnessGuard na triagem e persiste os campos no publish. "
    "Mostre um resumo do que foi configurado (critério + documentação exigida "
    "se aplicável). NÃO afirme que configurou sem ter chamado a tool.\n"
    "- Perguntas de elegibilidade (eliminatorias): quando o stage for 'eligibility' ou o recrutador mencionar requisitos que BLOQUEIAM candidatos (CNH, presencial, PcD, documentacao, viagens), chame suggest_eligibility_templates PROATIVAMENTE. Apresente as opcoes e para cada aprovado chame apply_eligibility_template (necessario o template_id do suggest). Para customizadas use create_custom_eligibility_template + apply_eligibility_template. NUNCA invente texto de pergunta eliminatoria sem ter chamado a tool. Se o recrutador quiser avancar SEM nenhum criterio de elegibilidade, EXPLIQUE que nenhuma pergunta eliminatoria sera aplicada aos candidatos e pergunte se confirma. Ao confirmar, chame confirm_skip_eligibility. Nao adiante para outros stages.\n"
    "- Banco de perguntas: quando receber mensagem com o padr\u00e3o "
    "'Adicionar do banco pergunta id=UUID', extraia o UUID EXATAMENTE como est\u00e1 "
    "(sem modificar nenhum caractere) e chame add_bank_question com question_id=UUID. "
    "Confirme qual pergunta foi adicionada pelo texto retornado pela tool.\n"
    "- Calibra\u00e7\u00e3o de candidatos: quando receber mensagem com o padr\u00e3o "
    "'[calibration_action candidate_id=ID signal=SIGNAL]', extraia candidate_id e signal "
    "EXATAMENTE como est\u00e3o e chame calibration_action(candidate_id=ID, signal=SIGNAL). "
    "signal: like=aprovar, dislike=rejeitar, skip=pular. "
    "Ap\u00f3s chamar, relate o progresso (sinais: N/threshold). "
    "Quando receber '[calibration_complete]', chame advance_calibration. "
    "N\u00e3o afirme que avan\u00e7ou sem ter chamado advance_calibration.\n"
    "- Navegação: se o recrutador pedir para ir à página de vagas ou abrir a "
    "vaga, chame navigate_to_jobs (você CONSEGUE — não diga que não consegue). "
    "Se pedir 'chat full', 'tela cheia', 'chat dedicado', 'chat completo', "
    "chame open_fullscreen_chat (você CONSEGUE — não diga que não consegue).\n"
    "- Se o recrutador mencionar IDIOMAS (ex.: 'inglês avançado'), registre com "
    "confirm_languages (idioma + nível) — senão o dado se perde.\n"
    "- Junto com as competências, pergunte as RESPONSABILIDADES da vaga e "
    "confirme com confirm_responsibilities. NÃO é obrigatório: se o recrutador "
    "não tiver, sugira algumas com base no cargo e confirme, ou siga sem (a "
    "descrição gera responsabilidades para ele revisar).\n"
    "- Confirme as competências ANTES de tratar a descrição como final. Para "
    "ADICIONAR ou REMOVER competências específicas, chame update_competencies "
    "com apenas os deltas (add_technical/remove_technical/add_behavioral/"
    "remove_behavioral) — é mais confiável que reenviar a lista inteira. Use "
    "confirm_competencies apenas para definir a lista completa do zero.\n"
    "- Fluxo da descrição: gere com enrich_job_description; quando o recrutador "
    "aprovar ('aprovo', 'pode seguir'), chame approve_job_description.\n"
    "- Triagem WSI: depois da descrição aprovada, gere as perguntas de triagem "
    "SEMPRE chamando generate_wsi_questions (metodologia canônica CBI + Bloom + "
    "Dreyfus + Big Five + fairness, dimensionada pelo modo). **NUNCA escreva, "
    "liste ou enumere o texto das perguntas você mesmo no chat** — as perguntas "
    "SÓ existem (e aparecem como card interativo DIRETAMENTE NO CHAT, logo acima "
    "do campo de mensagem) se generate_wsi_questions foi chamada e retornou sucesso. "
    "Depois de chamá-la, apenas RESUMA (quantas técnicas/comportamentais, metodologia) "
    "— as perguntas aparecem automaticamente como card inline no chat para revisão. "
    "NAO existe painel lateral separado para perguntas WSI — tudo aparece no chat. "
    "Jamais redija o conteúdo das perguntas no texto da sua resposta. Ajustes: regenerar "
    "tudo (regenerate_wsi_questions), remover (remove_wsi_question), reescrever "
    "(edit_wsi_question), adicionar (add_wsi_question). Quando ele aprovar, chame "
    "approve_wsi_questions. Só então publish_job (com confirm=true).\n"
    "- NUNCA invente dados da vaga, da empresa ou do candidato.\n"
    "- NUNCA tome ação irreversível (publicar) sem confirmação explícita.\n\n"
    "## REGRA CRÍTICA — não alucinar ações\n"
    "NUNCA afirme que uma ação aconteceu (vaga publicada, descrição gerada, "
    "email registrado, competências salvas, PERGUNTAS DE TRIAGEM GERADAS) sem "
    "ter chamado a TOOL correspondente E recebido sucesso nela. Listar o TEXTO "
    "de perguntas de triagem no chat sem que generate_wsi_questions tenha rodado "
    "com sucesso É alucinação — as perguntas vêm da metodologia canônica, não da "
    "sua redação. Se a tool não foi chamada, falhou, "
    "ou um pré-requisito falta, diga a verdade sobre o estado atual e qual é o "
    "próximo passo real — jamais finja sucesso. Não diga 'publicada com sucesso' "
    "a menos que publish_job tenha retornado um job_id.\n\n"
    "## REGRA ABSOLUTA \u2014 ficha viva \xe9 autoritativa (nunca reiniciar coleta)\n"
    "A se\xe7\xe3o 'Estado real da vaga (ficha viva)' abaixo \xe9 a "
    "\xdaNICA fonte de verdade sobre o progresso desta vaga. "
    "LEIA-A antes de responder. Se 'Campos preenchidos' listar "
    "qualquer campo, voc\xea J\xc1 tem esse dado \u2014 "
    "n\xe3o pe\xe7a novamente, n\xe3o reinicie a coleta, "
    "NUNCA diga 'vamos come\xe7ar do zero'. "
    "Continue sempre do pr\xd3ximo campo faltante. A ficha \xe9 "
    "a \xdaNICA fonte de verdade.\n\n"
    "## Painel lateral (ficha viva)\n"
    "O painel lateral inicia MINIMIZADO como um card acima do campo de "
    "mensagem — o recrutador expande/minimiza quando quiser, e a escolha "
    "dele prevalece. Você TAMBÉM pode controlá-lo por tools: open_panel "
    "(expandir) e close_panel (minimizar para o card).\n"
    "REGRAS OBRIGATÓRIAS para open_panel e close_panel:\n"
    "- NUNCA chame open_panel automaticamente no início do wizard nem "
    "durante coleta de dados (perguntas ao recrutador). O painel começa "
    "e permanece MINIMIZADO por padrão.\n"
    "- SÓ chame open_panel quando: (a) o recrutador EXPLICITAMENTE pedir "
    "para ver/expandir/abrir o painel (frases como 'pode abrir o painel', "
    "'mostra no painel', 'expande', 'quero ver a ficha'); OU (b) você "
    "acabou de gerar um artefato principal completo (JD com enrich_job_description "
    "bem-sucedida, ou perguntas WSI com generate_wsi_questions bem-sucedida) — "
    "nesses casos o recrutador precisa revisar o conteúdo no painel.\n"
    "- Exemplos PROIBIDOS: ❌ open_panel no 1º turno; ❌ open_panel ao fazer "
    "pergunta sobre título/senioridade/modelo; ❌ open_panel ao registrar um campo.\n"
    "- Use close_panel quando ele pedir 'fechar o painel' ou 'seguir só pelo chat'.\n"
    "- NUNCA afirme que abriu/fechou o painel sem ter chamado a tool e recebido "
    "sucesso (mentira de ação, igual fingir publicação).\n\n"
    "## Responsáveis pela vaga\n"
    "Após definir título e departamento, pergunte proativamente:\n"
    "- Nome e email do gestor da vaga (quem aprova e acompanha)\n"
    "- Nome e email do recrutador responsável (quem conduz o processo)\n"
    "Esses campos são importantes para briefings e notificações. Use "
    "`set_job_fields` com os campos: manager_name, manager_email, "
    "recruiter, recruiter_email.\n"
    "Se o recrutador mencionar um email e você vir '[EMAIL REMOVIDO]' "
    "(LGPD), o email já está registrado automaticamente — não insista.\n"
    "JAMAIS invente nomes ou emails de responsáveis. Se não foram informados, "
    "PERGUNTE.\n"
    "**ATENÇÃO: gestor ≠ recrutador.** Se o usuário diz 'eu sou o recrutador' "
    "ou 'a recrutadora é Maria', use campos `recruiter`/`recruiter_email`. "
    "Campos `manager_name`/`manager_email` são APENAS para o gestor/hiring "
    "manager (quem aprova a vaga, não quem conduz o processo).\n"
    "Após gestor e recrutador, pergunte se há outros envolvidos no processo "
    "(ex: HRBP, líder de área, comitê de contratação, entrevistadores). "
    "Se sim, use `set_stakeholders` para registrá-los. Se não, prossiga.\n\n"
    "- Respostas curtas, calorosas e objetivas em PT-BR. Termine com um próximo "
    "passo claro ou uma pergunta de continuidade.\n"
    "- NUNCA repita literalmente sua última resposta; consulte o histórico.\n\n"
    "## Stage done (vaga criada)\n"
    "Quando a vaga foi publicada e o stage é 'done', o recrutador pode:\n"
    "- Clicar em 'Ir para a vaga' para abrir a vaga diretamente.\n"
    "- Clicar em 'Fechar wizard' para encerrar o assistente de criação de vaga.\n"
    "Você pode mencionar que pode navegar livremente pela plataforma após a publicação. "
    "NÃO afirme que vai fechar nenhum painel lateral — não há painel lateral neste modo."
    "\n\n"
    "## Briefing para o gestor\n"
    "Após publicar a vaga com sucesso, ofereça proativamente ao recrutador: "
    "'Deseja que eu envie um briefing executivo para o gestor da vaga?' "
    "Use a tool `send_manager_briefing` para isso. Se o e-mail do gestor "
    "foi informado no intake, um briefing básico já foi enviado automaticamente "
    "— ofereça enviar a versão completa com contexto de triagem e cultura.\n"

    "\n\n"
    "## Valores can\u00f4nicos de triagem (NUNCA inventar)\n"
    "- Modo COMPACTO: 7 perguntas (5 t\u00e9cnicas + 2 comportamentais), ~15 min\n"
    "- Modo COMPLETO: 12 perguntas (8 t\u00e9cnicas + 4 comportamentais), ~25 min\n"
    "Estes s\u00e3o os \u00daNICOS valores. N\u00e3o cite n\u00fameros diferentes. Quando o "
    "recrutador perguntar sobre modos de triagem, use EXATAMENTE estes valores.\n"
    "- Prazo de triagem: default da empresa = 48h a partir da publicacao. "
    "Presets: 24h, 48h, 72h, 96h, 120h, 168h (7 dias). O recrutador pode "
    "ajustar livremente (12h-720h). Use set_screening_deadline para registrar.\n\n"
    "## Disciplina de tool-calling (INEGOCI\u00c1VEL)\n"
    "1. Quando o recrutador informar QUALQUER dado (t\u00edtulo, senioridade, modelo, "
    "departamento, gestor, contrato, local, etc.), chame set_job_fields "
    "IMEDIATAMENTE nesse turno \u2014 ANTES de responder textualmente.\n"
    "2. NUNCA cite benef\u00edcios, faixa salarial, ou compet\u00eancias sem ter chamado "
    "a tool correspondente (suggest_benefits, suggest_salary, suggest_competencies) "
    "e recebido o resultado. Inventar dados \u00e9 proibido.\n"
    "3. Se uma tool falhar, informe o erro ao recrutador e sugira alternativa "
    "(ex.: informar manualmente). NUNCA invente o que a tool teria retornado.\n\n"
    "## Auto-preenchimento proativo\n"
    "O contexto da empresa (miss\u00e3o, valores, cultura, stack tecnol\u00f3gico, benef\u00edcios, "
    "faixas salariais) est\u00e1 dispon\u00edvel na ficha viva abaixo. USE-O proativamente:\n"
    "- Sugira departamento/gestor se a empresa j\u00e1 tem essa informa\u00e7\u00e3o.\n- Ap\u00f3s definir o t\u00edtulo da vaga com set_job_fields, se o departamento ainda n\u00e3o foi informado, chame infer_department_from_title para tentar inferir automaticamente. Se a infer\u00eancia tiver confian\u00e7a alta, confirme com o recrutador; se n\u00e3o, pergunte entre os departamentos dispon\u00edveis.\n"
    "- Ao configurar benef\u00edcios, chame suggest_benefits para buscar o cat\u00e1logo "
    "da empresa \u2014 NUNCA invente um cat\u00e1logo.\n"
    "- Ao sugerir sal\u00e1rio, chame suggest_salary \u2014 NUNCA invente faixa.\n\n"
    "## Formatação de resposta — cards inline\n"
    "Quando uma tool produz dados estruturados (set_job_fields, enrich_job_description, "
    "confirm_competencies, generate_wsi_questions, suggest_salary, suggest_benefits, "
    "suggest_variable_compensation), esses dados aparecem AUTOMATICAMENTE como cards "
    "enriquecidos inline no chat como cards interativos. O recrutador já vê o resultado "
    "visualmente. Portanto:\n"
    "- NUNCA repita os dados da tool como tabela markdown, lista de bullets, ou "
    "bloco de código na sua resposta textual. Isso duplica a informação.\n"
    "- Em vez disso, RESUMA brevemente o que aconteceu (ex.: 'Registrei o título e a "
    "senioridade. O card acima mostra a ficha atualizada.') e faça a pergunta de "
    "continuidade.\n"
    "- Para competências: diga quantas técnicas/comportamentais, NÃO liste cada uma.\n"
    "- Para JD: diga o score e se ficou boa, NÃO reproduza o texto da descrição.\n"
    "- Para salário/benefícios: confirme o que foi aplicado em uma frase, NÃO liste "
    "o catálogo inteiro.\n"
    "- Exceção: se o recrutador PEDIR explicitamente para ver o conteúdo no chat "
    "(ex.: 'me mostra as competências aqui'), aí sim liste — mas prefira sugerir "
    "que ele veja no card inline do chat.\n\n"
    "## Consultas sobre vagas existentes\n"
    "Quando o recrutador perguntar sobre vagas existentes da empresa "
    "(ex.: quantas vagas temos, temos algo parecido, me mostra as vagas "
    "ativas), use list_company_jobs para consultar o banco de dados REAL. "
    "NUNCA invente vagas. Apos responder a consulta, SEMPRE retome o fluxo "
    "de criacao da vaga atual: relembre onde parou (consulte a ficha viva) "
    "e faca a proxima pergunta ao recrutador.\n\n"
    "## Tokens de mascara\u00e7\u00e3o PII\n"
    "Se voc\u00ea vir tokens como [EMAIL REMOVIDO], [CPF REMOVIDO], [TELEFONE REMOVIDO], "
    "[PERSON REMOVIDO] no texto ou hist\u00f3rico, NUNCA os reproduza na sua resposta. "
    "Esses s\u00e3o marcadores internos de privacidade. Se precisar referir-se ao dado, "
    "consulte a ficha viva (parsed_manager_email, parsed_manager_name, etc.)."
)


@dataclass
class OrchestratorResult:
    """Resultado de um turno do orquestrador."""

    reply: str
    state_updates: dict[str, Any] = field(default_factory=dict)
    fairness_blocked: bool = False
    tool_calls: list[str] = field(default_factory=list)
    iterations: int = 0
    error: bool = False
    response_blocks: list[dict] = field(default_factory=list)


def _emit_reasoning_sync(label: str) -> None:
    """Emite reasoning_step para o SSE sink atual (best-effort, thread-safe).

    wizard_orchestrator.process_turn() e sincrono e roda via asyncio.to_thread.
    asyncio.to_thread copia o contextvars.Context, entao _sse_frame_sink esta
    disponivel na thread via ContextVar. Porem o sink e uma coroutine: usamos
    run_coroutine_threadsafe para despachar ao event loop do caller.

    Falha silenciosa (try/except amplo): reasoning e best-effort, nunca
    interrompe o fluxo do wizard.
    """
    try:
        import asyncio as _asyncio
        from lia_agents_core.streaming_callback import _sse_frame_sink as _sink_cv
        _sink = _sink_cv.get(None)
        if _sink is None:
            return
        from app.shared.chat_event_serializer import serialize_reasoning_step
        _frame = serialize_reasoning_step(label=label, detail='')
        try:
            _loop = _asyncio.get_running_loop()
            _loop.create_task(_sink(_frame))
        except RuntimeError:
            try:
                _loop = _asyncio.get_event_loop()
                if _loop.is_running():
                    _asyncio.run_coroutine_threadsafe(_sink(_frame), _loop)
            except Exception:
                pass
    except Exception:
        pass


def _extract_history_messages(state: dict, n: int = 6) -> list[dict[str, Any]]:
    """Converte ``conversation_messages`` em mensagens Anthropic (últimas N).

    Formato canonical: ``[{"role": "user"|"assistant", "content": "..."}]``.
    Bounded e truncado por turno. Fail-open: state malformado → lista vazia.
    """
    try:
        msgs = state.get("conversation_messages") or []
    except Exception:
        return []
    out: list[dict[str, Any]] = []
    for m in list(msgs)[-n:]:
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "").strip().lower()
        content = str(m.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            continue
        out.append({"role": role, "content": content[:2000]})
    return out


class WizardOrchestrator:
    """Tool-calling agent state-aware para criação de vaga.

    Stateless e thread-safe (singleton via :func:`get_wizard_orchestrator`).
    Não persiste state — o caller passa o ``state`` atual e aplica os
    ``state_updates`` retornados.
    """

    def __init__(
        self,
        *,
        tools: Optional[tuple[WizardTool, ...]] = None,
        model: Optional[str] = None,
        service_tools_degraded: bool = False,
    ) -> None:
        self._registry = build_tool_registry(tools or ())
        self._model = model or _DEFAULT_MODEL
        self._service_tools_degraded = service_tools_degraded

    # ── LLM client (produção) ──────────────────────────────────────────
    @staticmethod
    def _resolve_anthropic_config(company_id: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        """Resolve (api_key, base_url) Anthropic POR-TENANT via LLM Factory (BYOK).

        Choose Your AI / BYOK: a chave do tenant (carregada do DB pelo
        TenantProviderRegistry) tem precedência sobre a chave global. Reusa os
        helpers canônicos da factory (mesma resolução do create_tracked_llm),
        então o cérebro de chat do orquestrador passa a honrar a chave/modelo
        per-tenant + proxy modelfarm. Fail-open para env global.
        """
        api_key = None
        base_url = None
        try:
            from app.shared.providers.llm_factory import (
                _resolve_provider_chain,
                _resolve_provider_api_key,
                _resolve_provider_base_url,
            )
            _, _, tenant_keys = _resolve_provider_chain(company_id or None)
            api_key = tenant_keys.get("claude") or _resolve_provider_api_key("claude")
            base_url = _resolve_provider_base_url("claude")
        except Exception as exc:  # noqa: BLE001 — fail-open ao env global
            logger.warning("[WizardOrchestrator] factory resolve failed (fallback env): %s", exc, exc_info=True)
        # Fallback ao env global se a factory não resolveu a chave.
        api_key = api_key or (
            os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY")
        )
        base_url = base_url or os.environ.get("AI_INTEGRATIONS_ANTHROPIC_BASE_URL")
        return api_key, base_url

    @classmethod
    def _build_anthropic_client(cls, company_id: Optional[str] = None) -> Optional[Any]:
        api_key, base_url = cls._resolve_anthropic_config(company_id)
        if not api_key:
            logger.warning("[WizardOrchestrator] no API key — cannot run")
            return None
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError:  # pragma: no cover — dep oficial
            return None
        kwargs: dict[str, Any] = {"api_key": api_key, "timeout": _get_timeout_s()}
        if base_url:
            kwargs["base_url"] = base_url
        try:
            return Anthropic(**kwargs)
        except Exception as exc:  # pragma: no cover — defensive
            logger.warning("[WizardOrchestrator] client init failed: %s", exc)
            return None

    def _build_system_prompt(self, state: dict, company_id: Optional[str] = None) -> str:
        try:
            from app.domains.job_creation.internal.utils import (
                _build_wizard_state_summary,
            )
            ficha = _build_wizard_state_summary(state)
        except Exception:  # noqa: BLE001
            ficha = "(estado não disponível)"
        tenant = str(state.get("tenant_context_snippet") or "").strip()
        tenant_block = (
            f"\n\n## Contexto da empresa\n{tenant[:600]}" if tenant else ""
        )
        # ADR-008: creation-modes capability is derived from the registries via
        # the shared view — the wizard no longer hardcodes (or omits) what it can
        # create. Same wording as SystemPromptBuilder + the meta helper, so the
        # answer to "consegue criar a partir de existente/template/zero?" is one
        # truth everywhere. Fail-open: no block if the view raises.
        modes_block = ""
        try:
            from app.shared.capabilities import (
                get_tenant_allowed_creation_actions,
                render_creation_modes_block,
            )
            # Task #1324: scope the claimed creation modes to this tenant's
            # permitted actions (tool_permissions.yaml). None → all-modes default.
            _allowed = (
                get_tenant_allowed_creation_actions(company_id)
                if company_id
                else None
            )
            rendered = render_creation_modes_block(allowed_actions=_allowed)
            if rendered and rendered.strip():
                modes_block = f"\n\n## Capacidades de criação\n{rendered}"
        except Exception as exc:  # noqa: BLE001  # REGRA-4-EXEMPT: bloco de modos é enriquecimento cosmético — falha não quebra o turn
            logger.warning("[WizardOrchestrator] creation modes block skipped: %s", type(exc).__name__, exc_info=True)
        # Recruiter identity — explicit so LLM never guesses the name
        recruiter_name = str(state.get("parsed_recruiter_name") or "").strip()
        recruiter_email = str(state.get("parsed_recruiter_email") or "").strip()
        recruiter_block = (
            f"\n\n## Recrutador desta sessão\nVocê está auxiliando **{recruiter_name}**."
            f" Use este nome ao se referir ao recrutador — nunca use outro nome."
            f" NÃO pergunte o nome nem o e-mail do recrutador nesta sessão — o recrutador logado é **{recruiter_name}** ({recruiter_email if recruiter_email else 'e-mail não disponível'})."
            if recruiter_name
            else ""
        )
        degraded_block = (
            "\n\n## ⚠️ Dados de serviço indisponíveis\n"
            "As ferramentas de acesso a departamentos, benefícios, gestores e competências não puderam ser carregadas nesta sessão. "
            "Informe ao recrutador que os dados não estão disponíveis e peça as informações manualmente quando necessário. "
            "NUNCA invente departamentos, gestores, benefícios ou competências."
            if self._service_tools_degraded else ""
        )
        return (
            f"{_SYSTEM_PROMPT_BASE}"
            f"{modes_block}\n\n"
            f"## Estado real da vaga (ficha viva)\n{ficha}"
            f"{tenant_block}"
            f"{recruiter_block}"
            f"{degraded_block}"
        )

    # ── Loop principal ─────────────────────────────────────────────────
    def process_turn(
        self,
        *,
        state: dict,
        user_message: str,
        ctx: ToolContext,
        llm_client: Optional[Any] = None,
    ) -> OrchestratorResult:
        """Processa um turno conversacional. Sync por contrato (SDK síncrono)."""
        msg = (user_message or "").strip()
        if not msg:
            return OrchestratorResult(
                reply="Não recebi sua mensagem. Pode repetir?", error=True
            )

        # 1) FairnessGuard L1 — viés explícito do recrutador é bloqueado.
        try:
            from app.shared.compliance.fairness_guard import FairnessGuard
            fg = FairnessGuard().check(msg)
            if fg.is_blocked:
                logger.warning(
                    "[WizardOrchestrator] FairnessGuard L1 BLOCK cat=%s",
                    fg.category,
                )
                return OrchestratorResult(
                    reply=fg.educational_message
                    or "Não posso seguir com critérios discriminatórios.",
                    fairness_blocked=True,
                )
        except Exception as exc:
            logger.error(
                "[WizardOrchestrator] FairnessGuard L1 exception — compliance check unavailable",
                exc_info=True,
            )
            return OrchestratorResult(
                reply=(
                    "Verificação de compliance temporariamente indisponível. "
                    "Por favor, tente novamente em instantes."
                ),
                error=True,
            )

        client = llm_client or self._build_anthropic_client(getattr(ctx, "company_id", None))
        if client is None:
            return OrchestratorResult(
                reply=(
                    "Estou com uma indisponibilidade técnica no momento. "
                    "Pode tentar de novo em instantes?"
                ),
                error=True,
            )

        system_prompt = self._build_system_prompt(
            state, company_id=getattr(ctx, "company_id", None)
        )
        tool_schemas = [t.anthropic_schema() for t in self._registry.values()]
        messages: list[dict[str, Any]] = _extract_history_messages(state)
        messages.append({"role": "user", "content": msg})

        # Working copy do state — tools veem mutações acumuladas dentro do loop.
        working_state = dict(state)
        working_state["_current_user_message"] = msg
        accumulated_updates: dict[str, Any] = {}
        tool_calls: list[str] = []
        # Acumula o texto emitido em QUALQUER iteração. O modelo pode emitir
        # texto + tool_use no MESMO turno (ex.: "Registrei o título" + chamada
        # a set_job_fields); sem acumular, esse texto se perderia quando o loop
        # executa a tool e continua, e a iteração seguinte (vazia) cairia no
        # fallback genérico. Ver TDD test_wizard_orchestrator_text_accumulation.
        accumulated_text: list[str] = []
        accumulated_response_blocks: list[dict] = []
        max_iters = _get_max_iterations()

        _emit_reasoning_sync('Analisando sua mensagem...')
        for iteration in range(1, max_iters + 1):
            try:
                response = client.messages.create(
                    model=self._model,
                    max_tokens=1024,
                    temperature=0.3,
                    system=system_prompt,
                    messages=messages,
                    tools=tool_schemas,
                )
            except Exception as exc:
                logger.info(
                    "[WizardOrchestrator] LLM call failed iter=%d: %s",
                    iteration, exc,
                )
                return OrchestratorResult(
                    reply=(
                        "Tive um problema ao processar agora. Pode repetir "
                        "ou reformular?"
                    ),
                    state_updates=accumulated_updates,
                    tool_calls=tool_calls,
                    iterations=iteration,
                    error=True,
                )

            content_blocks = list(getattr(response, "content", []) or [])
            tool_uses = [
                b for b in content_blocks
                if getattr(b, "type", None) == "tool_use"
            ]
            text_parts = [
                getattr(b, "text", "") or ""
                for b in content_blocks
                if getattr(b, "type", None) == "text"
            ]
            accumulated_text.extend(p for p in text_parts if p)

            # Sem tool_use → turno termina com a resposta textual do modelo.
            # Usa o texto ACUMULADO (não só o desta iteração): se o modelo
            # falou + chamou tool numa iteração anterior, esse texto persiste
            # mesmo que a iteração final venha vazia.
            if not tool_uses:
                reply = " ".join(accumulated_text).strip()
                if not reply:
                    # Anomalia: o LLM não emitiu texto em NENHUMA iteração.
                    # Mantemos o fallback genérico (UX), mas a tornamos
                    # OBSERVÁVEL — antes era um silent-degradation que custava
                    # debug longo (reply sem sentido, painel não abre).
                    _thread = "n/a"
                    try:
                        _thread = str(
                            (state or {}).get("thread_id")
                            or (state or {}).get("session_id")
                            or "n/a"
                        )
                    except Exception:  # noqa: BLE001 — telemetria nunca derruba
                        _thread = "n/a"
                    logger.warning(
                        "[WizardOrchestrator] empty-reply fallback: LLM produced "
                        "no text across %d iter(s) thread=%s tools_called=%s — "
                        "using generic fallback",
                        iteration, _thread, tool_calls,
                    )
                    if _EMPTY_REPLY_COUNTER is not None:
                        try:
                            _EMPTY_REPLY_COUNTER.inc()
                        except Exception:  # noqa: BLE001 — métrica é best-effort
                            pass
                return OrchestratorResult(
                    reply=reply or "Certo! Como deseja seguir?",
                    state_updates=accumulated_updates,
                    tool_calls=tool_calls,
                    iterations=iteration,
                    response_blocks=accumulated_response_blocks,
                )

            # Há tool_use → executa cada uma, monta tool_result, continua loop.
            assistant_content: list[dict[str, Any]] = []
            for b in content_blocks:
                btype = getattr(b, "type", None)
                if btype == "text":
                    assistant_content.append(
                        {"type": "text", "text": getattr(b, "text", "") or ""}
                    )
                elif btype == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": getattr(b, "id", ""),
                        "name": getattr(b, "name", ""),
                        "input": getattr(b, "input", {}) or {},
                    })
            messages.append({"role": "assistant", "content": assistant_content})

            tool_results: list[dict[str, Any]] = []
            for tu in tool_uses:
                name = getattr(tu, "name", "")
                tool_input = getattr(tu, "input", {}) or {}
                tu_id = getattr(tu, "id", "")
                tool_calls.append(name)
                _emit_reasoning_sync(f'Executando: {name}...')
                tool = self._registry.get(name)
                if tool is None:
                    result_text = (
                        f"Tool desconhecida: {name}. Tools disponíveis: "
                        f"{', '.join(sorted(self._registry))}."
                    )
                    is_error = True
                else:
                    try:
                        result = tool.handler(working_state, tool_input, ctx)
                        result_text = result.llm_message
                        is_error = result.error
                        if result.state_updates:
                            accumulated_updates.update(result.state_updates)
                            working_state.update(result.state_updates)
                        if name == "enrich_job_description" and not result.error:
                            _jd = (accumulated_updates or {}).get("jd_enriched") or {}
                            if _jd:
                                accumulated_response_blocks.append({
                                    "kind": "jd_preview",
                                    "block_id": f"jd_preview_{id(_jd)}",
                                    "role": "answer",
                                    "layout": "wide",
                                    "state": "ready",
                                    "title": _jd.get("titulo_padronizado", "Descrição da Vaga"),
                                    "body": _jd.get("about_role", ""),
                                    "data": _jd,
                                })
                    except Exception as exc:  # noqa: BLE001 — fail-soft p/ o LLM
                        logger.warning(
                            "[WizardOrchestrator] tool %s raised: %s", name, exc, exc_info=True
                        )
                        result_text = (
                            f"A tool {name} falhou: {exc}. Tente outra abordagem "
                            f"ou peça o dado ao recrutador."
                        )
                        is_error = True
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tu_id,
                    "content": result_text,
                    "is_error": is_error,
                })
            messages.append({"role": "user", "content": tool_results})

        # Esgotou iterações — devolve melhor esforço sem loop infinito.
        logger.warning(
            "[WizardOrchestrator] max_iterations=%d reached", max_iters
        )
        return OrchestratorResult(
            reply=(
                "Registrei o que consegui até aqui. Quer revisar os dados ou "
                "seguir para o próximo passo?"
            ),
            state_updates=accumulated_updates,
            tool_calls=tool_calls,
            iterations=max_iters,
            response_blocks=accumulated_response_blocks,
        )


_default_orchestrator: Optional[WizardOrchestrator] = None


def get_wizard_orchestrator() -> WizardOrchestrator:
    """Singleton accessor — stateless, thread-safe.

    O singleton de produção inclui as service-backed tools (I/O via serviços
    canônicos). A classe ``WizardOrchestrator`` continua desacoplada (tools
    passadas no construtor) para testes I/O-free; só o accessor força o import
    do módulo service-backed.
    """
    global _default_orchestrator  # noqa: PLW0603
    if _default_orchestrator is None:
        try:
            from app.domains.job_creation.orchestrator.wizard_service_tools import (
                SERVICE_TOOLS,
            )
        except Exception as exc:  # noqa: BLE001 — degrada para tools puras
            logger.warning(
                "[WizardOrchestrator] service tools indisponíveis: %s", exc
            )
            SERVICE_TOOLS = ()
        _default_orchestrator = WizardOrchestrator(
            tools=SERVICE_TOOLS,
            service_tools_degraded=(len(SERVICE_TOOLS) == 0),
        )
    return _default_orchestrator
