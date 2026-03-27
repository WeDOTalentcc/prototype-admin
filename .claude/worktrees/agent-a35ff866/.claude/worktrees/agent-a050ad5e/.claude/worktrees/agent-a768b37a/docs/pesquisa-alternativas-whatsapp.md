# Pesquisa de Alternativas para WhatsApp Business API — TRI-014

**Data:** 09 Fevereiro 2026  
**Responsável:** Paulo Moraes  
**Status:** Pesquisa Concluída — Pendente POC  
**Versão:** 1.0

---

## 1. CONTEXTO DO PROBLEMA

A WeDo Talent precisa de um canal WhatsApp para que a LIA conduza triagens com candidatos. O desafio principal é **provisionar números de WhatsApp Business API de forma ágil** para cada cliente da plataforma.

### Requisitos da WeDo Talent:
1. Cada cliente tem seu próprio número de WhatsApp (ex: "Itaú Talentos")
2. Todo o gerenciamento técnico (API, templates, envio) é feito pela WeDo Talent
3. Os custos de mensagens são repassados ao cliente
4. O processo de onboarding de novos clientes deve ser o mais rápido possível
5. Suporte a templates aprovados pela Meta para mensagens de triagem
6. Webhooks de status (entregue, lido, respondido) para rastreamento

---

## 2. COMO FUNCIONA O WHATSAPP BUSINESS API

### Conceitos Fundamentais

- **BSP (Business Solution Provider):** Parceiro oficial da Meta que fornece acesso à API do WhatsApp. Exemplos: Gupshup, 360dialog, Twilio, Zenvia.
- **WABA (WhatsApp Business Account):** Conta empresarial do WhatsApp. Cada cliente terá sua própria WABA.
- **Meta Business Manager:** Painel da Meta onde a empresa precisa ser verificada. Requisito obrigatório.
- **Templates:** Mensagens pré-aprovadas pela Meta para envio proativo (fora da janela de 24h).
- **Janela de 24h:** Após o candidato responder, a LIA pode enviar mensagens livres por 24 horas sem template.

### Fluxo de Mensagens da LIA

```
LIA envia template de triagem → Candidato responde → Janela 24h aberta
→ LIA conduz conversa livre de triagem WSI → Candidato completa
→ Score calculado → Resultado registrado no pipeline
```

---

## 3. MODELOS DE OPERAÇÃO POSSÍVEIS

### Modelo A: Número Único da WeDo Talent
- Um número só para todos os clientes
- Candidato recebe mensagem de "WeDo Talent", não da empresa contratante
- **Prós:** Setup único, rápido
- **Contras:** Confuso para o candidato, não profissional, sem identidade do cliente
- **Veredicto:** Não recomendado para MVP

### Modelo B: Conta Individual por Cliente no BSP
- Cada cliente cria sua própria conta no BSP (ex: Gupshup)
- Cada cliente faz sua própria verificação Meta
- WeDo Talent integra via API de cada conta
- **Prós:** Isolamento total
- **Contras:** WeDo Talent não controla nada, processo fragmentado, difícil de escalar
- **Veredicto:** Não recomendado

### Modelo C: WeDo Talent como Tech Provider/Partner (RECOMENDADO)
- WeDo Talent tem UMA conta de Partner no BSP
- Dentro dessa conta, cria WABAs separadas para cada cliente
- Cada WABA tem o número e nome do cliente
- Todo o gerenciamento (API, templates, envio, analytics) é centralizado na WeDo Talent
- Custos consolidados e repassados ao cliente
- **Prós:** Controle total, onboarding rápido, escalável, profissional
- **Contras:** WeDo Talent assume responsabilidade operacional
- **Veredicto:** Modelo ideal para a plataforma

---

## 4. FLUXO DE PROVISIONAMENTO DE NÚMERO (Modelo C)

### Passo a passo operacional:

```
1. Cliente assina contrato com WeDo Talent
2. WeDo Talent coleta documentos do cliente (ver seção 5)
3. No painel do BSP (Partner Dashboard), WeDo cria nova WABA para o cliente
4. Embedded Signup: representante do cliente confirma empresa via popup Meta
   → Se empresa já tem Meta Business verificado: pula para passo 5
   → Se NÃO tem: envia documentos (CNPJ, etc.) — 2 a 10 dias úteis
5. WeDo registra o número do cliente na WABA
6. Cliente recebe OTP no número → confirma (SMS ou ligação)
7. WeDo configura perfil (nome de exibição, logo, descrição)
8. WeDo cria templates de mensagem de triagem
9. Meta aprova templates (minutos a 24h)
10. Número ativo — LIA pode disparar triagens
```

### Tempos estimados:
| Cenário | Tempo Total |
|---------|-------------|
| Cliente já tem Meta Business verificado | 1-2 dias |
| Cliente precisa verificar do zero | 5-10 dias úteis |
| Empresa grande conhecida (Itaú, Ambev) | Verificação geralmente rápida |
| Empresa menor ou nova | Pode demorar até 10 dias |

### Gargalo principal:
A **verificação do Meta Business Manager** é o único passo que nenhum BSP acelera. É processo exclusivo da Meta. O Embedded Signup facilita (o cliente faz tudo dentro da plataforma WeDo), mas a aprovação depende da Meta.

---

## 5. CHECKLIST DE DOCUMENTOS DO CLIENTE

### Obrigatórios (exigência da Meta):

| # | Documento/Informação | Para quê | Exemplo |
|---|---|---|---|
| 1 | Razão Social | Verificação Meta Business | "Itaú Unibanco S.A." |
| 2 | CNPJ | Verificação Meta Business | 60.701.190/0001-04 |
| 3 | Endereço comercial | Verificação Meta Business | Av. Paulista, 1000, SP |
| 4 | Site oficial da empresa | Meta verifica se o domínio bate | www.itau.com.br |
| 5 | Email corporativo (domínio da empresa) | Ponto de contato | rh@itau.com.br |
| 6 | Número de telefone para WhatsApp | Registro do canal | +55 11 99999-0000 |
| 7 | Nome de exibição desejado | O que o candidato vê | "Itaú Talentos" |

### Regras sobre o número de telefone:
- NÃO pode estar ativo no WhatsApp pessoal ou WhatsApp Business App (precisa desvincular antes)
- Pode ser fixo (valida por ligação) ou celular (valida por SMS)
- Pode ser número novo comprado de operadora exclusivamente para isso
- NÃO pode ser VoIP genérico (ex: Skype) — precisa ser número real brasileiro

### Opcionais mas recomendados:

| # | Item | Para quê |
|---|---|---|
| 8 | Logo da empresa (PNG, alta resolução) | Foto do perfil no WhatsApp |
| 9 | Descrição curta (até 256 caracteres) | Bio do perfil WhatsApp Business |
| 10 | Categoria do negócio | Meta exige na criação (ex: "Serviços profissionais") |
| 11 | Contato interno responsável | Quem valida OTP e aprova templates |

---

## 6. COMPARATIVO DE BSPs (Business Solution Providers)

### Tabela Comparativa Principal

| Critério | **Gupshup** | **360dialog** | **Twilio** | **Zenvia** | **Infobip** |
|---|---|---|---|---|---|
| **Sede/Foco** | Global, forte LATAM | Global | Global | **Brasil** (Nasdaq: ZENV) | Global, escritório BR |
| **BSP Oficial Meta** | Sim | Sim | Sim | Sim | Sim |
| **Tech Provider Program** | Sim | Sim | Sim | Sim | Sim |
| **Multi-WABA (vários clientes)** | Sim, Partner Dashboard | Sim, Partner Hub | Sim | Sim | Sim |
| **Embedded Signup** | Sim | Sim | Sim | Sim | Sim |
| **Taxa de setup** | $0 | $0 | Variável | $649 USD | Custom |
| **Taxa mensal** | $0 | ~€25-45/número | Subscription | $20+/mês | Custom |
| **Markup por mensagem** | $0.001/msg | $0 (taxa Meta pura) | 10-30% sobre Meta | Pacotes bundled | Custom |
| **Dashboard de gestão** | Sim, com analytics | Mínimo (API-first) | Básico | Sim | Sim |
| **Chatbot/IA nativo** | Sim | Não | Via Flex | Sim | Sim |
| **Webhook de status** | Sim (entregue/lido/respondido) | Sim | Sim | Sim | Sim |
| **SDK/API qualidade** | Boa (REST + SDK) | Boa (REST) | Excelente | Razoável | Boa |
| **Suporte Brasil** | Sim (LATAM) | Sim | Sim | Sim (HQ Brasil) | Sim (escritório SP) |
| **Faturamento BRL** | Planejado H2 2026 | Planejado H2 2026 | Planejado H2 2026 | Sim | Custom |
| **Previsibilidade de custo** | Alta | Alta | Média | Baixa | Média |

### Custos Base da Meta (aplicáveis a TODOS os BSPs):

| Tipo de Mensagem | Custo por mensagem (Brasil) |
|---|---|
| Marketing | ~$0.035-$0.06 USD |
| Utilidade (utility) | ~$0.006-$0.015 USD |
| Autenticação | ~$0.010-$0.020 USD |
| Serviço (resposta do candidato, janela 24h) | 1.000 grátis/mês, depois por mensagem |

---

## 7. ANÁLISE DETALHADA DOS TOP 3

### 7.1 Gupshup (Recomendação Principal)

**Por que Gupshup:**
- $0 de setup, $0 mensal — paga apenas $0.001/msg + taxa Meta
- Partner Dashboard robusto para gerenciar múltiplos clientes
- Embedded Signup integrado — cliente faz verificação Meta dentro da plataforma WeDo
- API REST bem documentada com SDKs
- Forte presença LATAM, suporte a português
- Chatbot/IA nativo que pode complementar a LIA
- Escalável: suporta alto volume de mensagens

**Limitações:**
- 6% markup em mensagens de marketing (não-MM Lite) a partir de Jan 2026
- Dashboard menos polido que concorrentes enterprise
- Sem faturamento em BRL (previsto H2 2026)

**Custo estimado para WeDo Talent (100 triagens/mês, ~20 msgs cada = 2.000 msgs):**
- Mix estimado: 80% utility (1.600 msgs) + 20% marketing (400 msgs)
- Taxa Meta utility: 1.600 × $0.0068 = $10.88/mês
- Taxa Meta marketing: 400 × $0.0625 = $25.00/mês
- Taxa Gupshup: 2.000 × $0.001 = $2.00/mês
- **Total estimado: ~$37.88/mês (~R$ 220)** (câmbio ref. $1 = R$ 5.80)

### 7.2 360dialog (Alternativa — Melhor Custo Unitário)

**Por que 360dialog:**
- $0 markup por mensagem — paga apenas taxa Meta pura
- Melhor custo unitário em alto volume
- Partner Hub para gerenciar múltiplos clientes
- API minimalista e direta

**Limitações:**
- Taxa mensal por número: ~€25-45/mês
- Sem dashboard robusto (é API-first, precisa construir interface própria)
- Sem chatbot nativo
- Melhor para equipes técnicas

**Custo estimado (mesmo cenário: 2.000 msgs/mês):**
- Taxa 360dialog: €25-45/mês/número
- Taxa Meta (utility): 2.000 × $0.01 = $20.00/mês
- **Total estimado: ~€45-65/mês por número**

### 7.3 Zenvia (Alternativa Brasileira)

**Por que Zenvia:**
- Sede no Brasil, faturamento em BRL
- Suporte local em português
- Dashboard completo com automações
- Listada na Nasdaq (credibilidade)

**Limitações:**
- Setup: $649 USD
- Pricing em pacotes bundled — menos previsível
- Mais caro que Gupshup/360dialog em custo por mensagem
- Melhor para grandes enterprises

**Custo estimado (mesmo cenário):**
- Setup: $649 (único)
- Plataforma: $20+/mês
- Mensagens: pacote bundled ~$100+/mês
- **Total estimado: ~$120+/mês** (após setup de $649)

---

## 8. RECOMENDAÇÃO FINAL

### Escolha Principal: **Gupshup**

| Critério | Justificativa |
|---|---|
| Custo | Menor custo total ($0 setup, $0.001/msg markup) |
| Multi-tenant | Partner Dashboard suporta múltiplas WABAs nativamente |
| Onboarding do cliente | Embedded Signup integrado |
| API | REST bem documentada, webhooks robustos |
| Escalabilidade | Suporta de 10 a 100.000+ mensagens/mês |
| Presença LATAM | Suporte regional, documentação em português |

### Plano B: **360dialog**
Se precisarmos de custo unitário zero de markup em alto volume e tivermos capacidade técnica para construir dashboard próprio.

### Descartados para MVP:
- **Twilio:** Markup alto (10-30%), setup complexo, sem vantagem clara sobre Gupshup
- **Zenvia:** Setup de $649, pricing opaco em pacotes, overpriced para volume baixo-médio
- **Infobip:** Enterprise-only, pricing custom, overkill para MVP

---

## 9. PRÓXIMOS PASSOS

### Ações Imediatas (Paulo Moraes):

| # | Ação | Prazo | Status |
|---|---|---|---|
| 1 | Criar conta Partner no Gupshup (gupshup.io) | 09/02/2026 | Pendente |
| 2 | Verificar Meta Business Manager da WeDo Talent | 09-13/02/2026 | Pendente |
| 3 | Registrar número de teste da WeDo Talent | Após verificação Meta | Pendente |
| 4 | Criar template de triagem para teste | Após registro | Pendente |
| 5 | POC: enviar mensagem de teste via API | Após template aprovado | Pendente |
| 6 | Documentar integração API para time de produção | Após POC | Pendente |

### Ações Futuras (Time de Produção):

| # | Ação | Responsável |
|---|---|---|
| 7 | Implementar WhatsApp Provider abstrato no backend (FastAPI/Rails) | Time Backend |
| 8 | Implementar adapter Gupshup (implements WhatsAppProvider) | Time Backend |
| 9 | Criar fluxo de Embedded Signup na plataforma (onboarding cliente) | Time Full-Stack |
| 10 | Integrar webhooks de status (entregue/lido/respondido) | Time Backend |

---

## 10. LINKS ÚTEIS

| Recurso | URL |
|---|---|
| Gupshup Partner Program | https://www.gupshup.io/channels/self-serve/whatsapp |
| Gupshup API Docs | https://docs.gupshup.io/ |
| Gupshup Pricing | https://www.gupshup.io/channels/self-serve/whatsapp/pricing |
| 360dialog Partner Hub | https://www.360dialog.com |
| Meta Business Verification | https://business.facebook.com |
| WhatsApp Business Platform | https://business.whatsapp.com/products/business-platform |
| Meta Partner Directory | https://business.whatsapp.com/partners |
| WhatsApp Cloud API Docs | https://developers.facebook.com/docs/whatsapp |
| WhatsApp Template Guidelines | https://developers.facebook.com/docs/whatsapp/message-templates |
| WhatsApp Pricing (Meta) | https://developers.facebook.com/docs/whatsapp/pricing |

---

## 11. GLOSSÁRIO

| Termo | Definição |
|---|---|
| **BSP** | Business Solution Provider — parceiro oficial da Meta para WhatsApp API |
| **WABA** | WhatsApp Business Account — conta empresarial do WhatsApp |
| **OTP** | One-Time Password — código de verificação enviado por SMS/ligação |
| **Template** | Mensagem pré-aprovada pela Meta para envio proativo |
| **Janela 24h** | Período após resposta do candidato em que mensagens livres são permitidas |
| **Embedded Signup** | Fluxo de verificação Meta integrado dentro da plataforma parceira |
| **Tech Provider** | Programa da Meta para ISVs que provisionam WhatsApp para seus clientes |
| **Meta Business Manager** | Painel da Meta para verificação e gestão de contas empresariais |
