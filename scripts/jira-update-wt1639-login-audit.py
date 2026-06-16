#!/usr/bin/env python3
"""
Atualiza o card WT-1639 no Jira com a auditoria completa da tela de login reformulada.
"""

import os
import json
import requests

CLOUD_ID = '8cf762f8-6a44-47de-8915-6b3dc0cd2715'
BASE_URL = f'https://api.atlassian.com/ex/jira/{CLOUD_ID}/rest/api/3'
ISSUE_KEY = 'WT-1639'


def get_access_token():
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    repl_identity = os.environ.get('REPL_IDENTITY')
    web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')

    if repl_identity:
        x_replit_token = f'repl {repl_identity}'
    elif web_repl_renewal:
        x_replit_token = f'depl {web_repl_renewal}'
    else:
        raise ValueError('Nenhum token Replit disponível')

    resp = requests.get(
        f'https://{hostname}/api/v2/connection?include_secrets=true&connector_names=jira',
        headers={'Accept': 'application/json', 'X_REPLIT_TOKEN': x_replit_token}
    )
    data = resp.json()
    settings = data['items'][0]['settings']
    token = settings.get('access_token') or settings.get('oauth', {}).get('credentials', {}).get('access_token')
    if not token:
        raise ValueError('access_token não encontrado')
    return token


# ── ADF helpers ────────────────────────────────────────────────

def heading(level, text):
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [{"type": "text", "text": text}]
    }


def paragraph(text, bold=False):
    if bold:
        return {
            "type": "paragraph",
            "content": [{"type": "text", "text": text, "marks": [{"type": "strong"}]}]
        }
    return {
        "type": "paragraph",
        "content": [{"type": "text", "text": text}]
    }


def paragraph_mixed(*parts):
    """parts: list of (text, is_bold, is_code)"""
    content = []
    for text, is_bold, is_code in parts:
        node = {"type": "text", "text": text}
        marks = []
        if is_bold:
            marks.append({"type": "strong"})
        if is_code:
            marks.append({"type": "code"})
        if marks:
            node["marks"] = marks
        content.append(node)
    return {"type": "paragraph", "content": content}


def bullet_list(items):
    """items: list of strings or list of paragraph nodes"""
    list_items = []
    for item in items:
        if isinstance(item, str):
            content = [{"type": "paragraph", "content": [{"type": "text", "text": item}]}]
        else:
            content = [item]
        list_items.append({"type": "listItem", "content": content})
    return {"type": "bulletList", "content": list_items}


def rule():
    return {"type": "rule"}


def build_description():
    nodes = []

    # ── TÍTULO ──
    nodes.append(heading(1, "Auditoria Completa — Reformulação da Tela de Login"))
    nodes.append(paragraph(
        "Redesign completo da tela de login da Plataforma LIA: novo layout dois painéis, "
        "fluxo de autenticação em 2 etapas (email → senha), CloudsBackground animado com Framer Motion, "
        "branding WeDoTalent atualizado e alinhamento ao Design System LIA v4.2.1."
    ))
    nodes.append(rule())

    # ── ARQUIVOS DE REFERÊNCIA ──
    nodes.append(heading(2, "📁 Arquivos de Referência (Protótipo Replit)"))
    nodes.append(bullet_list([
        "Página principal: plataforma-lia/src/app/login/page.tsx",
        "Background animado: plataforma-lia/src/components/clouds-background.tsx",
        "Logo: plataforma-lia/public/logos/wedo-logo-transparent.png",
        "Oculta float LIA no login: plataforma-lia/src/components/lia-float/LiaFloatConditional.tsx",
    ]))
    nodes.append(rule())

    # ── CLOUDS BACKGROUND ──
    nodes.append(heading(2, "☁️ CloudsBackground — Especificação Técnica"))
    nodes.append(paragraph("Arquivo: src/components/clouds-background.tsx | Dependência: framer-motion ^12.x"))

    nodes.append(heading(3, "Gradiente de fundo"))
    nodes.append(paragraph(
        "linear-gradient(180deg, #7CBAD8 0%, #8EC5DE 20%, #A3D0E5 40%, "
        "#BCE0F0 60%, #D8EEF7 80%, #EDF7FB 95%, #ffffff 100%)"
    ))
    nodes.append(paragraph("Sky azul no topo → branco puro na base. Fade h-24 from-white/50 na parte inferior."))

    nodes.append(heading(3, "Variantes de SVG (A / B / C / D)"))
    nodes.append(bullet_list([
        "4 formas únicas, cada uma com 9–10 elipses sobrepostas (viewBox: 0 0 240 110)",
        "Todas usam radialGradient branco 95% → transparente 0% — aspecto volumoso sem contorno duro",
    ]))

    nodes.append(heading(3, "Camadas de Profundidade"))
    nodes.append(bullet_list([
        "BACK   — opacidade 0.30 | blur 3px | scale 0.85 | tamanho 280×140px | duração 55–65s | sem deriva vertical",
        "MID    — opacidade 0.60 | blur 2px | scale 1.00 | tamanho 380×190px | duração 36–44s | deriva vertical y:[0,-10,4,-6,0]",
        "FRONT  — opacidade 0.88 | blur 1px | scale 1.15 | tamanho 480×240px | duração 24–32s | sem deriva vertical",
    ]))

    nodes.append(heading(3, "Instâncias (15 nuvens — 5 por camada)"))
    nodes.append(bullet_list([
        "[back]  variante C | top 5%  | 60s | delay 0s  | → right",
        "[back]  variante A | top 28% | 55s | delay 20s | ← left",
        "[back]  variante D | top 52% | 65s | delay 10s | → right",
        "[back]  variante B | top 74% | 58s | delay 32s | ← left",
        "[back]  variante C | top 88% | 62s | delay 5s  | → right",
        "[mid]   variante B | top 12% | 40s | delay 8s  | → right | floatVertical",
        "[mid]   variante D | top 38% | 44s | delay 25s | ← left  | floatVertical",
        "[mid]   variante A | top 60% | 36s | delay 14s | → right | floatVertical",
        "[mid]   variante C | top 80% | 42s | delay 3s  | ← left  | floatVertical",
        "[mid]   variante B | top 22% | 38s | delay 36s | → right | floatVertical",
        "[front] variante A | top 7%  | 28s | delay 6s  | ← left",
        "[front] variante D | top 30% | 24s | delay 18s | → right",
        "[front] variante B | top 55% | 30s | delay 0s  | ← left",
        "[front] variante C | top 70% | 26s | delay 12s | → right",
        "[front] variante A | top 90% | 32s | delay 22s | ← left",
    ]))

    nodes.append(heading(3, "Animação técnica"))
    nodes.append(bullet_list([
        "Travel distance: window.innerWidth + cloudWidth (responsivo; fallback SSR 2560px)",
        "Deriva vertical (mid): y [0, -10, 4, -6, 0] · repeatType mirror · duration = duration * 0.35",
        "Apenas x e y animados — GPU transforms, sem layout thrashing",
        "pointer-events-none aria-hidden=true — não interfere com interação do usuário",
    ]))
    nodes.append(rule())

    # ── LAYOUT GERAL ──
    nodes.append(heading(2, "🏗️ Layout Geral da Página"))
    nodes.append(bullet_list([
        "min-h-screen flex overflow-hidden relative | fonte base: Open Sans",
        "Painel esquerdo (hidden lg:flex lg:w-1/2): branding — visível apenas em ≥ 1024px",
        "Painel direito (w-full lg:w-1/2): card de login — 100% em mobile",
        "CloudsBackground: absolute inset-0 atrás dos dois painéis (z-0)",
    ]))
    nodes.append(rule())

    # ── PAINEL ESQUERDO ──
    nodes.append(heading(2, "🎨 Painel Esquerdo — Branding"))
    nodes.append(bullet_list([
        "Logo WeDoTalent: absolute top-10 left-[38px] · 230px · wedo-logo-transparent.png · fora do fluxo flex",
        "\"talent\" tagline: Open Sans semibold · uppercase · tracking 0.18em · 18px · right-aligned",
        "Badge: pill rounded-full border-wedo-cyan/40 bg-wedo-cyan/10 · \"»\" cyan · text-sm font-medium text-gray-700",
        "Headline H1: text-5xl font-light Open Sans · \"Entre. A LIA já está / trabalhando por você.\"",
        "\"LIA\": Source Serif 4 font-bold — exceção tipográfica intencional de branding (não é violação do DS)",
        "Sequência: text-base font-light text-gray-500 · \"Sourcing global · Triagem inteligente · Agendamentos automáticos\" + \"Recrutamento simples\"",
        "\"simples\": text-wedo-cyan (#60BED1) — único acento de cor na sequência",
        "Footer esq.: absolute bottom-0 · Globe + LinkedIn + Mail (Lucide 16px text-gray-400) + © 2025 LIA by WeDoTalent",
        "Globe → https://www.wedotalent.cc (nova aba)",
        "LinkedIn → https://www.linkedin.com/company/wedotalent/ (nova aba)",
        "Mail → mailto:tech@wedotalent.cc",
    ]))
    nodes.append(rule())

    # ── CARD DE LOGIN ──
    nodes.append(heading(2, "🔐 Painel Direito — Card de Login (2 Etapas)"))
    nodes.append(paragraph("Card container: max-w-md bg-white/90 dark:bg-gray-800/90 backdrop-blur-md rounded-2xl shadow-2xl p-8 lg:p-10"))

    nodes.append(heading(3, "Etapa 1 — Email (step = email)"))
    nodes.append(bullet_list([
        "Título: \"Entrar na plataforma\" · text-xl font-semibold text-gray-950 · centralizado",
        "Label: text-xs font-medium text-gray-800",
        "Input email: type=email · ícone Mail (Lucide) à esquerda · rounded-xl border-gray-200 focus:ring-gray-900/20 · autoFocus",
        "Validação client-side: verifica @ e . · erro em bg-red-50 border-red-100 rounded-xl com AlertCircle",
        "Botão \"Entrar\": bg-gray-900 hover:bg-gray-800 text-white h-10 w-full · avança para Etapa 2",
    ]))

    nodes.append(heading(3, "Etapa 2 — Senha (step = password)"))
    nodes.append(bullet_list([
        "Email pill: bg-gray-50 dark:bg-gray-700 rounded-xl · ícone Mail + email truncado + botão Alterar (Pencil icon 12px)",
        "\"Alterar\": chama handleBack() — reseta step, senha e erro",
        "Input senha: type password/text toggle · Lock à esquerda · Eye/EyeOff à direita · rounded-xl · autoFocus · disabled no submit",
        "Lembrar de mim: checkbox nativo border-gray-300 focus:ring-gray-900/20",
        "Esqueceu a senha?: href=/forgot-password · hover:text-wedo-cyan · font-medium",
        "Botão \"Confirmar\": bg-gray-900 h-10 w-full · loading: Loader2 animate-spin + \"Entrando...\" · disabled={isSubmitting}",
        "Separador: border-t border-gray-200 + label \"ou\" centralizado",
        "Botão Microsoft: SVG oficial 4 quadrados 16×16 (#F25022 #7FBA00 #00A4EF #FFB900) · variant=outline · SSO WorkOS: /api/auth/workos/sso?email=...&connection=conn_microsoft_entra",
    ]))
    nodes.append(rule())

    # ── DARK MODE ──
    nodes.append(heading(2, "🌙 Dark Mode"))
    nodes.append(bullet_list([
        "Loading background: dark:bg-gray-900",
        "Loading spinner: dark:text-gray-400",
        "Card principal: dark:bg-gray-800/90",
        "Email pill: dark:bg-gray-700",
    ]))
    nodes.append(rule())

    # ── FOOTER DIREITO ──
    nodes.append(heading(2, "🌐 Footer Rodapé Direito"))
    nodes.append(paragraph("Posição absolute bottom-0 — não desloca o card."))
    nodes.append(bullet_list([
        "\"A WeDoTalent é uma HRTech brasileira que desenvolve soluções avançadas de tecnologia para o RH do futuro.\"",
        "\"© 2025 WeDoTalent. Todos os direitos reservados.\"",
    ]))
    nodes.append(rule())

    # ── CRITÉRIOS DE ACEITE ──
    nodes.append(heading(2, "✅ Critérios de Aceite"))
    nodes.append(bullet_list([
        "[Layout] Painel esquerdo visível apenas em ≥ 1024px — mobile exibe somente o card",
        "[CloudsBg] Background anima continuamente sem bloquear interação (pointer-events-none)",
        "[CloudsBg] Gradiente de céu visível imediatamente, sem flash branco",
        "[Branding] Logo WeDoTalent no topo esquerdo, fora do fluxo de centralização",
        "[Branding] Badge \"IA Agêntica para Recrutamento\" com borda e fundo cyan visíveis",
        "[Branding] Headline text-5xl font-light — \"LIA\" em Source Serif 4 bold",
        "[Branding] \"simples\" em text-wedo-cyan na segunda linha da sequência",
        "[Footer esq.] Globe/LinkedIn/Mail abrem links corretos em nova aba",
        "[Etapa 1] Email inválido exibe mensagem de erro no container vermelho",
        "[Etapa 1] Email válido avança para Etapa 2 sem recarregar a página",
        "[Etapa 2] \"Alterar\" retorna Etapa 1 — senha e erro são limpos",
        "[Etapa 2] Toggle Eye/EyeOff alterna visibilidade da senha",
        "[Etapa 2] \"Esqueceu a senha?\" redireciona para /forgot-password",
        "[Etapa 2] Botão \"Confirmar\" exibe spinner durante submit e desabilita reenvio",
        "[Etapa 2] Botão Microsoft usa logo SVG 4 cores oficial e inicia SSO WorkOS",
        "[Dark Mode] Card usa bg-gray-800/90 em dark mode",
        "[DS] Todos os inputs usam rounded-xl (DS LIA v4.2.1 compliant)",
        "[LIA Float] Botão flutuante da LIA está oculto na rota /login",
    ]))

    return {"version": 1, "type": "doc", "content": nodes}


def update_issue(token, description):
    url = f'{BASE_URL}/issue/{ISSUE_KEY}'
    resp = requests.put(url,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        json={"fields": {"description": description}}
    )
    return resp.status_code, resp.text


def get_issue(token):
    url = f'{BASE_URL}/issue/{ISSUE_KEY}?fields=summary,description,status'
    resp = requests.get(url, headers={
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    })
    return resp.json()


def main():
    print("=" * 60)
    print(f"ATUALIZANDO CARD {ISSUE_KEY} — AUDITORIA LOGIN")
    print("=" * 60)

    token = get_access_token()
    print("✓ Token obtido com sucesso")

    issue = get_issue(token)
    summary = issue.get('fields', {}).get('summary', 'N/A')
    status = issue.get('fields', {}).get('status', {}).get('name', 'N/A')
    print(f"✓ Card encontrado: [{ISSUE_KEY}] {summary} (status: {status})")

    description = build_description()
    print(f"✓ Descrição ADF gerada ({len(json.dumps(description))} chars)")

    print(f"\nPublicando no Jira...")
    status_code, text = update_issue(token, description)

    if status_code in (200, 204):
        print(f"\n✅ SUCESSO! Card {ISSUE_KEY} atualizado.")
        print(f"   URL: https://wedotalent.atlassian.net/browse/{ISSUE_KEY}")
    else:
        print(f"\n❌ ERRO {status_code}: {text[:400]}")


if __name__ == '__main__':
    main()
