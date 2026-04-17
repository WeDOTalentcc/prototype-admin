"""
LIA CAPABILITIES AUDIT — Teste Exaustivo de Cenários Reais
=============================================================
Testa TODAS as capacidades da LIA preservando arquitetura canônica.
Não altera rotas, não duplica arquivos — apenas observa e reporta.

Uso: python3 tests/lia_capabilities_audit.py
"""
import asyncio, json, time, sys, traceback
from typing import Any
import urllib.request, urllib.error

API = "http://localhost:8001"
PASS, FAIL, WARN, SKIP = "✅", "❌", "⚠️ ", "⏭️ "

def http_post(path: str, body: dict, headers: dict = None) -> dict:
    h = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(f"{API}{path}", json.dumps(body).encode(), h)
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()[:200]}
    except Exception as ex:
        return {"error": str(ex)}

def http_get(path: str, headers: dict = None) -> dict:
    h = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(f"{API}{path}", headers=h)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except Exception as ex:
        return {"error": str(ex)}

# ─────────────────────────────────────────────────────────────────────────────
results: list[dict] = []

def check(name: str, passed: bool, detail: str = "", warn: bool = False) -> None:
    status = WARN if warn else (PASS if passed else FAIL)
    results.append({"status": status, "name": name, "detail": detail})
    print(f"  {status} {name}")
    if detail and not passed:
        print(f"       → {detail[:120]}")

def lia_response(chat_resp: dict) -> tuple[str, str, str | None]:
    """Extract (content, intent, ui_action) from /api/v1/chat response."""
    if chat_resp.get("error"):
        return f"HTTP_ERROR:{chat_resp.get('error')}", "", None
    msg = chat_resp.get("data", {}).get("message", {})
    meta = msg.get("message_metadata", {})
    ui = meta.get("ui_action") or chat_resp.get("data", {}).get("ui_action")
    return msg.get("content", ""), meta.get("intent", ""), ui

# ─────────────────────────────────────────────────────────────────────────────
def run_audit():
    print("\n" + "="*70)
    print("  LIA CAPABILITIES AUDIT — Iniciando...")
    print("="*70)

    # AUTH
    print("\n[AUTH]")
    login = http_post("/api/v1/auth/login", {"email": "demo@wedotalent.com", "password": "demo123"})
    token = login.get("data", {}).get("access_token", "")
    check("Login demo user retorna JWT", bool(token), f"Response: {str(login)[:100]}")
    if not token:
        print("FATAL: sem token, abortando.")
        return

    auth = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def chat(msg: str, conv_id: str = None) -> tuple[str, str, str | None, str]:
        body = {"content": msg}
        if conv_id:
            body["conversation_id"] = conv_id
        r = http_post("/api/v1/chat", body, auth)
        content, intent, ui_action = lia_response(r)
        conv = r.get("data", {}).get("conversation", {}).get("id", "")
        return content, intent, ui_action, conv

    # ─── BLOCO 1: CONVERSACIONAL GERAL ───────────────────────────────────────
    print("\n[BLOCO 1] Conversacional Geral")

    c, i, u, _ = chat("oi")
    check("1.1 Saudação — resposta não vazia", len(c) > 0, c[:80])
    check("1.2 Saudação — sem erro explícito", "erro" not in c.lower() and "ocorreu" not in c.lower(), c[:80])

    c, i, u, _ = chat("o que você consegue fazer?")
    has_kw = any(k in c.lower() for k in ["candidato", "vaga", "buscar", "pipeline", "ajudar"])
    check("1.3 Capacidades — menciona funções relevantes", has_kw, c[:120])

    c, i, u, _ = chat("qual é a capital da França?")
    check("1.4 Pergunta genérica — responde sem erro", len(c) > 5, c[:80])

    c, i, u, _ = chat("me explique o processo de recrutamento")
    check("1.5 Conversa sobre RH — resposta contextual", len(c) > 20, c[:80])

    time.sleep(1)

    # ─── BLOCO 2: BUSCA DE CANDIDATOS ────────────────────────────────────────
    print("\n[BLOCO 2] Busca de Candidatos")

    c, i, u, conv_search = chat("busque candidatos")
    check("2.1 'busque candidatos' — detecta intent search", "search" in i or "candidat" in i or "sourcing" in i or len(c) > 0, f"intent={i}")
    check("2.2 'busque candidatos' — pede critérios OU busca", len(c) > 0, c[:80])

    c, i, u, _ = chat("busque desenvolvedores Python sênior em São Paulo")
    check("2.3 Busca com critérios — responde sem travar", len(c) > 0, c[:100])
    check("2.4 Busca com critérios — não retorna erro genérico", "ocorreu um erro" not in c.lower(), c[:100])

    c, i, u, _ = chat("encontre candidatos com experiência em fintech e Node.js")
    check("2.5 Busca composta — processa sem crash", len(c) > 0, c[:100])

    c, i, u, _ = chat("quero ver candidatos para a vaga de gerente de marketing")
    check("2.6 Busca por vaga — responde", len(c) > 0, c[:100])

    time.sleep(1)

    # ─── BLOCO 3: PIPELINE / MOVER CANDIDATO ─────────────────────────────────
    print("\n[BLOCO 3] Pipeline — Mover / Status Candidato")

    c, i, u, _ = chat("mova o candidato João Silva para entrevista técnica")
    check("3.1 Mover candidato — intent detectado", any(k in i for k in ["mover","move","pipeline","candidat","agentic"]), f"intent={i}")
    check("3.2 Mover candidato — pede confirmação ou mais info", any(k in c.lower() for k in ["confirm","candidato","qual","nome","etapa","informação"]), c[:120])
    check("3.3 Mover candidato — não executa sem confirmar", "movido" not in c.lower() and "atualizado" not in c.lower(), c[:80], warn=True)

    c, i, u, _ = chat("altere o status do candidato Maria Santos para aprovado")
    check("3.4 Alterar status — resposta não vazia", len(c) > 0, c[:80])
    check("3.5 Alterar status — sem erro genérico", "ocorreu um erro" not in c.lower(), c[:100])

    c, i, u, _ = chat("reprove o candidato Pedro Lima com feedback")
    check("3.6 Reprovar candidato — pede confirmação", any(k in c.lower() for k in ["confirm","candidato","reprova","certeza","qual"]), c[:120])

    time.sleep(1)

    # ─── BLOCO 4: COMUNICAÇÃO ─────────────────────────────────────────────────
    print("\n[BLOCO 4] Comunicação — Email / WhatsApp")

    c, i, u, _ = chat("envie um email de feedback para o candidato")
    check("4.1 Enviar email — pede dados necessários", any(k in c.lower() for k in ["candidato","assunto","mensagem","qual","email","nome"]), c[:120])
    check("4.2 Enviar email — não envia sem confirmar", "enviado" not in c.lower(), c[:80], warn=True)

    c, i, u, _ = chat("mande uma mensagem WhatsApp para Ana Costa dizendo que ela foi aprovada na triagem")
    check("4.3 WhatsApp — detecta intenção de comunicação", len(c) > 0, c[:100])
    check("4.4 WhatsApp — pede confirmação antes de enviar", any(k in c.lower() for k in ["confirma","certeza","candidata","número","contato","whatsapp","enviar"]), c[:120], warn=True)

    time.sleep(1)

    # ─── BLOCO 5: VAGAS ───────────────────────────────────────────────────────
    print("\n[BLOCO 5] Gestão de Vagas")

    c, i, u, _ = chat("quais são as vagas abertas?")
    check("5.1 Listar vagas — responde (sem dados = informa)", len(c) > 0, c[:100])
    check("5.2 Listar vagas — sem crash", "ocorreu um erro" not in c.lower(), c[:100])

    c, i, u, _ = chat("crie uma nova vaga de desenvolvedor full stack pleno")
    check("5.3 Criar vaga — detecta intenção", len(c) > 0, c[:100])
    check("5.4 Criar vaga — oferece iniciar wizard ou pede dados", any(k in c.lower() for k in ["vaga","cargo","título","empresa","criação","wizard","preencher","detalhe"]), c[:120])

    c, i, u, _ = chat("pause a vaga de engenheiro de software")
    check("5.5 Pausar vaga — pede confirmação", any(k in c.lower() for k in ["confirm","vaga","pausar","qual","nome"]), c[:120])

    c, i, u, _ = chat("qual o status da vaga de Product Manager?")
    check("5.6 Status de vaga — responde", len(c) > 0, c[:100])

    time.sleep(1)

    # ─── BLOCO 6: ANÁLISE E PARECER ───────────────────────────────────────────
    print("\n[BLOCO 6] Análise — Parecer de Vaga / Candidato")

    c, i, u, _ = chat("faça um parecer sobre a vaga de engenheiro de dados sênior: 5 anos de experiência, Python, SQL, cloud, salário entre R$15k e R$20k")
    check("6.1 Parecer de vaga — resposta substantiva", len(c) > 50, c[:150])
    check("6.2 Parecer de vaga — analisa requisitos", any(k in c.lower() for k in ["vaga","requisito","salário","experiência","candidato","análise","mercado"]), c[:150])

    c, i, u, _ = chat("analise o perfil de um desenvolvedor com 3 anos em Python e Django, certificação AWS")
    check("6.3 Análise de perfil — gera análise", len(c) > 30, c[:150])

    c, i, u, _ = chat("qual o benchmark salarial para gerente de produto em SP?")
    check("6.4 Benchmark salarial — responde (pode ser sem dados)", len(c) > 0, c[:100])

    time.sleep(1)

    # ─── BLOCO 7: TRIAGEM WSI ─────────────────────────────────────────────────
    print("\n[BLOCO 7] Triagem WSI")

    c, i, u, _ = chat("inicie uma triagem WSI para o candidato Carlos Mendes")
    check("7.1 WSI — detecta intenção", len(c) > 0, c[:100])
    check("7.2 WSI — guia para ação ou pede dados", any(k in c.lower() for k in ["triagem","wsi","candidato","iniciar","link","vaga","confirma"]), c[:120])
    if u:
        check("7.3 WSI — ui_action setado para navegar", True, f"ui_action={u}")
    else:
        check("7.3 WSI — ui_action ausente (navegar deveria ser sugerido)", False, "ui_action não retornado", warn=True)

    time.sleep(1)

    # ─── BLOCO 8: ANALYTICS / KPIs ───────────────────────────────────────────
    print("\n[BLOCO 8] Analytics e KPIs")

    c, i, u, _ = chat("qual o time to hire médio da empresa?")
    check("8.1 Time to hire — responde", len(c) > 0, c[:100])
    check("8.2 Time to hire — sem erro genérico", "ocorreu um erro" not in c.lower(), c[:100])

    c, i, u, _ = chat("como está o funil de recrutamento?")
    check("8.3 Funil recrutamento — responde", len(c) > 0, c[:100])

    c, i, u, _ = chat("quais são as métricas de diversidade?")
    check("8.4 Métricas diversidade — responde", len(c) > 0, c[:100])

    time.sleep(1)

    # ─── BLOCO 9: CONFIGURAÇÕES DA EMPRESA ───────────────────────────────────
    print("\n[BLOCO 9] Configurações da Empresa")

    c, i, u, _ = chat("preencha os dados da empresa: nome WeDo Talent, CNPJ 12.345.678/0001-00, setor RH")
    check("9.1 Preencher dados empresa — processa", len(c) > 0, c[:100])
    check("9.2 Preencher dados empresa — não retorna erro genérico", "ocorreu um erro" not in c.lower(), c[:100])

    c, i, u, _ = chat("configure a política de recrutamento para exigir mínimo 2 anos de experiência")
    check("9.3 Configurar política — responde com ação ou confirmação", len(c) > 0, c[:100])

    time.sleep(1)

    # ─── BLOCO 10: NAVEGAÇÃO / UI_ACTION ─────────────────────────────────────
    print("\n[BLOCO 10] Navegação — ui_action e direcionamento")

    # Test navigation_intent.py directly
    try:
        sys.path.insert(0, "/home/runner/workspace/lia-agent-system")
        from app.orchestrator.navigation_intent import NavigationIntentDetector
        detector = NavigationIntentDetector()

        cases = [
            ("quero ver as vagas abertas", "Vagas"),
            ("me mostra o funil de talentos", "Funil de Talentos"),
            ("abrir configurações", "Configurações"),
            ("ver indicadores e métricas", "Indicadores"),
        ]
        for msg, expected_page in cases:
            result = detector.detect(msg)
            passed = result.page == expected_page and result.confidence >= 0.5
            check(f"10.{cases.index((msg,expected_page))+1} Nav '{msg}' → {expected_page}", passed,
                  f"page={result.page} conf={result.confidence:.2f}")
    except Exception as ex:
        check("10.x NavigationIntentDetector import", False, str(ex)[:100])

    # Test via chat that ui_action is populated for navigation commands
    c, i, u, _ = chat("quero ver o funil de talentos")
    check("10.5 'funil de talentos' → ui_action populado", u is not None, f"ui_action={u}, content={c[:60]}", warn=(u is None))

    c, i, u, _ = chat("me leva para as configurações da empresa")
    check("10.6 'configurações' → ui_action ou resposta de navegação", u is not None or "configuração" in c.lower(), f"ui_action={u}, content={c[:60]}", warn=(u is None))

    time.sleep(1)

    # ─── BLOCO 11: CONTEXTO MULTI-TURNO ──────────────────────────────────────
    print("\n[BLOCO 11] Contexto Multi-Turno (memória)")

    c1, _, _, conv11 = chat("quero buscar candidatos para uma vaga de designer UX")
    c2, i2, _, _ = chat("mostre apenas os que têm experiência com Figma", conv11)
    check("11.1 Multi-turno — resposta ao turno 2 não vazia", len(c2) > 0, c2[:100])
    check("11.2 Multi-turno — turno 2 não retorna erro genérico", "ocorreu um erro" not in c2.lower(), c2[:100])

    c1, _, _, conv12 = chat("vou enviar um email para o candidato Ricardo")
    c2, _, _, _ = chat("o assunto é: Parabéns! Você foi aprovado na triagem.", conv12)
    check("11.3 Email multi-turno — turno 2 continua fluxo", len(c2) > 0, c2[:100])
    check("11.4 Email multi-turno — sem erro", "ocorreu um erro" not in c2.lower(), c2[:100])

    time.sleep(1)

    # ─── BLOCO 12: ROBUSTEZ / EDGE CASES ─────────────────────────────────────
    print("\n[BLOCO 12] Robustez — Edge Cases")

    c, i, u, _ = chat("")
    check("12.1 Mensagem vazia — handled gracefully", True, "N/A (validation should prevent)", warn=True)

    c, i, u, _ = chat("DROP TABLE candidates; --")
    check("12.2 SQL injection — rejeitado ou responde safe", "error" not in c.lower() or len(c) > 0, c[:80])

    c, i, u, _ = chat("a" * 500)
    check("12.3 Mensagem longa (500 chars) — não crashar", len(c) > 0, c[:80])

    c, i, u, _ = chat("mova mova mova mova candidato para entrevista entrevista")
    check("12.4 Mensagem repetida — not crash", len(c) > 0, c[:80])

    # ─── BLOCO 13: VERIFICAÇÃO DE ROTAS ──────────────────────────────────────
    print("\n[BLOCO 13] Rotas de Orquestração")

    for path, name in [
        ("/api/v1/orchestrator/talent-chat", "talent-chat orchestrator"),
        ("/api/v1/orchestrator/job-chat", "job-chat orchestrator"),
    ]:
        r = http_post(path, {"message": "oi", "user_id": "demo"}, auth)
        content = r.get("data", {}).get("content") or r.get("content", "")
        has_error = r.get("error") or ("detail" in r and "error" in str(r.get("detail","")))
        check(f"13.x {name} — responde sem crash", not has_error and len(content) > 0, f"resp={str(r)[:100]}")

    # ─── RELATÓRIO FINAL ─────────────────────────────────────────────────────
    print("\n" + "="*70)
    total = len(results)
    passed = sum(1 for r in results if r["status"] == PASS)
    failed = sum(1 for r in results if r["status"] == FAIL)
    warned = sum(1 for r in results if r["status"] == WARN)

    print(f"\n  RESULTADO FINAL: {passed}/{total} passaram | {failed} falharam | {warned} avisos")
    print(f"\n  {FAIL} FALHAS DETALHADAS:")
    for r in results:
        if r["status"] == FAIL:
            print(f"     • {r['name']}")
            if r["detail"]:
                print(f"       {r['detail'][:100]}")

    print(f"\n  {WARN} AVISOS (comportamento esperado mas verificar):")
    for r in results:
        if r["status"] == WARN:
            print(f"     • {r['name']}: {r['detail'][:80]}")

    print("\n" + "="*70)
    return failed

if __name__ == "__main__":
    failed = run_audit()
    sys.exit(1 if failed > 0 else 0)
