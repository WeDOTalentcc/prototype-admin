# Product

## Register

product

## Users

**Primário — Recrutador (cliente final, B2B SaaS):**
Profissional de RH/talent acquisition em empresas médias e grandes no Brasil
(operação multi-tenant via Apartment). Usa a WeDOTalent diariamente como ferramenta
de trabalho: cria vagas, configura WSI (Worker Style Inventory), monitora kanban
de candidatos, conversa com a LIA no chat lateral, valida triagem, envia ofertas.
Contexto típico: 9-18h, desktop 24"+, navegador em foreground o dia inteiro,
múltiplas vagas em paralelo. Job-to-be-done: reduzir tempo de contratação sem
perder fairness/qualidade de fit.

**Secundário — Candidato:**
Pessoa em busca de emprego no Brasil, familiaridade digital variada (do júnior
tech ao operacional sem desktop em casa). Acessa portal candidato em mobile na
maioria das vezes. Interage com LIA via WhatsApp ou web chat pra triagem (WSI,
big five, perguntas técnicas). Job-to-be-done: ser avaliado de forma justa e
saber onde está no processo.

**Terciário — Manager (decisor da vaga):**
Gerente que abriu a vaga e aprova shortlist/oferta. Uso esporádico (não diário),
geralmente em pontos específicos do funil. Precisa de visualização rápida +
contexto pra decidir sem entrar no operacional.

## Product Purpose

Plataforma de recrutamento com IA conversacional (LIA) que combina ATS canonical
+ triagem inteligente + assistente que executa tarefas no chat. Operação
multi-tenant (Apartment + RLS). Não é um chatbot dentro de um ATS — é um agente
operacional com o ATS como camada de persistência. Sucesso quando o recrutador
delega tarefas reais à LIA (criar vaga, ajustar WSI, mover candidato no pipeline,
enviar comunicação) em vez de operar manualmente. plataforma-lia é o frontend
Next.js que o recrutador e o candidato usam; lia-agent-system é o back-end
FastAPI/Python que serve o agente + ATS via Rails proxy.

## Brand Personality

Confiável, expert, conversacional. Tom adulto e profissional (não infantil, não
brincalhão), com peso técnico (não fofo, não meme). A LIA é uma colega recrutadora
sênior com IA por baixo — não uma mascote nem um assistente bot. Referências
positivas: Linear (densidade visual sóbria sem virar planilha), Notion (texto
respira, blocos como ferramenta), Stripe (clareza decisiva, micro-interações
contidas). Voice rules: PT-BR direto, 1 ideia por frase, sem jargão de RH legado
("colaborador", "candidatabilidade"), sem emoji decorativo. Confiança vem de
mostrar o trabalho da IA (Live Task Feed / ThinkingStepsCard), não de afirmações
de marketing.

## Anti-references

**ATS legado pesado (Gupy, Kenoby, Vagas.com).** Tabelas infinitas sem
hierarquia, formulário-mãe de 40 campos, navegação por menus aninhados, visual
de planilha+formulário. Tudo que faz o recrutador brasileiro associar "ATS" a
"sofrimento operacional".

**ATS "divertido" infantil.** Combinação simultânea azul + amarelo + vermelho
saturados, blobs amorfos no background, ilustrações Storyset/unDraw, gradiente
hero+3-cards-iguais. Decisão Brandbook 2026-04-26 (override v2): WeDOTalent é
adulto, sem combinação infantil, sem formas amorfas.

**Chatbot brincalhão emoji-heavy.** Drift / Intercom widget style: "Hi there!
👋", "Aaaand we're done! 🎉", emoji em quase toda mensagem do bot, tom
performaticamente entusiasmado. A LIA não comemora — ela trabalha.

**SaaS genérico AI-slop.** Big-number-hero (47K candidatos triados!), 3
identical cards com gradient accent, glassmorphism decorativo, "AI made that"
óbvio. Side-stripe borders, gradient text, modal-first patterns — proibidos
por design.

## Design Principles

1. **Practice what you preach.** A LIA é uma IA recrutadora; o produto inteiro
   precisa parecer feito por gente que entende IA + recrutamento. Telas devem
   transmitir competência, não promessa.

2. **Zero páginas novas.** Toda interação cabe no right panel ou no chat (premissa
   UX-1..UX-7, 2026-04-19). Modais só quando inline / progressive disclosure
   genuinamente não atende.

3. **Mostrar o trabalho da IA.** Quando a LIA pensa, o usuário vê o que ela está
   fazendo (Live Task Feed canonical: ThinkingStepsCard). IA opaca = IA não
   confiável.

4. **Canonical-fix sobre patch local.** Produzir 1 source of truth em vez de
   replicar; consumidores leem do produtor. Aplica a code E a design tokens
   (90% gray + 10% accent cyan já é canonical — não introduzir outra paleta de
   acento).

5. **Decisão antes de variação.** Cada surface compromete-se com 1 escolha
   tipográfica + 1 paleta + 1 densidade. Variação por estado, não por capricho.

## Accessibility & Inclusion

- **WCAG 2.1 nível AA** mandatório em toda surface (contraste 4.5:1 texto normal,
  3:1 large text + UI components, foco visível em todo controle interativo,
  keyboard nav completa, semantic HTML).
- **`prefers-reduced-motion`** respeitado — coerente com decisão arquitetural de
  desabilitar animações Radix globalmente. Quando animação for adicionada, deve
  ter fallback estático sob reduced-motion.
- **PT-BR como locale primário** com EN como secundário. Tradução validada por
  contrato (`scripts/check_i18n_keys.py` v2.1 + runtime `MISSING_MESSAGE`
  guard).
- **Mobile-first no portal candidato** (uso real é majoritariamente mobile);
  desktop-first no recrutador (24"+ é o caso comum). Não inverter.
