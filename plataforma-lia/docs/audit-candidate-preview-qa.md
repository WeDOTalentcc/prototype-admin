# AUDITORIA QA — Candidate Preview Panel
## WeDOTalent Producao (Vue/Vuetify/Nuxt) vs Referencia Replit (React/Tailwind/Next.js)

**Data:** 2026-04-03
**Fonte Vue:** Repositorio `wedotalent/ats_front` branch `develop` (30+ arquivos, ~6.345 linhas, obtido via GitHub API)
**Fonte React:** `plataforma-lia/src/components/candidate-preview/` (13 arquivos, ~6.196 linhas)
**Testes:** Playwright e2e contra ambos os ambientes
**Score Geral:** 48/100

---

## ADVERTENCIAS IMPORTANTES

1. **Tab Atividades do React usa dados DEMO.** O `CandidateActivitiesTab.tsx` usa `getDemoActivities()` com flag `NEXT_PUBLIC_USE_DEMO_DATA`. Os 15+ tipos de atividade sao UI pronta para backend futuro, nao dados reais. O Vue `applies.vue` usa `AppliesTable` com dados **reais** de candidaturas.
2. **Endpoints React usam proxy.** URLs como `/api/backend-proxy/opinions/...` sao proxy Next.js. O endpoint real e o FastAPI em `BACKEND_URL`. Tab Arquivos do React usa `BACKEND_URL` diretamente, causando CORS em producao.
3. **Vue tem features superiores ao React em 4 areas:** Remuneracao detalhada (`remunerations.vue`, 191 linhas com calculo anualizado 13.33x), Score Analysis (`score_analysis.vue`, 692 linhas com requisitos expandiveis), Insights da Query com evidencias reais do curriculo, e Perguntas Sugeridas geradas pela IA. Essas devem ser PRESERVADAS e backportadas para o React (FIX-R01, R02, R08, R09).
4. **Fixes nao sao 100% drop-in.** Cada correcao requer verificacao de imports, props e event contracts no contexto real do componente.

---

## INDICE

- **Parte 1:** [Resumo Executivo + Screenshots](#parte-1-resumo-executivo)
- **Parte 2:** [Bugs Visuais + Code Fixes](#parte-2-bugs-visuais--code-fixes)
- **Parte 3:** [Feature Gaps (Funcionalidades Ausentes)](#parte-3-feature-gaps)
- **Parte 4:** [Bugs Backend + API](#parte-4-bugs-backend--api)
- **Parte 5:** [Bugs IA + Banco de Dados](#parte-5-bugs-ia--banco-de-dados)
- **Parte 6:** [Tabela de Prioridades Unificada](#parte-6-tabela-de-prioridades-unificada)
- **Parte 7:** [Referencia Tecnica](#parte-7-referencia-tecnica)
- **Como Criar Cards Jira**

---

# PARTE 1: RESUMO EXECUTIVO

## Resumo por Area

| Area | Vue (Producao) | React (Replit) | Status |
|------|---------------|----------------|--------|
| **Header candidato** | Avatar + nome + score + LinkedIn | Avatar "TN" + "senior" badge + "13.0 anos" + "LGPD" + TH1886 + 10 icones acao + datas cadastro/atualizacao + Brain button + expand/close | GAP CRITICO |
| **Tabs** | 4 tabs (Perfil, Atividades, Arquivos, Curriculo) | 4 tabs (Perfil Completo, Atividades, Arquivos, Pareceres e Analises) | DIFERENTE |
| **Tab Perfil** | 9 cards separados (lia_assessment 458L, score_analysis 692L, etc.) | Resumo LIA (com erro "Nao foi possivel gerar") + Experiencia (border-left, duracao calculada) + Formacao (datas ISO raw) + Remuneracao (R$ 32.211) + Preferencias (**bugs: "undefined"/"null" renderizados**) | PARCIAL + BUGS |
| **Tab Atividades** | `applies.vue` (30L) — tabela basica, dados reais | 8 filtros + "Nova Atividade" + agrupamento Hoje/Esta Semana + cards expandiveis (email completo, Avaliacao LIA 4 metricas) + 8 tipos de atividade — **dados demo** | GAP |
| **Tab Arquivos** | `wrapper.vue` (120L) — lista + download | Drag-drop + 4 categorias coloridas + FilePreviewModal (PDF/imagem/video + Analise LIA + Parecer + Score) | GAP CRITICO |
| **Tab Pareceres** | NAO EXISTE | 2 sub-tabs ("Pareceres da LIA" + "Analises") + empty state informativo | FALTANDO |
| **Botoes de acao** | 8 icones-only no dropdown | 9 botoes com labels + LIA Chat + favoritar | GAP |
| **Modais** | 3 (Email, Enrich, AddToJob) | 7+ (LIA Chat, DISC, BigFive, Screening, FilePreview, etc.) | GAP |
| **Layout preview** | Empurra header/botoes da tabela | Drawer overlay sem afetar tabela | BUG CRITICO |
| **Design System** | Roboto, cores hardcoded, sombras Material | Open Sans + Inter, tokens semanticos, sem sombras | GAP |
| **Backend IA** | Multi-tenancy ausente, FairnessGuard nao integrado | Idem (mesmo backend) | BUG CRITICO |
| **Remuneracao** | 191L com calculo 13.33x + beneficios | ~80L simplificado | VUE SUPERIOR |
| **Score Analysis** | 692L com requisitos expandiveis e confianca | Embutido no Parecer LIA (~150L) | VUE SUPERIOR |

**Total de problemas catalogados: 88** (63 Vue originais + 4 bugs React + 5 detalhes visuais + 8 bugs Vue Sessao 2 + 2 itens Vue INFO/BAIXO + 2 features Vue positivas + 4 cards backport novos)
**Criticos: 15 | Altos: 26 | Medios: 30 | Baixos: 16 | INFO: 1**
**Screenshots documentados: 48** (23 React + 7 Vue Sessao 1 + 18 Vue Sessao 2)
**Features Vue SUPERIORES ao React: 4** (Remuneracao 13.33x, Score Analysis 692L, Insights da Query com evidencias, Perguntas Sugeridas IA)
**Cards Jira prontos: ~50 brutos / ~44 unicos** (FIX-01..31 + FIX-12b Vue original + FIX-V01..V09 Vue hotfix + FIX-R01..R09 React — desconto ~6 sobreposicoes layout/atividades)

## Verificacao Funcional (Playwright e2e)

### Producao WeDOTalent

| Passo | Resultado | Observacao |
|---|---|---|
| Navegar para /user/candidates | PASS | Lista de candidatos carregada |
| Abrir preview de candidato | PASS | Drawer lateral com dados reais |
| Tab Perfil Completo | PASS | Header, skills, experiencia visiveis |
| Tab Atividades | PASS | Conteudo visivel, MAS cards nao expandem |
| Tab Arquivos | **FAIL** | **Erro "Failed to fetch" — arquivos nao carregados** |
| Tab Pareceres | PASS | Conteudo basico visivel |
| Fechar painel | PASS | Painel fecha corretamente |

### Replit (Referencia)

| Passo | Resultado | Observacao |
|---|---|---|
| Navegar para home | PASS | Pagina "Funil de Talentos" carregada |
| Abrir candidato via URL direta | PASS | Pagina de detalhe com dados do candidato |
| Tab Perfil Completo | PASS | Header, badges, skills, experiencia visiveis |
| Tab Atividades | PASS | Filtros e timeline renderizados (dados demo) |
| Tab Arquivos | PASS | Area de upload e lista de arquivos |
| Tab Pareceres e Analises | PASS | Sub-tabs e empty states funcionais |

## Screenshots

### Producao WeDOTalent (em `attached_assets/`)

| # | Arquivo | Conteudo | Bugs Relacionados |
|---|---|---|---|
| P1 | `Screen_Shot_..._1.23.34_PM` | Preview aberto, Perfil topo | D01, D03, D05, D06, D07 |
| P2 | `Screen_Shot_..._1.23.56_PM` | Perfil scrollado (skills, requisitos) | D10, D12, D11 |
| P3 | `Screen_Shot_..._1.24.14_PM` | Perfil scrollado (idiomas, remuneracao) | D15, D16 |
| P4 | `Screen_Shot_..._1.24.35_PM` | Atividades (preview) | D17, D19, D20 |
| P5 | `Screen_Shot_..._1.25.00_PM` | Atividades (entries) | D18, D19 |
| P6 | `Screen_Shot_..._1.25.00_PM` (2) | Atividades (entries, duplicata) | D18, D19 |
| P7 | `Screen_Shot_..._1.25.58_PM` | Atividades (full page expandido) | D18, D21, D22 |

### Producao WeDOTalent — Sessao 2 (em `attached_assets/`, candidato Lucas Campos)

| # | Arquivo (timestamp) | Conteudo | Bugs Novos |
|---|---|---|---|
| V1 | `3.29.00_PM` | Lista candidatos (15 perfis) + preview lateral Perfil Completo topo: Parecer LIA "Aguardando triagem", Analise Score 80% Alta Confianca, Resumo azul, Pontos Positivos, Skills Principais (Java/Spring/REST/SQL/Git/Ingles/Python/Angular), Skills Nao Encontradas (Delphi/PHP/C#/C), Resumo por Prioridade (Essencial 3req, Importante 5req) | VUE-NEW-01 |
| V2 | `3.29.14_PM` | Perfil Completo scroll: Resumo Prioridade completo (Essencial 3/0/0, Importante 4/0/1), Avaliacao por Requisitos (8, colapsado), Insights da Query (8, colapsado), Perguntas Sugeridas (3, colapsado), Mapa de Skills 39 itens (pl/sql, javascript, websphere, python, weblogic, sql server, pascal, mysql, Java, Spring, Angular, Git, Web Services REST, SCRUM, PostgreSQL, Desenvolvimento Web, C#, PHP, Delphi, Struts, Hibernate, JSF, Maven, jQuery, Kanban, Oracle WebCenter Sites, AEM, PostgreSQL, Web Services, DevOps, REST, SQL, Jenkins, Spring Framework, REST APIs, Tomcat, JBoss, Ingles, MongoDB) | — |
| V3 | `3.29.29_PM` | Experiencia Profissional: 6 cargos (programador java Jul/2018-, analista software senior Ago/2014-Jun/2018 CI&T, desenvolvedor java Jun/2014-Jul/2014 Cpqd, programador pleno ii Set/2011-Out/2013 Luxfacta, programador junior Set/2010-Fev/2011 Luxfacta), Formacao Academica "Nao informado", Idiomas "Nao informado", inicio Remuneracao e Beneficios | — |
| V4 | `3.29.41_PM` | Remuneracao: Salario Mensal Anualizado 13,33x, Subtotal Remuneracao BRL 0,00, Beneficios vazio, Remuneracao Total Anual BRL 0,00 (highlight verde), Endereco parcial | VUE-NEW-02 |
| V5 | `3.29.54_PM` | Tab Atividades: Feed 4 atividades, filtro "Todo periodo", sub-filtros (Todas/Emails/Entrevistas/Testes/LIA/...), Timeline vertical verde/roxa. Atividade 1: "Inscrito em vaga - Back-end Senior Software Engineer" tag Criacao, realizado por anderson ha 68 dias. Log Atualizado: **JSON RAW EXPOSTO** — dados brutos do candidato visiveis | VUE-BUG-01 CRITICO |
| V6 | `3.30.06_PM` | Atividades scroll: **JSON RAW COMPLETO EXPOSTO** — skills array, applies array, selective_process_name "Rejected"/"Submission", linkedin URL, role_name "Programador Java", sectors_a, businesses, created_at ISO timestamp — DADOS SENSIVEIS VISIVEIS | VUE-BUG-01 CRITICO |
| V7 | `3.30.24_PM` | Atividades: "Inscrito em vaga - Desenvolvedor Java" tag Criacao, ha 152 dias por anderson. Log Criacao expandido: Resumo Id->1173, Name->Questt Candidate 111710, Email->lucas.pcampos@outlook.com, Account->2 | VUE-BUG-02 |
| V8 | `3.30.38_PM` | Atividades: mesmo "Inscrito em vaga - Back-end Senior Software Engineer", Log Atualizado com **JSON RAW novamente** — Name: Questt Candidate 111710 -> Lucas Campos, Phone, Gender, skills array completo | VUE-BUG-01 CRITICO |
| V9 | `3.30.54_PM` | Atividades scroll: texto bruto de experiencia profissional (nao formatado), mesma inscricao Desenvolvedor Java + Log Criacao | VUE-BUG-03 |
| V10 | `3.31.10_PM` | Log Criacao expandido: Campos Alterados com accordion — Id (vazio->1173), Name (vazio->Questt Candidate 111710), Email (->lucas.pcampos@outlook.com), Account Id (vazio->2). Botao "Desfazer" visivel | — |
| V11 | `3.31.22_PM` | Tab Arquivos: "Arquivos e Documentos", area drag-drop "Arraste arquivos ou clique para selecionar — PDF, DOC, DOCX, JPG, PNG, MP4 Max 10MB". Sem arquivos listados (vazio) | — |
| V12 | `3.31.35_PM` | Tab Curriculo: "1 linhas, 2903 caracteres", Copiar + Ver mais. Conteudo: **HTML RAW** — `<p>Lucas Campos Desenvolvedor Java Senior na CI&amp;T Campinas...` com tags HTML visiveis ao usuario | VUE-BUG-04 CRITICO |
| V13 | `3.32.04_PM` | Candidato Davi Guides (DG, ID 4701, Score 88%, Alta Confianca, Baseado em Rubrica). Resumo: "Candidato experiente em Python backend, AWS e SQL, com ingles avancado e vivencia em microservicos." Pontos Positivos (2): progressao carreira + experiencia diversas tecnologias. Skills Principais: python/sql/aws/docker/kubernetes/restful webservices/ci-cd. Skills Nao Encontradas: php/as3/flex. Resumo Prioridade: Essencial 3 (3/0/0), Importante 2 (2/0/0), Desejavel 1 (1/0/0) | — |
| V14 | `3.32.16_PM` | Davi Guides — Avaliacao por Requisitos (6) colapsado, Insights da Query (6) EXPANDIDO: "Experiencia em desenvolvimento Python" (Essencial, evidencias: Senior python backend developer Dataart 2022-presente, Staff python backend engineer Facily 2022), "Experiencia em desenvolvimento backend" (Essencial, evidencias: Microservices oriented architecture, Wordpress plug-in postgresql+php), "Experiencia com AWS" (Importante, evidencias: docker containers on aws, fastapi k8s rancher), "Experiencia com SQL" (Importante) | VUE-GOOD-01 |
| V15 | `3.32.36_PM` | Davi Guides — Perguntas Sugeridas (3) EXPANDIDO: 1) "Pode detalhar sua experiencia com otimizacao de queries SQL?", 2) "Quais servicos AWS voce utilizou em seus projetos?", 3) "Como voce aplicou metodologias ageis em seus projetos?". Mapa de Skills 7 itens (python/sql/aws/docker/kubernetes/restful webservices/ci-cd). Experiencia Profissional: staff python backend engineer Jan/2022-Set/2022 Facily, senior python backend developer Out/2018-Dez/2021 Quiteja, senior python backend developer Jan/2017-Set/20.. Freelancer | VUE-GOOD-02 |
| V16 | `image_1775241260428` | Davi Guides — Tooltip "Adicionar a vaga" visivel no hover do icone. **Unico icone com tooltip funcional** dos 9 icones de acao no header. Os outros 8 nao mostram tooltip | VUE-BUG-05 |
| V17 | `3.36.14_PM` | Davi Guides — **LAYOUT: Preview ocupa 100% da altura** da viewport, colado ao topo da tela (sem margem superior). Header do preview (avatar DG, Score 88, icones) inicia direto abaixo da barra do browser. Sem espacamento entre preview e tabela de candidatos a esquerda. Perguntas Sugeridas + Mapa de Skills + Experiencia Profissional visiveis. Ausencia de controle de largura do painel | VUE-BUG-06, VUE-BUG-07, VUE-BUG-08 |
| V18 | `3.36.31_PM` | Carolina Mendez (CM, CA8749, senior, 5.0 anos, LGPD) — **LAYOUT: Preview inicia ACIMA dos filtros** (Selecionar Todos, Filtros, Colunas), empurrando header "Novo Candidato" + "Nova Busca" para fora. Nenhum gap/espacamento entre borda esquerda da tabela e borda direita do preview. Painel de preview nao tem handle de resize. Datas raw "2016-02-01 - 2020-12-01" na Formacao Academica. Cursos e Certificacoes + Idiomas: "Nao informado" | VUE-BUG-06, VUE-BUG-07, VUE-BUG-08 |

### Replit Referencia (em `plataforma-lia/docs/screenshots/` e `attached_assets/`)

| # | Arquivo | Conteudo |
|---|---|---|
| R1 | `replit-ref-home.jpg` | Pagina principal Funil de Talentos |
| R2 | `replit-ref-atividades-tab.jpg` | Tab Atividades com filtros e layout |
| R3 | `Screen_Shot_2.40.26_PM` | Tab Arquivos — estado vazio, drag-drop, "+ Adicionar Arquivo" |
| R4 | `Screen_Shot_2.40.46_PM` | Tab Arquivos — 4 arquivos com categorias coloridas e status |
| R5 | `Screen_Shot_2.40.56_PM` | Tab Arquivos — videos entrevista + audio triagem com badges |
| R6 | `Screen_Shot_2.41.15_PM` | FilePreviewModal — PDF com paginacao "1/5" |
| R7 | `Screen_Shot_2.41.36_PM` | FilePreviewModal — Video com player + transcricao + Analise LIA |
| R8 | `Screen_Shot_2.41.48_PM` | FilePreviewModal — Parecer LIA: Pontos Fortes/Atencao, Score 91% |
| R9 | `Screen_Shot_2.44.39_PM` | Tab Perfil — erro resumo, Experiencia com border-left, duracao 2.9 anos |
| R10 | `Screen_Shot_2.44.52_PM` | Tab Perfil — Formacao, Cursos, Idiomas "Nao informado", Remuneracao R$ 32.211 |
| R11 | `Screen_Shot_2.45.03_PM` | Tab Perfil — Remuneracao CLT/PJ, Preferencias com bugs "undefined"/"null" |
| R12 | `Screen_Shot_2.45.24_PM` | Tab Atividades — 8 filtros, "+ Nova Atividade", agrupamento "Hoje", cards com status |
| R13 | `Screen_Shot_2.45.49_PM` | Tab Atividades — Avaliacao LIA 91%, Candidatura LinkedIn "Nova", "Esta Semana" |
| R14 | `Screen_Shot_2.46.11_PM` | Tab Atividades — Rubrica 89% "Fit Alto", Email "Visualizado", Assessment 85% |
| R15 | `Screen_Shot_2.46.28_PM` | Tab Atividades (full page) — job-id nos cards, layout expandido |
| R16 | `Screen_Shot_2.46.39_PM` | Tab Atividades — Triagem voz 93% "Concluida", 4 perguntas respondidas |
| R17 | `Screen_Shot_2.47.01_PM` | Tab Pareceres — sub-tabs "Pareceres da LIA" + "Analises", empty state |
| R18 | `Screen_Shot_2.47.24_PM` | Tab Atividades — card expandido: email completo com De/Para/Cc/Assunto/corpo |
| R19 | `Screen_Shot_2.47.46_PM` | Tab Atividades — card expandido: Avaliacao LIA com 4 metricas coloridas + Pontos Fortes |
| R20 | `Screen_Shot_2.53.14_PM` | Atividades — Avaliacao LIA expandida: 5 Pontos Fortes + Recomendacao completa com 3 focos |
| R21 | `Screen_Shot_2.53.47_PM` | Atividades — Candidatura LinkedIn expandida: ID aplicacao, metodo Easy Apply, dispositivo, botoes Baixar CV + Ver LinkedIn |
| R22 | `Screen_Shot_2.54.09_PM` | Atividades — Triagem por Voz expandida: 4/4 perguntas, Duracao 4:32, Completude 100%, Confianca 97%, Destaques |
| R23 | `Screen_Shot_2.54.23_PM` | Atividades — Triagem por Voz: Destaques (5 bullets) + Impressao Geral + botao "Ouvir Triagem" |

**Total:** 23 screenshots React + 7 screenshots Vue Sessao 1 (P1-P7) + 18 screenshots Vue Sessao 2 (V1-V18: Lucas Campos V1-V12, Davi Guides V13-V17, Carolina Mendez V18) = **48 screenshots documentados.**

### Bugs Vue NOVOS descobertos na Sessao 2

| ID | Severidade | Descricao | Screenshots |
|---|---|---|---|
| VUE-BUG-01 | **CRITICO** | **JSON RAW exposto em Atividades** — Log de Atualizacao mostra objeto JSON completo do candidato (skills array, applies array, linkedin URL, email, phone, gender, selective_process "Rejected") diretamente na UI. Vazamento de dados sensiveis e estrutura interna. | V5, V6, V8 |
| VUE-BUG-02 | ALTO | **Dados internos em Log de Criacao** — Mostra "Questt Candidate 111710" (nome interno do sistema) + email pessoal lucas.pcampos@outlook.com + Account Id diretamente no feed de atividades | V7, V10 |
| VUE-BUG-03 | MEDIO | **Texto bruto de experiencia nao formatado** — Experiencia profissional aparece como texto plain sem quebras de linha ou formatacao adequada no feed de atividades | V9 |
| VUE-BUG-04 | **CRITICO** | **HTML RAW na Tab Curriculo** — Tags HTML visiveis ao usuario (`<p>`, `&amp;`) em vez de conteudo renderizado. Mostra "1 linhas, 2903 caracteres" indicando que o curriculo e armazenado como HTML mas exibido como texto | V12 |
| VUE-NEW-01 | INFO | **Parecer LIA "Aguardando triagem"** — Card Parecer LIA mostra loading state permanente. Pode indicar falta de processamento ou timeout | V1 |
| VUE-NEW-02 | BAIXO | **Remuneracao BRL 0,00** — Remuneracao Total Anual mostra BRL 0,00 com multiplicador 13,33x aplicado a zero. Deveria ocultar quando nao informado | V4 |
| VUE-BUG-05 | MEDIO | **Tooltips ausentes nos icones de acao** — Dos 9 icones de acao no header do candidato (email, telefone, agenda, copiar, adicionar vaga, comparar, favoritar, desabilitar, notas), apenas "Adicionar a vaga" tem tooltip funcional. Os outros 8 nao mostram tooltip no hover, dificultando a descoberta de funcionalidade | V16 |
| VUE-BUG-06 | **ALTO** | **Preview colado ao topo da viewport** — Painel de preview ocupa 100% da altura da tela, comecando direto abaixo da barra do browser sem nenhuma margem/padding superior. Header do candidato (avatar, nome, score) colado ao topo absoluto. No React (Replit), o preview e um drawer/overlay que respeita o header da aplicacao e inicia abaixo dos controles ("Novo Candidato", filtros). Sobreposicao parcial com D01/D03 (FIX-01). | V17, V18 |
| VUE-BUG-07 | **ALTO** | **Sem espacamento entre preview e tabela** — Zero gap/margem entre a borda esquerda da tabela de candidatos e a borda direita do painel de preview. O preview "cola" diretamente na tabela, prejudicando a legibilidade e a separacao visual. No React (Replit), o drawer tem sombra + gap explicito separando-o da lista. Sobreposicao parcial com D01/D02 (FIX-01). | V17, V18 |
| VUE-BUG-08 | MEDIO | **Ausencia de controle de largura (resize handle)** — Painel de preview nao oferece nenhum mecanismo para o usuario ajustar a largura (drag handle, snapping, ou presets). O preview empurra a tabela e os botoes de acao ("Novo Candidato", "Nova Busca", "Selecionar Todos", "Filtros", "Colunas") para fora da area visivel. No React (Replit), a largura e fixa em overlay sem alterar o layout da tabela. Sobreposicao parcial com D02 (FIX-01). | V17, V18 |
| VUE-GOOD-01 | POSITIVO | **Insights da Query funcional** — 6 insights com evidencias reais, tags Essencial/Importante, citacoes do curriculo. Feature ausente no React | V14 |
| VUE-GOOD-02 | POSITIVO | **Perguntas Sugeridas funcional** — 3 perguntas contextuais geradas pela IA. Feature ausente no React | V15 |

---

# PARTE 2: BUGS VISUAIS + CODE FIXES

## 2.1 LAYOUT GERAL DO PREVIEW

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D01 | **Layout do preview** | Preview empurra header e botoes da tabela ("Novo Candidato", "Nova Busca") para fora da area visivel | Drawer overlay que NAO altera layout da tabela | **CRITICO** |
| D02 | **Largura do preview** | ~50% em preview, 100% em full page, sem transicao suave | Drawer lateral com largura fixa (overlay) ou pagina full separada | ALTO |
| D03 | **Header fixo** | Header nome/avatar/botoes colado ao topo da viewport mesmo ao scrollar tabela | Header dentro do scroll natural da pagina de detalhe | ALTO |
| D04 | **Proporcao conteudo** | Cards grandes com muito padding, scroll excessivo | Cards compactos com `p-2.5` (10px), `text-xs` (12px), densidade maxima | MEDIO |

---

## 2.2 HEADER DO CANDIDATO

**Screenshots React:** `Screen_Shot_2.44.39_PM`, `Screen_Shot_2.45.49_PM`

| ID | Elemento | Vue (Producao) | React (Replit — dos screenshots) | Sev. |
|----|---------|---------------|----------------------------------|------|
| D05 | **Avatar** | `v-avatar size="40"`, iniciais inline, sem indicador status | Avatar "TN" circular com fundo cinza + badge "senior" (chip cinza) + "13.0 anos" + "LGPD" (chip vermelho) | ALTO |
| D06 | **ID Badge** | ID numerico raw `4681` | `TH1886` — prefixo + numerico, chip outline arredondado | BAIXO |
| D07 | **Redes sociais** | Apenas LinkedIn | **Barra de 10 icones** separada por `|`: mail, phone, calendar, clipboard, chart, star, comments `|` linkedin, message, fork, X, Behance | **CRITICO** |
| D08 | **Datas** | Nenhuma data no header | Duas datas com icones: "📅 13 de mar. de 2026" (cadastro) + "🕐 13 de mar. de 2026" (atualizacao) | ALTO |
| D09 | **Botao LIA** | Ausente | Botao Brain (⊕) circular no canto superior direito do header | ALTO |
| D09c | **Botoes expand/close** | Apenas fechar (X) | Botao expand (⛶) para full page + botao fechar (X) | MEDIO |

### Codigo Vue ATUAL — preview.vue (linhas 140-230)

```vue
<div class="d-flex py-3 px-3 ga-3 border-b border-border-color border-opacity-100">
  <v-avatar size="40">
    <img v-if="candidate_record.avatar_url" :src="candidate_record.avatar_url" />
    <span v-else-if="candidate_record.name" class="f16 text-primary font-weight-medium">
      {{ candidate_record.name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase() }}
    </span>
  </v-avatar>
  <div>
    <h2 class="f13 font-weight-semibold font-serif">{{ candidate_record.name }}</h2>
    <span class="f9 text-primary border border-primary rounded-pill px-1">{{ candidate_record.id }}</span>
    <v-progress-circular :model-value="candidateScore" :size="28" :width="3" :color="scoreColor">
      <span class="f9 font-weight-bold">{{ candidateScore }}</span>
    </v-progress-circular>
    <span class="f11 text-body-light">{{ candidate_record.role_name }}</span>
    <Icon name="lucide-linkedin" :color="candidate_record.linkedin ? 'primary' : 'body-light'" />
  </div>
</div>
```

### CORRECAO — Header Vue (D05-D09)

```vue
<div class="d-flex py-2 px-2 ga-2 border-b border-border-color border-opacity-100">
  <v-avatar size="40" class="position-relative">
    <div v-if="candidateStatus" class="position-absolute rounded-circle"
      :class="`border-2 border-${statusColor}`" style="inset: -2px; z-index: 1;" />
    <img v-if="candidate_record.avatar_url" :src="candidate_record.avatar_url" />
    <span v-else class="f16 text-primary font-weight-medium d-flex align-center justify-center w-100 h-100"
      style="background-color: rgba(var(--v-theme-primary), 0.2)">
      {{ getInitials(candidate_record.name) }}
    </span>
  </v-avatar>
  <div class="flex-grow-1" style="min-width: 0;">
    <div class="d-flex align-center ga-1 flex-wrap mb-0">
      <h2 class="f12 font-weight-semibold text-on-surface">{{ candidate_record.name }}</h2>
      <span class="f8 font-mono text-primary border border-primary border-opacity-100 rounded-pill px-1"
        style="background-color: rgba(var(--v-theme-primary), 0.15);">
        {{ formatShortId(candidate_record.id) }}
      </span>
    </div>
    <p class="f10 text-body-light mb-1">
      {{ candidate_record.role_name }} <span class="mx-1">•</span> {{ candidate_record.current_company }}
    </p>
    <div class="d-flex align-center ga-2 f9 text-body-light mb-1">
      <span class="d-flex align-center ga-1">
        <Icon name="lucide-calendar" size="10" /> Cadastrado em {{ formatDate(candidate_record.created_at) }}
      </span>
      <span class="d-flex align-center ga-1">
        <Icon name="lucide-clock" size="10" /> Atualizado em {{ formatDate(candidate_record.updated_at) }}
      </span>
    </div>
    <div class="d-flex align-center ga-1">
      <Icon name="lucide-linkedin" size="14" :color="candidate_record.linkedin ? 'primary' : 'body-light'"
        @click="openUrl(candidate_record.linkedin)" />
      <Icon name="lucide-github" size="14" :color="candidate_record.github ? 'on-surface' : 'body-light'"
        @click="openUrl(candidate_record.github)" />
      <Icon name="lucide-globe" size="14" :color="candidate_record.portfolio ? 'on-surface' : 'body-light'"
        @click="openUrl(candidate_record.portfolio)" />
    </div>
  </div>
</div>
```

```js
// Adicionar ao <script setup> de preview.vue:
function formatShortId(id) {
  if (!id) return ''
  const hash = String(id).split('').reduce((a, c) => ((a << 5) - a + c.charCodeAt(0)) | 0, 0)
  const hex = Math.abs(hash).toString(16).toUpperCase().padStart(6, '0').slice(0, 6)
  return hex.slice(0, 2).replace(/[0-9]/g, c => String.fromCharCode(65 + Number(c))) + hex.slice(2, 6)
}
function openUrl(url) {
  if (url) window.open(url.startsWith('http') ? url : `https://${url}`, '_blank')
}
```

---

## 2.3 BOTOES DE ACAO

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D10 | **Labels nos botoes** | Icones-only sem texto, dificil identificar | Icone + texto: "Email", "WhatsApp", "Triagem WSI", etc. | ALTO |
| D11 | **Acoes ausentes** | Faltam Triagem WSI, Adicionar a Lista, Ocultar, Feedback | 9 botoes de acao rapida com callbacks | ALTO |

### Codigo Vue ATUAL — preview.vue (linhas 230-260)

```vue
<div class="d-flex align-center ga-1 py-1 px-3 border-b border-border-color">
  <v-menu>
    <template #activator="{ props }">
      <v-btn v-bind="props" size="small" variant="tonal" color="primary">
        <Icon name="lucide-ellipsis" size="14" />
      </v-btn>
    </template>
    <v-list density="compact">
      <v-list-item @click="openFullPage">Abrir Completo</v-list-item>
      <v-list-item @click="addToJob">Adicionar a Vaga</v-list-item>
      <v-list-item @click="sendEmail">Enviar Email</v-list-item>
      <v-list-item @click="startEnrich">Enriquecer</v-list-item>
    </v-list>
  </v-menu>
  <v-tooltip v-for="action in quickActions">
    <template #activator="{ props }">
      <v-btn v-bind="props" icon variant="text" size="small" @click="action.handler">
        <Icon :name="action.icon" size="16" />
      </v-btn>
    </template>
    <span>{{ action.tooltip }}</span>
  </v-tooltip>
</div>
```

### Diferenca detalhada de botoes

| Botao/Acao | Vue | React | Delta |
|---|---|---|---|
| Email | Via menu dropdown | Botao direto com icone | React mais acessivel |
| WhatsApp | Nao implementado | Botao direto | **Ausente** |
| Triagem WSI | Nao implementado | Botao com callback | **Ausente** |
| Agendamento | Nao implementado | Botao com callback | **Ausente** |
| Feedback | Nao implementado | Botao com callback | **Ausente** |
| LIA Chat | Nao implementado | Botao "Perguntar a LIA" abre modal | **Ausente** |
| Adicionar a Vaga | Menu dropdown | Menu dropdown | Equivalente |
| Enriquecer | Menu + dialog creditos | Nao implementado | **Vue tem, React nao** |
| Favoritar | Nao implementado | Toggle coracao | **Ausente** |
| Navegacao prev/next | Nao implementado | Setas `<` `>` com `1 de 42` | **Ausente** |

---

## 2.4 TABS E NAVEGACAO

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D12 | **Tab truncada** | Tab "Arquivos" aparece como "Arq..." no preview | Tabs com nomes completos | MEDIO |
| D13 | **Tab Pareceres** | NAO EXISTE como tab | Tab "Pareceres e Analises" com historico + subtabs | **CRITICO** |
| D14 | **Tab Curriculo** | Aparece em full page mas nao no preview | Nao existe — CVs ficam na tab Arquivos | MEDIO |

### Codigo Vue ATUAL — preview.vue (linhas 260-300)

```vue
<v-tabs v-model="active_tab" grow density="compact" class="f11 font-weight-medium">
  <v-tab value="profile">
    <Icon name="lucide-user" size="14" class="mr-1" />Perfil Completo
  </v-tab>
  <v-tab value="activities">
    <Icon name="lucide-clock" size="14" class="mr-1" />Atividades
  </v-tab>
  <v-tab value="files">
    <Icon name="lucide-file-text" size="14" class="mr-1" />Arquivos
  </v-tab>
  <v-tab value="curriculum">
    <Icon name="lucide-file" size="14" class="mr-1" />Curriculo
  </v-tab>
</v-tabs>
```

### CORRECAO — Adicionar Tab Pareceres (D13)

```vue
<!-- Adicionar ao v-tabs em preview.vue -->
<v-tab value="opinions">
  <Icon name="lucide-brain" size="14" class="mr-1" />
  Pareceres
  <v-chip v-if="opinionsCount > 0" size="x-small" color="primary" variant="tonal" class="ml-1 f9">
    {{ opinionsCount }}
  </v-chip>
</v-tab>

<!-- Adicionar ao v-window -->
<v-window-item value="opinions">
  <CandidateOpinionsTab
    :candidate="candidate_record"
    :opinions-history="opinionsHistory"
    :is-loading="isLoadingOpinions"
  />
</v-window-item>
```

---

## 2.5 TAB PERFIL — RESUMO E PARECER LIA

**Screenshots React:** `Screen_Shot_2.44.39_PM`

| ID | Elemento | Vue (Producao) | React (Replit — dos screenshots) | Sev. |
|----|---------|---------------|----------------------------------|------|
| D15 | **Erro no resumo** | "Aguardando triagem" com loading, sem botao de acao | Exibe "Nao foi possivel gerar o resumo" com botao "Tentar novamente" — erro visivel mas com recovery | **CRITICO** |
| D16 | **Score sem contexto** | Badge "87" sem escala de cores, sem label "Alta Confianca" | Score com barra circular colorida + label + badge metodo | ALTO |

---

## 2.6 TAB PERFIL — EXPERIENCIA E FORMACAO

**Screenshots React:** `Screen_Shot_2.44.39_PM`, `Screen_Shot_2.44.52_PM`

| ID | Elemento | Vue (Producao) | React (Replit — dos screenshots) | Sev. |
|----|---------|---------------|----------------------------------|------|
| D16b | **Experiencia visual** | Titulo, empresa, datas, texto plano | **Border-left laranja** por experiencia + empresa ao lado do titulo + **duracao calculada** "(2.9 anos)" + descricao abaixo | ALTO |
| D16e | **Formacao datas** | Datas formatadas | Datas em **formato ISO raw** "2020-02-01 - 2022-12-01" — deveria ser formatado | BUG MEDIO |
| D16f | **Cursos e Certificacoes** | Nao visivel | Card "Cursos e Certificacoes" com "Nao informado" em italico cinza | BAIXO |

---

## 2.7 TAB PERFIL — REMUNERACAO, PREFERENCIAS E BUGS

**Screenshots React:** `Screen_Shot_2.44.52_PM`, `Screen_Shot_2.45.03_PM`

| ID | Elemento | Vue (Producao) | React (Replit — dos screenshots) | Sev. |
|----|---------|---------------|----------------------------------|------|
| D16c | **Remuneracao** | "BRL 0,00" para todos os campos | Salario Atual: **R$ 32.211,00** formatado, Pretensao Salarial: "Nao informado", Expectativa CLT: "Nao informado", Expectativa PJ: "Nao informado" | MEDIO |
| D16d | **Idiomas** | "Nao informado" | Card "Idiomas" com "Nao informado" em italico | BAIXO |
| D16g | **BUG: "undefined" exibido** | N/A (Vue nao tem campo) | Preferencias: "Aceita Mudanca: **undefined**" — valor `undefined` renderizado como texto | **BUG CRITICO** |
| D16h | **BUG: "null" exibido** | N/A (Vue nao tem campo) | Preferencias: "Disponibilidade Viagens: **null**" — valor `null` renderizado como texto | **BUG CRITICO** |
| D16i | **LGPD sem consentimento** | Nao exibe | "Consentimento LGPD: ✗ Nao consentido" (vermelho) — exibido corretamente como alerta | MEDIO |
| D16j | **Contradicao dados** | N/A | "Modelo de Trabalho: remoto" MAS "Aceita Remoto: Nao" — dados contraditorios sem validacao | **BUG ALTO** |
| D15b | **Preferencias Pessoais** | Nao visivel | Card completo: Modelo Trabalho, Tipo Contrato (CLT), Aceita Remoto, Aceita Mudanca, Disp. Viagens, LGPD | MEDIO |

### Anatomia da Secao Preferencias (React — do screenshot)

```
┌─────────────────────────────────────────────┐
│ 🧑 Preferências e Dados Pessoais           │
│                                             │
│ Modelo de Trabalho              remoto      │
│ Tipo de Contrato                CLT         │
│ Aceita Remoto                   Não         │ ← contradição com "remoto" acima
│ Aceita Mudança                  undefined   │ ← BUG: valor JS renderizado
│ Disponibilidade Viagens         null        │ ← BUG: valor JS renderizado
│ Consentimento LGPD    ✗ Não consentido      │ ← vermelho, correto
└─────────────────────────────────────────────┘
```

---

## 2.7b TAB PERFIL — SECOES AUSENTES

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D09b | **Card Score Analysis desproporcionado** | Grafico circular grande demais, ocupa muito espaco vertical | Grid compacto 2 colunas com barra de progresso por metrica | MEDIO |
| D10b | **Skills sem categorias** | 37 itens planos sem agrupamento | Mapa categorizado: Backend, Frontend, Data, DevOps + cores por fonte | ALTO |
| D10c | **Skills sem fonte** | Todas as badges iguais, impossivel saber se CV/LinkedIn/LIA | Cores distintas: `wedo-cyan` para LIA, `wedo-magenta` para Interesses | MEDIO |
| D11b | **Acordeoes sem preview** | "Avaliacao por Requisitos (7)" — apenas titulo + chevron | Conteudo exibido diretamente com scroll natural | MEDIO |
| D12b | **ExperienceHighlight** | Nao existe | Card no topo do perfil com resumo gerado pela LIA | MEDIO |
| D13b | **Perfil LinkedIn** | Nao existe | Card com headline, idade estimada, seguidores, conexoes | MEDIO |
| D14b | **Indicadores especiais** | Nao existe | Badges: Open to Work, Top University, Decision Maker, LCNU | MEDIO |

---

## 2.8 TAB ATIVIDADES

**Screenshots React:** `Screen_Shot_2.45.24_PM`, `Screen_Shot_2.45.49_PM`, `Screen_Shot_2.46.11_PM`, `Screen_Shot_2.46.28_PM`, `Screen_Shot_2.46.39_PM`, `Screen_Shot_2.47.24_PM`, `Screen_Shot_2.47.46_PM`

### Bugs Identificados

| ID | Elemento | Vue (Producao) | React (Replit — dos screenshots) | Sev. |
|----|---------|---------------|----------------------------------|------|
| D17 | **Cards nao expandem** | Cards estaticos sem interacao ao clicar | Cards com chevron (v) que expande: email mostra De/Para/Cc/Assunto/corpo completo; Avaliacao LIA mostra 4 metricas coloridas + Pontos Fortes | **CRITICO** |
| D18 | **JSON raw visivel** | Card "Log de Atualizacao" exibe dados raw (`"url": "/recruiter/..."`) | Cada tipo formatado: email com campos, entrevista com horario, avaliacao com scores, candidatura com fonte | **CRITICO** |
| D19 | **Cards desproporcionais** | Card "Resumo das Alteracoes" ocupa tela inteira com texto bruto | Cards com altura fixa e expand on-click | **CRITICO** |
| D20 | **Filtros truncados** | Preview mostra apenas "Todas, Emails, Entrevistas", demais ocultos | **8 filtros chip sempre visiveis:** Todas (preto), Emails, Entrevistas, Testes, LIA, Ofertas, Inscricoes, Avaliacoes — cada um com icone proprio | ALTO |
| D21 | **Sem header de controle** | Nenhum header na secao | Header: "Feed de Atividades **11**" + select "Todo periodo" (dropdown) + botoes sort/view + botao "+ Nova Atividade" | ALTO |
| D22 | **Sem Nova Atividade** | Nao ha botao para adicionar | Botao "+ Nova Atividade" proeminente no header | ALTO |
| D23 | **Sem agrupamento por data** | Lista cronologica sem separadores | Agrupamento visual: "○ **Hoje**", "○ **Esta Semana**" com circulo vazio como separador | ALTO |
| D24 | **Dots sem significado** | Verde/roxo sem explicacao | Color-coded por tipo: azul (email ✉), verde (sistema/candidatura 📋), laranja (LIA ⊕), roxo (triagem 🎤) | MEDIO |

### Anatomia da Tab Atividades (React — dos screenshots)

```
┌─────────────────────────────────────────────────────────────┐
│ ⚡ Feed de Atividades  11   [Todo período ▾]  [↕] [☰]      │
│                                        (⊕) Nova Atividade  │
│                                                             │
│ [Todas] [📧Emails] [📝Entrevistas] [🧪Testes] [🧠LIA]     │
│ [💼Ofertas] [📋Inscrições] [🎯Avaliações]                  │
│                                                             │
│ ○ Hoje                                                      │
│ ●─── Email convite para entrevista  [Enviado]  v            │
│ │    🏢 Tech Lead Mobile                                    │
│ │    Maria Santos • Hoje, 10:30                             │
│ │    Convite para entrevista técnica com time...            │
│ │                                                           │
│ ●─── Entrevista técnica agendada   [Confirmada]  v          │
│ │    🏢 Tech Lead Mobile                                    │
│ │    Sistema • Hoje, 09:15                                  │
│ │    Entrevista com Time de Engenharia 15/01 às 14:00       │
│ │                                                           │
│ ○ Esta Semana                                               │
│ ●─── Avaliação automática da LIA   [91.0%]                  │
│ │    concluída              [Altamente Recomendado]  v      │
│ │    🏢 Tech Lead Mobile                                    │
│ │    LIA • Ontem, 16:45                                     │
│ │    Análise de CV e perfil LinkedIn com score de 91%       │
│ │                                                           │
│ ●─── Candidatura recebida via LinkedIn  [Nova]  v           │
│      🏢 Tech Lead Mobile                                    │
│      Sistema • Ontem, 14:20                                 │
│      Candidato aplicou para a vaga...                       │
└─────────────────────────────────────────────────────────────┘
```

### Tipos de Atividade Identificados (dos screenshots)

| Tipo | Icone | Cor dot | Status badges | Card expandido mostra |
|------|-------|---------|---------------|----------------------|
| Email enviado | ✉ | Azul | Enviado, Visualizado | De/Para/Cc/Assunto + corpo email completo |
| Entrevista | 📅 | Verde | Confirmada | Detalhes do agendamento |
| Avaliacao LIA | ⊕ | Laranja | Score% + Nivel | **4 metricas** (Tecnico/Fit Cultural/Experiencia/Soft Skills) + **5 Pontos Fortes** com checkmarks verdes + **Recomendacao** texto completo com 3 focos de entrevista |
| Candidatura | 📋 | Verde | Nova | Grid 2x2: ID Aplicacao (APP-2026-001234), Metodo (Easy Apply), Recebido em (data+hora), Dispositivo (iPhone 15 Pro) + botoes **[Baixar CV]** e **[Ver LinkedIn]** |
| Rubrica CV | ⊕ | Laranja | Score% + Fit | Analise detalhada de aderencia CV vs requisitos |
| Follow-up | ✉ | Azul | Visualizado | Corpo do email completo |
| Assessment | ⊕ | Verde | Score% + Nivel | Resultado comportamental |
| Triagem voz | 🎤 | Vermelho | Score% + Status | **3 metricas** (Duracao 4:32, Completude 100%, Confianca 97%) + **Destaques** (5 bullets) + **Impressao Geral** (texto) + botao **[▶ Ouvir Triagem]** |

### Card Expandido — Email (Screenshot 2.47.24)

```
┌─────────────────────────────────────────────────────────────┐
│ ● Email de convite para entrevista enviado  [Enviado]  ^    │
│   🏢 Tech Lead Mobile  Maria Santos • Hoje, 10:30          │
│   Convite para entrevista técnica com time de engenharia    │
│   agendada para 15/01                                       │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ De:      maria.santos@wedotalent.com.br               │ │
│   │ Para:    bruno.carvalho@email.com                     │ │
│   │ Cc:      recrutamento@wedotalent.com.br               │ │
│   │ Assunto: Convite: Entrevista Técnica - Tech Lead      │ │
│   │          Mobile | WeDo Talent                         │ │
│   │                                                       │ │
│   │ Olá Bruno,                                            │ │
│   │                                                       │ │
│   │ Esperamos que esteja bem! É com grande satisfação     │ │
│   │ que entramos em contato para informar que sua         │ │
│   │ candidatura para a posição de Tech Lead Mobile foi    │ │
│   │ muito bem avaliada pela nossa equipe...               │ │
│   └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Card Expandido — Avaliacao LIA (Screenshot 2.47.46)

```
┌─────────────────────────────────────────────────────────────┐
│ ● Avaliação automática da LIA  [91.0%]                      │
│   concluída         [Altamente Recomendado]  ^              │
│   🏢 Tech Lead Mobile                                       │
│   LIA • Ontem, 16:45                                        │
│   Análise de CV e perfil LinkedIn com score de 91%          │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ ⊕ Avaliação Automática da LIA                        │ │
│   │                                                       │ │
│   │ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                 │ │
│   │ │94.0% │ │88.0% │ │92.0% │ │89.0% │                 │ │
│   │ │Técni.│ │Fit   │ │Exper.│ │Soft  │                 │ │
│   │ │      │ │Cultu.│ │      │ │Skills│                 │ │
│   │ └──────┘ └──────┘ └──────┘ └──────┘                 │ │
│   │  laranja   laranja   verde    teal                   │ │
│   │                                                       │ │
│   │ Pontos Fortes                                         │ │
│   │ ✔ Domínio avançado de React Native (5+ anos)          │ │
│   └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Card Expandido — Avaliacao LIA Completa (Screenshots 2.53.14 + 2.47.46)

```
┌─────────────────────────────────────────────────────────────┐
│ ● Avaliação automática da LIA  [91.0%]                      │
│   concluída         [Altamente Recomendado]  ^              │
│   🏢 Tech Lead Mobile                                       │
│   LIA • Ontem, 16:45                                        │
│   Análise de CV e perfil LinkedIn com score de 91%          │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ ⊕ Avaliação Automática da LIA                        │ │
│   │                                                       │ │
│   │ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                 │ │
│   │ │94.0% │ │88.0% │ │92.0% │ │89.0% │                 │ │
│   │ │Técni.│ │Fit   │ │Exper.│ │Soft  │                 │ │
│   │ │      │ │Cultu.│ │      │ │Skills│                 │ │
│   │ └──────┘ └──────┘ └──────┘ └──────┘                 │ │
│   │  laranja   laranja   verde    teal                   │ │
│   │                                                       │ │
│   │ Pontos Fortes                                         │ │
│   │ ✔ Domínio avançado de React Native (5+ anos)          │ │
│   │ ✔ Experiência comprovada em liderança (4 anos)        │ │
│   │ ✔ Histórico de entregas em grandes empresas           │ │
│   │   (Nubank, iFood)                                     │ │
│   │ ✔ Contribuições open source relevantes                │ │
│   │ ✔ Certificações AWS e Google Cloud                    │ │
│   │                                                       │ │
│   │ Recomendação                                          │ │
│   │ Candidato altamente qualificado para a posição de     │ │
│   │ Tech Lead Mobile. Possui experiência sólida em        │ │
│   │ liderança técnica... Recomendo fortemente agendar     │ │
│   │ entrevista técnica com foco em:                       │ │
│   │ 1. Arquitetura de sistemas mobile escaláveis          │ │
│   │ 2. Gestão de equipes multidisciplinares               │ │
│   │ 3. Estratégias de migração e modernização de apps     │ │
│   └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Card Expandido — Candidatura LinkedIn (Screenshot 2.53.47)

```
┌─────────────────────────────────────────────────────────────┐
│ ● Candidatura recebida via LinkedIn        [Nova]  ^        │
│   🏢 Tech Lead Mobile  Sistema • Ontem, 14:20               │
│   Candidato aplicou para a vaga de Tech Lead Mobile         │
│   através da integração com LinkedIn                        │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ 📋 Candidatura Recebida   [LinkedIn Jobs]             │ │
│   │                                                       │ │
│   │ ID da Aplicação          Método                       │ │
│   │ APP-2026-001234          Easy Apply                   │ │
│   │                                                       │ │
│   │ Recebido em              Dispositivo                  │ │
│   │ 13/01/2026 às 14:20:33   iPhone 15 Pro -              │ │
│   │                          LinkedIn App                 │ │
│   │                                                       │ │
│   │ [⬇ Baixar CV]  [🔗 Ver LinkedIn]                      │ │
│   └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Card Expandido — Triagem por Voz (Screenshots 2.54.09 + 2.54.23)

```
┌─────────────────────────────────────────────────────────────┐
│ ● Triagem por voz concluída    [93.0%]  [Concluída]  ^      │
│   🏢 Tech Lead Mobile  LIA • 2 dias atrás, 11:00            │
│   Candidato completou triagem de voz com 4 perguntas        │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │ 🎤 Triagem por Voz   [4/4 perguntas]                  │ │
│   │                                                       │ │
│   │ ┌──────────┐ ┌──────────┐ ┌──────────┐               │ │
│   │ │  4:32    │ │  100%    │ │   97%    │               │ │
│   │ │ Duração  │ │Completude│ │Confiança │               │ │
│   │ └──────────┘ └──────────┘ └──────────┘               │ │
│   │                                                       │ │
│   │ ✨ Destaques                                          │ │
│   │ • 8+ anos de experiência em desenvolvimento mobile    │ │
│   │ • Liderou time de 6 desenvolvedores no Nubank         │ │
│   │ • Migrou app com 5M+ usuários para micro-frontends   │ │
│   │ • Disponibilidade imediata (aviso prévio 30 dias)     │ │
│   │ • Pretensão salarial: R$ 28-32k CLT                   │ │
│   │                                                       │ │
│   │ Impressão Geral                                       │ │
│   │ Candidato demonstrou excelente comunicação,           │ │
│   │ conhecimento técnico profundo e experiência relevante │ │
│   │ em liderança. Respostas claras e objetivas, com       │ │
│   │ exemplos concretos de situações reais.                │ │
│   │                                                       │ │
│   │ [▶ Ouvir Triagem]                                     │ │
│   └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Full Page vs Preview (Screenshot 2.46.28)

No modo full page, cada card de atividade inclui o **job-id** na segunda linha:
- Preview: "🏢 Tech Lead Mobile"
- Full page: "🏢 **job-001** - Tech Lead Mobile"

### Codigo Vue ATUAL — applies.vue (30 linhas)

```vue
<template>
  <div class="pa-3">
    <AppliesTable :candidate_id="candidate_record.id" />
  </div>
</template>
```

### CORRECAO — Filtros de Atividade (D20, D21, D22)

```vue
<!-- NOVO: features/candidates/activities/ActivityFilters.vue -->
<template>
  <div class="d-flex flex-column ga-2">
    <div class="d-flex align-center justify-space-between">
      <div class="d-flex align-center ga-2">
        <Icon name="lucide-activity" size="16" />
        <span class="f12 font-weight-semibold">Feed de Atividades</span>
        <v-chip size="x-small" color="primary" variant="flat" class="f9">
          {{ totalCount }}
        </v-chip>
      </div>
      <div class="d-flex align-center ga-2">
        <v-select v-model="period" :items="periods" density="compact"
          variant="outlined" class="f10" style="max-width: 140px;" hide-details />
        <v-btn size="small" variant="tonal" color="primary" @click="$emit('new-activity')">
          <Icon name="lucide-plus" size="14" class="mr-1" /> Nova Atividade
        </v-btn>
      </div>
    </div>
    <v-chip-group v-model="selectedFilter" mandatory selected-class="text-primary">
      <v-chip v-for="f in filters" :key="f.value" :value="f.value"
        size="small" variant="tonal" class="f10">
        <Icon :name="f.icon" size="12" class="mr-1" />{{ f.label }}
      </v-chip>
    </v-chip-group>
  </div>
</template>
```

### CORRECAO — Timeline com Agrupamento (D17, D23, D24)

```vue
<!-- NOVO: features/candidates/activities/ActivityTimeline.vue -->
<template>
  <div class="d-flex flex-column">
    <template v-for="(group, idx) in groupedActivities" :key="idx">
      <div class="d-flex align-center ga-2 my-3">
        <div class="rounded-circle border" style="width: 12px; height: 12px;" />
        <span class="f11 font-weight-bold">{{ group.label }}</span>
      </div>
      <div v-for="activity in group.items" :key="activity.id"
        class="d-flex ga-3 position-relative mb-3 cursor-pointer"
        @click="toggleExpand(activity.id)">
        <div class="d-flex flex-column align-center" style="width: 24px;">
          <div class="rounded-circle d-flex align-center justify-center"
            :style="{ backgroundColor: getBgColor(activity.type), width: '24px', height: '24px' }">
            <Icon :name="getIcon(activity.type)" size="12" :color="getColor(activity.type)" />
          </div>
          <div v-if="!isLast(group, activity)" class="flex-grow-1"
            style="width: 2px; background: rgb(var(--v-theme-border-color));" />
        </div>
        <div class="flex-grow-1 pb-2">
          <div class="d-flex align-center justify-space-between">
            <span class="f11 font-weight-medium">{{ activity.title }}</span>
            <div class="d-flex align-center ga-1">
              <v-chip v-if="activity.score" size="x-small" color="primary" variant="flat">
                {{ activity.score }}%
              </v-chip>
              <v-chip size="x-small" :color="activity.statusColor" variant="tonal">
                {{ activity.statusLabel }}
              </v-chip>
              <Icon :name="expanded === activity.id ? 'lucide-chevron-up' : 'lucide-chevron-down'" size="14" />
            </div>
          </div>
          <div class="f10 text-body-light mt-1">
            🏢 {{ activity.jobTitle }}
          </div>
          <div class="f9 text-body-light">
            {{ activity.author }} • {{ formatRelativeTime(activity.timestamp) }}
          </div>
          <div class="f10 text-body-light mt-1">{{ activity.description }}</div>
          <ActivityExpandedContent v-if="expanded === activity.id"
            :activity="activity" class="mt-2" />
        </div>
      </div>
    </template>
  </div>
</template>
```

---

## 2.9 TAB ARQUIVOS

**Screenshots React (Replit):**
- `Screen_Shot_2.40.26_PM` — Tab vazia: header "Arquivos e Documentos 0", botao "+ Adicionar Arquivo", filtro "Todos (0)", zona drag-drop, empty state
- `Screen_Shot_2.40.46_PM` — Lista com 4 arquivos: CV (PDF), foto (JPG), video triagem (MP4), video entrevista (MP4)
- `Screen_Shot_2.40.56_PM` — Mais arquivos: entrevista completa (MP4), audio triagem (MP3) com badges de status
- `Screen_Shot_2.41.15_PM` — FilePreviewModal para PDF com paginacao "1/5"
- `Screen_Shot_2.41.36_PM` — FilePreviewModal para video com transcricao + Analise LIA
- `Screen_Shot_2.41.48_PM` — FilePreviewModal para video: Parecer LIA com score 91%

### Bugs Identificados

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D25 | **"Failed to fetch"** | Tab Arquivos nao carrega, erro em producao | Lista de arquivos funcional | **CRITICO** |
| D26 | **Sem drag-and-drop** | Apenas botao de upload basico | Zona dashed com borda tracejada: "Arraste arquivos ou clique para selecionar" + "PDF, DOC, DOCX, JPG, PNG, MP4 • Max 10MB" + empty state com icone documento | ALTO |
| D27 | **Sem preview de midia** | Download abre em nova aba | `FilePreviewModal` com 3 modos: PDF (paginado), imagem, video (com player + transcricao + analise IA) | **CRITICO** |
| D28 | **Sem categorias coloridas** | Lista plana de arquivos sem categorias | 7 categorias com badges coloridos: Curriculo (vermelho), Foto (verde), Triagem (laranja), Entrevista (azul) + filtro chip "Todos (N)" | ALTO |
| D29 | **Sem status de processamento** | Nenhum indicador de status | Badges de status por arquivo: "Analisado", "Destaque", "Completa", "Transcrito" — indicam processamento IA | ALTO |
| D30 | **Sem metadados ricos** | Apenas nome e tipo do arquivo | Cada card exibe: nome, tamanho (2.1 MB), formato (PDF), tempo relativo (Enviado ha 2 dias), duracao para midia (3:45, 8:20, 30:15), descricao ("Curriculo atualizado • Categorizado pela LIA"), categoria source | MEDIO |
| D30b | **Sem botoes de acao por arquivo** | Apenas download | 3 botoes: olho (preview), download, chevron (expandir/menu). Videos tem botao play adicional | MEDIO |
| D30c | **Sem descricao/contexto** | Nenhuma descricao | Texto contextual: "Curriculo atualizado • Categorizado pela LIA", "Video de apresentacao pessoal • Prescreening", "Apresentacao de case tecnico • Entrevista gravada", "Resposta de triagem por voz • OpenMic.ai" | MEDIO |
| D30d | **Sem delete** | Nao implementado | Botao com confirmacao | MEDIO |

### Anatomia de um Card de Arquivo (React — dos screenshots)

```
┌─────────────────────────────────────────────────────────────┐
│ [icone categoria]  CV_MariaOliveira_2024.pdf    [👁] [⬇] [v]│
│                    2.1 MB • PDF  Enviado há 2 dias          │
│                    ◉ Currículo (badge vermelho)              │
│                    Currículo atualizado • Categorizado pela  │
│                    LIA                                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ [icone video]  Apresentacao_Pessoal.mp4  [Analisado] [▶][v] │
│                25.4 MB • MP4 • 3:45                         │
│                ◉ Triagem (badge laranja)                    │
│                Vídeo de apresentação pessoal • Prescreening  │
└─────────────────────────────────────────────────────────────┘
```

### Categorias de Arquivo (React — dos screenshots)

| Categoria | Cor Badge | Icone | Tipos de arquivo |
|-----------|----------|-------|-----------------|
| Curriculo | Vermelho `#ef4444` | Documento | PDF, DOC, DOCX (CVs) |
| Foto | Verde `#22c55e` | Imagem | JPG, PNG (fotos perfil) |
| Triagem | Laranja `#f97316` | Video/Audio | MP4, MP3 (prescreening, OpenMic.ai) |
| Entrevista | Azul `#3b82f6` | Video | MP4 (entrevistas gravadas) |

### Status de Processamento (React — dos screenshots)

| Status | Significado | Aparece em |
|--------|------------|-----------|
| Analisado | IA processou o conteudo | Videos de triagem |
| Destaque | Conteudo marcado como relevante | Videos de entrevista |
| Completa | Gravacao completa | Entrevistas longas |
| Transcrito | Transcricao IA disponivel | Audios de triagem |

### FilePreviewModal — 3 Modos (React — dos screenshots)

**Modo PDF:**
```
┌──────────────────────────────────────────────────┐
│ [📄] CV_MariaOliveira_2024.pdf   < 1/5 > [⬇ Baixar] [X] │
│                                                    │
│  ┌──────────────────────────────────────────────┐  │
│  │                                              │  │
│  │         Visualizando página 1 de 5           │  │
│  │     [Conteúdo do PDF seria renderizado aqui] │  │
│  │                                              │  │
│  └──────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
```
- Header: icone PDF + nome + navegacao paginas `< 1/5 >` + "Baixar" + fechar
- Renderizacao inline do conteudo PDF

**Modo Video (Triagem/Entrevista):**
```
┌─────────────────────────────────────────────────────────────┐
│ [🎬] Apresentacao_Pessoal.mp4           [▶] [⬇ Baixar] [X] │
│                                                               │
│ ┌──────────────────────────┐  ┌───────────────────────────┐  │
│ │                          │  │ 📋 Transcrição            │  │
│ │   [▶ Clique para        │  │ [Vídeo de Triagem] 3:45   │  │
│ │    reproduzir]           │  │                           │  │
│ │  Apresentacao_Pessoal.mp4│  │ Transcrição não           │  │
│ │                          │  │ disponível para           │  │
│ └──────────────────────────┘  │ este vídeo                │  │
│                               └───────────────────────────┘  │
│                                                               │
│ 📋 Perguntas de Triagem                                      │
│  1. Por favor, apresente-se e conte sobre sua experiência    │
│  2. Por que você está interessado nesta vaga e empresa?      │
│  3. Quais são suas principais conquistas profissionais?      │
│  4. Qual sua disponibilidade para início e expectativa       │
│     salarial?                                                │
│                                                               │
│ ⊕ Análise da LIA                                            │
│  Confiança    Comunicação    Clareza    Entusiasmo           │
│    92%           95%          88%          90%                │
│                                                               │
│ ⊕ Parecer da LIA                                            │
│  Pontos Fortes: O candidato demonstra excelente capacidade   │
│   de comunicação, com respostas claras e estruturadas...     │
│  Pontos de Atenção: Poderia ter elaborado mais sobre         │
│   metodologias específicas de design...                      │
│  Recomendação: Candidato altamente recomendado para          │
│   próxima fase...                                            │
│                                                               │
│  Score Geral  [91% - Altamente Recomendado] (badge verde)    │
└─────────────────────────────────────────────────────────────┘
```

**Layout modal video:**
- **Header:** icone video (vermelho) + nome arquivo + botao play + "Baixar" + fechar
- **Corpo esquerdo (60%):** Player de video com overlay "Clique para reproduzir"
- **Corpo direito (40%):** Painel "Transcricao" com chip tipo ("Video de Triagem"), duracao, texto transcricao
- **Abaixo do player:** "Perguntas de Triagem" — lista numerada das perguntas usadas
- **Analise da LIA:** 4 metricas em grid horizontal: Confianca, Comunicacao, Clareza, Entusiasmo (% cada)
- **Parecer da LIA:** Secoes textuais: Pontos Fortes, Pontos de Atencao, Recomendacao
- **Score Geral:** Badge verde com "91% - Altamente Recomendado"

### Codigo Vue ATUAL — files/wrapper.vue (120 linhas)

```vue
<ul class="d-flex flex-column ga-2 pa-3">
  <li v-for="file in files" :key="file.id"
    class="px-3 py-4 border border-border-color rounded-lg d-flex align-start ga-2">
    <Icon :name="icons[file.file_type]" size="14" color="body-light" />
    <div>
      <p class="f11">{{ file.name }}</p>
      <p class="f10 text-body-light">{{ file.file_type }}</p>
    </div>
    <Icon name="lucide-download" size="14" @click="downloadFile(file)" clickable />
  </li>
</ul>
```

### CORRECAO — Tab Arquivos Completa (D25-D30d)

```vue
<!-- REWRITE: features/candidates/files/wrapper.vue -->
<template>
  <div class="pa-3">
    <!-- Header -->
    <div class="d-flex align-center justify-space-between mb-3">
      <div class="d-flex align-center ga-2">
        <Icon name="lucide-file-text" size="14" />
        <p class="f12 font-weight-medium">Arquivos e Documentos</p>
        <v-chip size="x-small" variant="tonal">{{ files.length }}</v-chip>
      </div>
      <v-btn size="small" variant="tonal" color="primary" @click="triggerUpload">
        <Icon name="lucide-plus" size="12" class="mr-1" />Adicionar Arquivo
      </v-btn>
    </div>

    <!-- Filtro por categoria -->
    <div class="d-flex ga-1 flex-wrap mb-3">
      <v-chip v-for="cat in categories" :key="cat.value"
        :variant="selectedCategory === cat.value ? 'flat' : 'outlined'"
        :color="cat.color" size="x-small"
        @click="selectedCategory = selectedCategory === cat.value ? 'all' : cat.value"
        class="cursor-pointer f9">
        {{ cat.icon }} {{ cat.label }} ({{ cat.count }})
      </v-chip>
    </div>

    <!-- Zona drag-and-drop -->
    <div class="rounded-lg pa-4 text-center mb-3 cursor-pointer"
      :class="isDragging ? 'border-primary bg-primary-lighten-5' : ''"
      :style="{
        border: isDragging ? '2px dashed rgb(var(--v-theme-primary))' : '2px dashed rgba(0,0,0,0.12)',
      }"
      @dragover.prevent="isDragging = true" @dragleave="isDragging = false"
      @drop.prevent="handleDrop" @click="triggerUpload">
      <Icon name="lucide-upload" size="24" color="body-light" class="mb-2" />
      <p class="f11 text-on-surface">Arraste arquivos ou clique para selecionar</p>
      <p class="f9 text-body-light mt-1">PDF, DOC, DOCX, JPG, PNG, MP4 • Max 10MB</p>
    </div>

    <!-- Empty state -->
    <div v-if="filteredFiles.length === 0 && !isLoading" class="text-center py-6">
      <Icon name="lucide-file-text" size="36" color="body-light" class="mb-2" />
      <p class="f11 text-body-light">Nenhum arquivo enviado</p>
      <p class="f9 text-body-light">Arraste arquivos ou clique acima para enviar</p>
    </div>

    <!-- Lista de arquivos -->
    <div v-for="file in filteredFiles" :key="file.id"
      class="d-flex align-start ga-3 pa-3 border border-border-color rounded-lg mb-2
             hover:bg-grey-lighten-5 transition-colors">
      <!-- Icone da categoria -->
      <div class="rounded-lg d-flex align-center justify-center flex-shrink-0"
        :style="{ width: '36px', height: '36px', backgroundColor: getCategoryBg(file.category) }">
        <Icon :name="getCategoryIcon(file)" size="18" :color="getCategoryColor(file.category)" />
      </div>

      <!-- Info principal -->
      <div class="flex-grow-1" style="min-width: 0;">
        <div class="d-flex align-center ga-2 mb-0">
          <p class="f11 font-weight-medium text-on-surface text-truncate">{{ file.name }}</p>
        </div>
        <div class="d-flex align-center ga-1 f9 text-body-light flex-wrap">
          <span>{{ formatFileSize(file.size) }}</span>
          <span>•</span>
          <span>{{ file.file_type?.toUpperCase() }}</span>
          <template v-if="file.duration">
            <span>•</span>
            <span>{{ formatDuration(file.duration) }}</span>
          </template>
          <span>Enviado {{ formatRelativeTime(file.created_at) }}</span>
        </div>
        <div class="d-flex align-center ga-1 mt-1">
          <v-chip size="x-small" :color="getCategoryColor(file.category)" variant="tonal" class="f8">
            ◉ {{ file.category }}
          </v-chip>
          <v-chip v-if="file.status" size="x-small" variant="outlined" class="f8">
            {{ file.status }}
          </v-chip>
        </div>
        <p v-if="file.description" class="f9 text-body-light mt-1">{{ file.description }}</p>
      </div>

      <!-- Acoes -->
      <div class="d-flex align-center ga-1 flex-shrink-0">
        <v-btn v-if="isMedia(file)" icon variant="text" size="x-small"
          @click="previewFile(file)">
          <Icon name="lucide-play" size="14" />
        </v-btn>
        <v-btn icon variant="text" size="x-small" @click="previewFile(file)">
          <Icon name="lucide-eye" size="14" />
        </v-btn>
        <v-btn icon variant="text" size="x-small" @click="downloadFile(file)">
          <Icon name="lucide-download" size="14" />
        </v-btn>
        <v-btn icon variant="text" size="x-small" @click="showFileMenu(file)">
          <Icon name="lucide-chevron-down" size="14" />
        </v-btn>
      </div>
    </div>

    <!-- File Preview Modal -->
    <FilePreviewModal v-if="previewingFile" :file="previewingFile"
      @close="previewingFile = null" @download="downloadFile" />

    <input ref="fileInput" type="file" class="d-none" multiple
      accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.mp4,.mp3"
      @change="handleFileSelect" />
  </div>
</template>
```

### CORRECAO — FilePreviewModal para Video com Analise IA (D27)

```vue
<!-- NOVO: features/candidates/files/FilePreviewModal.vue -->
<template>
  <v-dialog v-model="isOpen" max-width="900" persistent>
    <v-card class="rounded-lg">
      <!-- Header -->
      <v-card-title class="d-flex align-center justify-space-between pa-3 border-b">
        <div class="d-flex align-center ga-2">
          <Icon :name="getTypeIcon(file)" size="16" :color="getTypeColor(file)" />
          <span class="f12 font-weight-medium">{{ file.name }}</span>
        </div>
        <div class="d-flex align-center ga-1">
          <template v-if="isPDF">
            <v-btn icon variant="text" size="x-small" @click="prevPage" :disabled="currentPage <= 1">
              <Icon name="lucide-chevron-left" size="14" />
            </v-btn>
            <span class="f10">{{ currentPage }} / {{ totalPages }}</span>
            <v-btn icon variant="text" size="x-small" @click="nextPage" :disabled="currentPage >= totalPages">
              <Icon name="lucide-chevron-right" size="14" />
            </v-btn>
          </template>
          <v-btn v-if="isVideo" icon variant="text" size="x-small" @click="playVideo">
            <Icon name="lucide-play" size="14" />
          </v-btn>
          <v-btn size="small" variant="tonal" @click="$emit('download', file)">
            <Icon name="lucide-download" size="12" class="mr-1" />Baixar
          </v-btn>
          <v-btn icon variant="text" size="small" @click="$emit('close')">
            <Icon name="lucide-x" size="16" />
          </v-btn>
        </div>
      </v-card-title>

      <v-card-text class="pa-0">
        <!-- Modo PDF -->
        <div v-if="isPDF" class="pa-6 d-flex justify-center" style="min-height: 500px; background: #f5f5f5;">
          <div class="text-center">
            <p class="f11 text-body-light">Visualizando pagina {{ currentPage }} de {{ totalPages }}</p>
          </div>
        </div>

        <!-- Modo Video/Audio -->
        <template v-if="isMedia">
          <div class="d-flex" style="min-height: 300px;">
            <!-- Player (60%) -->
            <div class="flex-grow-1 pa-4" style="flex-basis: 60%;">
              <div class="rounded-lg d-flex align-center justify-center"
                style="background: #1a1a2e; aspect-ratio: 16/9; cursor: pointer;"
                @click="playVideo">
                <div class="text-center">
                  <Icon name="lucide-play-circle" size="48" color="white" class="mb-2" />
                  <p class="f11 text-white">Clique para reproduzir</p>
                  <p class="f9 text-grey-lighten-1">{{ file.name }}</p>
                </div>
              </div>
            </div>
            <!-- Transcricao (40%) -->
            <div class="pa-4 border-s" style="flex-basis: 40%;">
              <div class="d-flex align-center ga-2 mb-3">
                <span class="f11">📋 Transcricao</span>
              </div>
              <div class="d-flex align-center ga-2 mb-3">
                <v-chip size="small" color="grey-darken-3" variant="flat" class="text-white f9">
                  {{ file.category === 'Triagem' ? 'Video de Triagem' : 'Entrevista' }}
                </v-chip>
                <span class="f10 text-body-light">Duracao: {{ formatDuration(file.duration) }}</span>
              </div>
              <p v-if="file.transcription" class="f10" style="white-space: pre-wrap;">
                {{ file.transcription }}
              </p>
              <p v-else class="f10 text-body-light">
                Transcricao nao disponivel para este video
              </p>
            </div>
          </div>

          <!-- Perguntas de Triagem -->
          <div v-if="file.screening_questions?.length" class="pa-4 border-t">
            <p class="f11 font-weight-medium mb-2">📋 Perguntas de Triagem</p>
            <ol class="pl-4">
              <li v-for="(q, i) in file.screening_questions" :key="i" class="f10 mb-1">{{ q }}</li>
            </ol>
          </div>

          <!-- Analise da LIA -->
          <div v-if="file.lia_analysis" class="pa-4 border-t">
            <p class="f11 font-weight-medium mb-3">
              <Icon name="lucide-brain" size="12" class="mr-1" /> Analise da LIA
            </p>
            <div class="d-flex justify-space-around mb-4">
              <div v-for="metric in file.lia_analysis.metrics" :key="metric.label" class="text-center">
                <p class="f9 text-body-light mb-1">{{ metric.label }}</p>
                <p class="f14 font-weight-bold" :style="{ color: getMetricColor(metric.value) }">
                  {{ metric.value }}%
                </p>
              </div>
            </div>
          </div>

          <!-- Parecer da LIA -->
          <div v-if="file.lia_opinion" class="pa-4 border-t">
            <p class="f11 font-weight-medium mb-2">
              <Icon name="lucide-brain" size="12" class="mr-1" /> Parecer da LIA
            </p>
            <div class="mb-2">
              <p class="f10"><b>Pontos Fortes:</b> {{ file.lia_opinion.strengths }}</p>
            </div>
            <div class="mb-2">
              <p class="f10"><b>Pontos de Atencao:</b> {{ file.lia_opinion.concerns }}</p>
            </div>
            <div class="mb-3">
              <p class="f10"><b>Recomendacao:</b> {{ file.lia_opinion.recommendation }}</p>
            </div>
            <div class="d-flex align-center ga-2">
              <span class="f10">Score Geral</span>
              <v-chip :color="file.lia_opinion.score >= 80 ? 'success' : 'warning'" variant="flat"
                size="small" class="font-weight-bold">
                {{ file.lia_opinion.score }}% - {{ file.lia_opinion.label }}
              </v-chip>
            </div>
          </div>
        </template>

        <!-- Modo Imagem -->
        <div v-if="isImage" class="pa-4 d-flex justify-center">
          <img :src="file.url" :alt="file.name" style="max-width: 100%; max-height: 600px;" />
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>
```

---

## 2.10 TAB PARECERES E ANALISES

**Screenshot React:** `Screen_Shot_2.47.01_PM`

| ID | Elemento | Vue (Producao) | React (Replit — do screenshot) | Sev. |
|----|---------|---------------|-------------------------------|------|
| D31 | **Sub-tabs** | Lista unica de pareceres | 2 sub-tabs: "⊕ Pareceres da LIA" (brain icon) + "📄 Analises" | ALTO |
| D31b | **Empty state** | Nao documentado | Icone documento grande + "Nenhum parecer disponivel" + "Os pareceres serao gerados automaticamente apos triagens ou analises da LIA." — texto informativo e claro | MEDIO |
| D32 | **Sem score breakdown** | Score como numero simples | Grid 2 colunas com label + valor + barra progresso por metrica | ALTO |
| D33 | **Sem secoes qualitativas** | Nao exibe Pontos Fortes, Gaps, Skills Match separadamente | Secoes expansiveis com listas bulleted | ALTO |
| D34 | **Sem copiar parecer** | Nao ha botao copiar | Botao copiar com formatacao limpa | MEDIO |
| D35 | **Sem historico de versoes** | Apenas parecer atual visivel | Historico completo com timestamps e scores | ALTO |

### Anatomia da Tab Pareceres (React — do screenshot)

```
┌─────────────────────────────────────────────────────────────┐
│  [⊕ Pareceres da LIA]  [📄 Análises]                       │
│  ──────────────────────                                     │
│                                                             │
│   ┌───────────────────────────────────────────────────────┐ │
│   │                                                       │ │
│   │            📄  (ícone documento grande)                │ │
│   │                                                       │ │
│   │        Nenhum parecer disponível                      │ │
│   │   Os pareceres serão gerados automaticamente          │ │
│   │   após triagens ou análises da LIA.                   │ │
│   │                                                       │ │
│   └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### CORRECAO — Tab Pareceres Vue (D31-D35)

```vue
<!-- NOVO: features/candidates/opinions/CandidateOpinionsTab.vue -->
<template>
  <div class="pa-3">
    <v-tabs v-model="subTab" density="compact" class="mb-3">
      <v-tab value="pareceres" class="f10">
        <Icon name="lucide-brain" size="12" class="mr-1" color="wedo-cyan" />
        Pareceres da LIA
        <v-chip v-if="opinions.length" size="x-small" color="primary" variant="tonal" class="ml-1">
          {{ opinions.length }}
        </v-chip>
      </v-tab>
      <v-tab value="analises" class="f10">
        <Icon name="lucide-file-text" size="12" class="mr-1" />Analises
      </v-tab>
    </v-tabs>
    <v-window v-model="subTab">
      <v-window-item value="pareceres">
        <div v-if="loading" class="d-flex flex-column ga-3">
          <v-skeleton-loader v-for="i in 2" :key="i" type="card" />
        </div>
        <div v-else-if="opinions.length === 0" class="text-center py-6">
          <Icon name="lucide-brain" size="32" color="body-light" class="mb-2" />
          <p class="f12 text-body-light">Nenhum parecer gerado ainda</p>
        </div>
        <OpinionCard v-for="opinion in opinions" :key="opinion.id"
          :opinion="opinion" :expanded="expandedId === opinion.id"
          @toggle="expandedId = expandedId === opinion.id ? null : opinion.id"
          @copy="copyOpinion" />
      </v-window-item>
      <v-window-item value="analises">
        <AnalysisCard v-for="analysis in analyses" :key="analysis.id"
          :analysis="analysis" @delete="deleteAnalysis" @copy="copyAnalysis" />
      </v-window-item>
    </v-window>
  </div>
</template>
```

---

## 2.11 DESIGN SYSTEM — TIPOGRAFIA, CORES, ESPACAMENTO

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D36 | **Font family** | Roboto (Vuetify default) | Open Sans 85% + Inter 10% + JetBrains Mono 5% | MEDIO |
| D37 | **Tamanho base** | ~14px padrao Vuetify | `text-xs` (12px) base, `text-micro` (10px) badges | MEDIO |
| D38 | **Hierarquia tipografica** | Pesos similares entre titulo/label/corpo | `textStyles.label` 12px medium, `textStyles.caption` 10px | MEDIO |
| D39 | **Cores de badge** | Inconsistentes, sem padrao semantico | Design tokens: success/warning/error/info | MEDIO |
| D40 | **Sombras** | Box-shadow Material Design (elevation) | Borders sem sombras: `border-lia-border-subtle` | BAIXO |
| D41 | **Dark mode** | Nao suportado | Tokens adaptaveis preparados | BAIXO |
| D42 | **Padding excessivo** | Cards com espaco interno visivelmente maior | `p-2.5` (10px), `gap-1.5` (6px), `rounded-md` (6px) | MEDIO |
| D43 | **Border radius** | ~4px padrao Vuetify | `rounded-md` (6px) padrao | BAIXO |

### Mapeamento de Design Tokens

| Token React | Uso | Equivalente Vue |
|---|---|---|
| `--lia-bg-primary` | Fundo principal | `rgb(var(--v-theme-surface))` |
| `--lia-bg-secondary` | Fundo secundario | `rgb(var(--v-theme-background))` |
| `--lia-text-primary` | Texto principal | `text-on-surface` |
| `--lia-text-tertiary` | Texto terciario | `text-body-light` |
| `--lia-border-subtle` | Borda sutil | `border-border-color border-opacity-100` |
| `--wedo-cyan` | Cor LIA | `wedo-cyan` (custom) |

### Mapeamento de Tipografia

| Classe React | Tamanho | Classe Vue |
|---|---|---|
| `text-micro` | 9px | `f9` |
| `text-xs` | 10px | `f10` |
| `textStyles.body` | 11px | `f11` |
| `textStyles.label` | 12px | `f12` |
| `text-sm` | 14px | `f13` / `f14` |

### Espacamento — Vue ~20% maior que React

| React | Valor | Vue | Delta |
|---|---|---|---|
| `p-2.5` | 10px | `pa-3` (12px) | +2px |
| `gap-1.5` | 6px | `ga-2` (8px) | +2px |
| `rounded-md` | 6px | `rounded-lg` (8px) | +2px |

---

## 2.12 NOMENCLATURA E TERMINOLOGIA

| ID | Elemento | Vue (Producao) | React (Replit) | Sev. |
|----|---------|---------------|----------------|------|
| D44 | **Tab 4 (preview)** | Nao visivel (truncado) | "Pareceres e Analises" | ALTO |
| D45 | **Tab 4 (full page)** | "Pareceres" (sem "e Analises") | "Pareceres e Analises" | ALTO |
| D46 | **Tab extra full page** | "Curriculo" (nao existe na referencia) | Nao existe | MEDIO |
| D47 | **Score label** | `87` (badge numerico) | `Score: 85/100` com label e escala | ALTO |
| D48 | **Recommendation** | "Alta Confianca" (badge) | `highly_recommended` mapeado para label PT-BR | MEDIO |
| D49 | **Activity changes** | JSON raw no "Resumo das Alteracoes" | Formatado por tipo no `ActivityExpandedDetails` | **CRITICO** |
| D50 | **Botoes header** | Icones-only sem labels | Icone + texto descritivo | ALTO |

---

# PARTE 3: FEATURE GAPS

Funcionalidades que existem no React e NAO existem no Vue. Cada item e um potencial card de Jira.

| ID | Feature | Componente React | Linhas | Descricao | Sev. |
|----|---------|-----------------|--------|-----------|------|
| G01 | **Tab Pareceres** | `CandidateOpinionsTab.tsx` | 293 | Historico de pareceres + analises salvas com subtabs | **CRITICO** |
| G02 | **LIA Chat Modal** | `LiaChatModal.tsx` | 315 | Chat conversacional com IA sobre o candidato | **CRITICO** |
| G03 | **LIA Analysis Modal** | `lia-analysis-modal.tsx` | dynamic | Gerar nova analise IA sob demanda (bullet_points, short, detailed) | ALTO |
| G04 | **Screening Media Modal** | `screening-media-modal.tsx` | dynamic | Player video/audio com transcricao IA segmentada | ALTO |
| G05 | **DISC Assessment Modal** | `disc-assessment-modal.tsx` | dynamic | Resultado DISC com grafico visual | ALTO |
| G06 | **Big Five Modal** | `big-five-modal.tsx` | dynamic | Resultado Big Five com radar chart | ALTO |
| G07 | **File Preview Modal** | `FilePreviewModal.tsx` | 546 | 3 modos: PDF (paginado com < 1/5 >), imagem, video/audio. Modo video inclui: player com overlay, painel Transcricao lateral (chip tipo + duracao + texto), Perguntas de Triagem (lista numerada), Analise da LIA (4 metricas: Confianca/Comunicacao/Clareza/Entusiasmo em %), Parecer da LIA (Pontos Fortes, Pontos de Atencao, Recomendacao), Score Geral com badge colorido ("91% - Altamente Recomendado") | **CRITICO** |
| G08 | **Drag & Drop Upload** | `CandidateFilesTab.tsx` | embutido | Zona dashed "Arraste arquivos ou clique para selecionar" + "PDF, DOC, DOCX, JPG, PNG, MP4 • Max 10MB" + empty state com icone | ALTO |
| G09 | **Categorias + Status** | `useCandidateFiles.tsx` | embutido | Categorias coloridas (Curriculo vermelho, Foto verde, Triagem laranja, Entrevista azul) + badges de status (Analisado, Destaque, Completa, Transcrito) + descricao contextual por arquivo | ALTO |
| G10 | **Activity Timeline** | `ActivityTimeline.tsx` | 98 | Timeline visual com dots coloridos e click-to-expand | ALTO |
| G11 | **Activity Filters** | `ActivityFilters.tsx` | 131 | Filtros por tipo + periodo + modo visualizacao | ALTO |
| G12 | **Activity Details** | `ActivityExpandedDetails.tsx` | 878 | Detalhes expandidos por tipo (15+ tipos) | ALTO |
| G13 | **Navegacao candidatos** | `candidate-preview.tsx` | embutido | Setas prev/next com indice `1 de 42` | MEDIO |
| G14 | **ExperienceHighlight** | `experience-highlight-card.tsx` | embutido | Card destaque de experiencia no topo do perfil | MEDIO |
| G15 | **Alertas de confirmacao** | Varios `AlertDialog` | embutido | "Gerar novo parecer substituira o atual", "Excluir analise?" | MEDIO |
| G16 | **Toast notifications** | Sonner | embutido | Feedback: sucesso de copia, erro de rede, confirmacao | BAIXO |

## Features EXCLUSIVAS do Vue (preservar no React)

| ID | Feature | Componente Vue | Descricao |
|----|---------|---------------|-----------|
| V01 | **Enriquecimento** | `preview.vue` dialog | Enriquecer perfil com creditos (email, telefone) |
| V02 | **Remuneracao detalhada** | `remunerations.vue` (191L) | Calculo 13.33x + variaveis + beneficios + total anual |
| V03 | **Score Analysis separado** | `score_analysis.vue` (692L) | Score com confianca, requisitos expandiveis, skills matched |
| V04 | **Curriculo como tab** | `curriculum_text.vue` (513L) | Tab dedicada para texto do curriculo |
| V05 | **Sourced Profile** | `sourced-profile-*.vue` (9 arqs) | Preview especifico para candidatos sourcing LIA |
| V06 | **Candidatos similares** | `similar_candidates_modal.vue` | Modal de candidatos similares |
| V07 | **Busca IA** | `preview.vue` dialog | Gerar perfil IA para candidatos sem origem IA |

---

# PARTE 4: BUGS BACKEND + API

## Criticos

| ID | Problema | Onde | Impacto |
|----|---------|------|---------|
| B01 | **`company_id` hardcoded como `demo_company`** em todas as chamadas API do frontend React. Na producao Vue, vem da sessao mas pode haver mismatch | `useCandidatePreviewCore.tsx` linhas 77, 92, 105, 145 | Multi-tenancy comprometida |
| B02 | **Analise IA sem `company_id`** — `AnalysisRequest` nao tem campo company_id | `app/schemas/analysis.py`, `analysis_service.py` | Vazamento de dados entre empresas |

## Altos

| ID | Problema | Onde | Impacto |
|----|---------|------|---------|
| B03 | **N+1 query no opinions history** — para cada opinion, query separada para `job_vacancy.title` | `app/api/v1/opinions.py:110-117` | Performance degradada |
| B04 | **Count query ineficiente** — carrega todos records para contar em vez de `SELECT COUNT(*)` | `app/api/v1/opinions.py` | Carga desnecessaria |
| B05 | **Files usa `BACKEND_URL` direto** — bypassing proxy que adiciona auth headers | `useCandidateFiles.tsx:44,51,102,145,169` | CORS errors, sem auth |
| B06 | **Tab Arquivos "Failed to fetch"** — confirmado via Playwright em producao | `/api/v1/candidates/{id}/files` | Funcionalidade inacessivel |

## Medios/Baixos

| ID | Problema | Onde | Impacto | Sev. |
|----|---------|------|---------|------|
| B07 | **`recruiter_override` sem validacao de permissao** | `app/api/v1/opinions.py` | Usuarios sem permissao alteram pareceres | MEDIO |
| B08 | **Tipo inconsistente `candidate_id`** — UUID em `lia_opinions`, String(255) em `lia_profile_analyses` | Models SQLAlchemy | JOINs complicados | MEDIO |
| B09 | **Sem FK** entre `lia_profile_analyses`/`candidate_attachments` e `candidates` | Models SQLAlchemy | Dados orfaos | MEDIO |
| B10 | **8 endpoints nao consumidos** — paginacao opinions, PATCH, cultural-fit, bias audit, etc. | `app/api/v1/` | Funcionalidade sem UI | BAIXO |

## Endpoints Vue (codigo real)

| Endpoint | Componente | Uso |
|---|---|---|
| `GET /users/data_files` | files/wrapper.vue | Buscar arquivos |
| `GET /users/experiences` | cards/experiences.vue | Buscar experiencias |
| `GET /users/educations` | cards/educations.vue | Buscar formacoes |
| `GET /users/skill_relationships` | cards/skills.vue | Buscar skills |
| `GET /users/addresses/Candidate/{id}` | cards/addresses.vue | Buscar enderecos |
| `GET /users/candidates/{id}/calculate_remunerations` | cards/remunerations.vue | Calcular remuneracao |
| `GET /users/candidates/{id}/calculate_benefits` | cards/remunerations.vue | Calcular beneficios |

## Endpoints React (codigo real)

| Endpoint | Componente | Uso |
|---|---|---|
| `GET /api/backend-proxy/opinions/candidate/{id}/summary` | useCandidatePreviewCore | Resumo pareceres |
| `POST /api/backend-proxy/opinions/generate` | useCandidatePreviewCore | Gerar parecer |
| `GET /api/backend-proxy/opinions/candidate/{id}/history` | useCandidatePreviewCore | Historico |
| `GET /api/backend-proxy/analyses/candidate/{id}` | useCandidatePreviewCore | Analises salvas |
| `DELETE /api/backend-proxy/analyses/{aid}` | useCandidatePreviewCore | Deletar analise |
| `POST /api/backend-proxy/lia/chat` | useCandidatePreviewCore | Chat com LIA |
| `GET {BACKEND_URL}/api/v1/candidates/{id}/files` | useCandidateFiles | Buscar arquivos |

## Endpoints Ausentes no Vue

| Endpoint | Sev. | Descricao |
|---|---|---|
| `GET /opinions/history` | **CRITICO** | Historico de pareceres LIA |
| `POST /opinions/generate` | **CRITICO** | Gerar novo parecer |
| `POST /lia/chat` | **CRITICO** | Chat conversacional com LIA |
| `GET /activities` | ALTO | Timeline de atividades |
| `DELETE /files/{id}` | MEDIO | Deletar arquivo |
| `GET /analyses` | ALTO | Analises salvas por vaga |

---

# PARTE 5: BUGS IA + BANCO DE DADOS

## Inteligencia Artificial

| ID | Problema | Onde | Impacto | Sev. |
|----|---------|------|---------|------|
| IA01 | **Sem multi-tenancy na analise** — `AnalysisRequest` sem `company_id` | `app/schemas/analysis.py` | Sem isolamento por empresa | **CRITICO** |
| IA02 | **FairnessGuard NAO integrado** na geracao de parecer | `personalized_feedback_service.py` vs `analysis_service.py` | Parecer pode conter bias | ALTO |
| IA03 | **Prompt Injection Guard nao aplicado** — inputs nao sanitizados | `app/shared/prompt_injection.py` nao chamado em `analysis_service.py` | Candidato pode manipular analise | ALTO |
| IA04 | **Score sem nivel de confianca** — frontend nao mostra se EXPLICIT ou INFERRED | `rubric_evaluation_service.py:331-392` | Score sem transparencia | ALTO |
| IA05 | **Pesos fixos 35/25/20/20** sem customizacao por empresa | `app/schemas/analysis.py:38-43` | Mesma ponderacao para todos | MEDIO |
| IA06 | **Archetypes hardcoded** — 8 tipos fixos | `app/api/v1/analysis.py:56-112` | Nao customizavel | BAIXO |

### Arquitetura IA

```
Frontend (React/Vue)
    |
    v
POST /api/v1/analysis/candidates
    |
    v
analysis_service.analyze_candidates()
    |
    v
Claude AI (Anthropic)
    |-- Big Five -> Archetype (8 tipos)
    |-- Score Breakdown -> match_tecnico (35%), fit_personalidade (25%),
    |                      relevancia_experiencia (20%), alinhamento_cultural (20%)
    |-- Recommendation -> highly_recommended / recommended / potential / low_match / not_recommended
    v
CandidateAnalysisResult -> Frontend
```

## Banco de Dados

| ID | Problema | Tabelas | Impacto | Sev. |
|----|---------|---------|---------|------|
| DB01 | **Tipo inconsistente `candidate_id`** — UUID nativo em `lia_opinions`, String(255) em `lia_profile_analyses` e `candidate_attachments` | 3 tabelas | JOINs com conversao de tipo | MEDIO |
| DB02 | **`CandidateAttachment.id` e String** (gerado via `str(uuid4())`) | `candidate_attachments` | Performance em indexacao | MEDIO |
| DB03 | **Sem FK `lia_profile_analyses.candidate_id`** → `candidates.id` | `lia_profile_analyses` | Sem CASCADE delete | MEDIO |
| DB04 | **Sem FK `candidate_attachments.candidate_id`** → `candidates.id` | `candidate_attachments` | Anexos orfaos | MEDIO |
| DB05 | **`languages` default={}** mas producao retorna `null` | `candidates` | Frontend tratar null e {} | BAIXO |
| DB06 | **`past_locations` default=[]** mutable | `candidates` | Shared state entre instancias | BAIXO |

---

# PARTE 6: TABELA DE PRIORIDADES UNIFICADA

## Sprint 1 — Criticos (bloqueia uso) — 1-2 semanas

| # | Correcao | IDs | Arquivo Vue | Esforco | Impacto |
|---|---------|-----|-------------|---------|---------|
| FIX-01 | **Corrigir layout preview** — drawer nao deve empurrar header/botoes da tabela | D01, D02, D03 | `preview.vue` | 1-2 dias | **CRITICO** |
| FIX-02 | **Corrigir cards atividade** — expandir ao clicar, formatar JSON, altura maxima | D17, D18, D19, D49 | `applies.vue` → novo componente | 2-3 dias | **CRITICO** |
| FIX-03 | **Implementar Tab Pareceres** — historico + subtabs + OpinionCard | D13, G01, D31-D35 | **NOVO:** `opinions/CandidateOpinionsTab.vue` | 3 dias | **CRITICO** |
| FIX-04 | **Corrigir Tab Arquivos** — resolver "Failed to fetch", implementar proxy | D25, B05, B06 | `files/wrapper.vue` + proxy config | 1-2 dias | **CRITICO** |
| FIX-05 | **Implementar acao Parecer LIA** — botao "Gerar Parecer" + conectar API | D15 | `lia_assessment.vue` | 1 dia | **CRITICO** |
| FIX-06 | **Multi-tenancy na analise IA** — company_id no AnalysisRequest | B02, IA01 | `app/schemas/analysis.py` | 1 dia | **CRITICO** |

## Sprint 2 — Alta Prioridade (funcionalidade core) — 2-3 semanas

| # | Correcao | IDs | Arquivo Vue | Esforco | Impacto |
|---|---------|-----|-------------|---------|---------|
| FIX-07 | **Botoes de acao com labels** — trocar icones-only por icone + texto | D10, D11, D50 | `preview.vue` | 1 dia | ALTO |
| FIX-08 | **Datas no header** — cadastro, atualizacao, ultimo contato | D08 | `preview.vue` | 2h | ALTO |
| FIX-09 | **Botao LIA no header** + conectar modal chat/analise | D09, G02 | `preview.vue` + **NOVO:** `LiaChatModal.vue` | 3 dias | ALTO |
| FIX-10 | **Skills categorizadas** — agrupar por Backend/Frontend/Data + cores por fonte | D10b, D10c | `cards/skills.vue` | 1-2 dias | ALTO |
| FIX-11 | **Filtros atividade completos** — 8 filtros visiveis + "Nova Atividade" + nota | D20, D22 | **NOVO:** `activities/ActivityFilters.vue` | 1-2 dias | ALTO |
| FIX-12 | **Upload drag-and-drop** + cards ricos (categorias coloridas, status IA, metadados, descricao) | D26, D28, D29, D30, D30b, D30c, G08, G09 | `files/wrapper.vue` (rewrite) | 3 dias | ALTO |
| FIX-12b | **FilePreviewModal** — 3 modos: PDF paginado, imagem, video (player + transcricao + Perguntas Triagem + Analise LIA 4 metricas + Parecer LIA + Score) | D27, G07 | **NOVO:** `files/FilePreviewModal.vue` | 3-5 dias | **CRITICO** |
| FIX-13 | **Integrar FairnessGuard** na geracao de parecer | IA02 | `analysis_service.py` | 1 dia | ALTO |
| FIX-14 | **Prompt Injection Guard** nos inputs | IA03 | `analysis_service.py` | 1 dia | ALTO |
| FIX-15 | **Corrigir N+1 query** no opinions history | B03, B04 | `app/api/v1/opinions.py` | 1 dia | ALTO |

## Sprint 3 — Media Prioridade (polish) — 2-3 semanas

| # | Correcao | IDs | Arquivo Vue | Esforco | Impacto |
|---|---------|-----|-------------|---------|---------|
| FIX-16 | Tipografia DS v4.2.1 (Open Sans + Inter + JetBrains Mono) | D36, D37, D38 | `nuxt.config.ts` + CSS | 1 dia | MEDIO |
| FIX-17 | Design tokens semanticos de cores | D39, D42 | Todos os componentes | 2 dias | MEDIO |
| FIX-18 | Secoes ausentes no perfil (ExperienceHighlight, Indicadores, Preferencias) | D12b-D15b, G14 | `overview.vue` | 2-3 dias | MEDIO |
| FIX-19 | Cards experiencia melhorados (border colorida, tech stack, startup badge) | D16b | `cards/experiences.vue` | 1 dia | MEDIO |
| FIX-20 | Timeline com agrupamento por data | D23, D24 | **NOVO:** `activities/ActivityTimeline.vue` | 1-2 dias | MEDIO |
| FIX-21 | Modais DISC, BigFive, Screening | G04, G05, G06 | **NOVOS:** 3 componentes | 3 dias | MEDIO |
| FIX-22 | FKs e tipos inconsistentes no banco | DB01-DB04 | Models SQLAlchemy + migration | 1 dia | MEDIO |
| FIX-23 | Score com nivel de confianca | IA04 | Frontend + `rubric_evaluation_service.py` | 1 dia | MEDIO |
| FIX-24 | Copiar/colar parecer | D34 | `OpinionCard.vue` | 2h | MEDIO |
| FIX-25 | Redes sociais expandidas no header | D07 | `preview.vue` | 2h | MEDIO |

## Sprint 4 — Baixa Prioridade (nice-to-have) — 1-2 semanas

| # | Correcao | IDs | Arquivo Vue | Esforco | Impacto |
|---|---------|-----|-------------|---------|---------|
| FIX-26 | Dark mode | D41 | Vuetify theme config | 2 dias | BAIXO |
| FIX-27 | Toast notifications | G16 | Config global | 2h | BAIXO |
| FIX-28 | Alertas confirmacao para acoes destrutivas | G15 | Varios | 1 dia | BAIXO |
| FIX-29 | Tab overflow com setas | D12 | `preview.vue` | 2h | BAIXO |
| FIX-30 | Defaults mutaveis no schema | DB05, DB06 | Models SQLAlchemy | 1h | BAIXO |
| FIX-31 | Navegacao prev/next entre candidatos | G13 | `preview.vue` | 1 dia | BAIXO |

## Sprint Bugfix React — Bugs visuais encontrados nos screenshots

| # | Correcao | IDs | Arquivo React | Esforco | Impacto |
|---|---------|-----|--------------|---------|---------|
| FIX-R04 | **BUG: "undefined"/"null" renderizados** — sanitizar valores nulos em Preferencias | D16g, D16h | `CandidatePreviewProfileTab.tsx` | 2h | **CRITICO** |
| FIX-R05 | **BUG: Datas ISO raw na Formacao** — formatar "2020-02-01" → "fev. de 2020" | D16e | `CandidatePreviewProfileTab.tsx` | 1h | MEDIO |
| FIX-R06 | **BUG: Contradicao remoto** — validar Modelo Trabalho vs Aceita Remoto | D16j | `CandidatePreviewProfileTab.tsx` | 2h | ALTO |
| FIX-R07 | **Erro resumo sem recovery automatico** — retry com exponential backoff | D15 | `useCandidatePreviewCore.tsx` | 2h | ALTO |

## Sprint Bugfix Vue Producao — Bugs descobertos na revisao visual (Sessao 2)

| # | Correcao | IDs | Arquivo Vue | Esforco | Impacto |
|---|---------|-----|------------|---------|---------|
| FIX-V01 | **JSON RAW exposto em Log de Atualizacao** — sanitizar Data raw no feed de atividades, ocultar objeto JSON bruto, mostrar apenas campos humanamente legiveis (nome antigo→novo, campos alterados) | VUE-BUG-01 | `applies.vue` ou componente de activities/log | 1 dia | **CRITICO** |
| FIX-V02 | **Dados internos expostos em Log de Criacao** — ocultar "Questt Candidate 111710", IDs internos, Account Id do feed de atividades. Mostrar apenas nome real do candidato | VUE-BUG-02 | `applies.vue` ou componente de activities/log | 4h | ALTO |
| FIX-V03 | **Texto experiencia nao formatado** — aplicar formatacao (quebras de linha, bullet points) ao texto bruto de experiencia profissional no feed de atividades | VUE-BUG-03 | `applies.vue` | 2h | MEDIO |
| FIX-V04 | **HTML RAW na Tab Curriculo** — renderizar HTML do curriculo em vez de exibir como texto plano com tags visiveis. Usar `v-html` com sanitizacao (DOMPurify) | VUE-BUG-04 | `curriculum_text.vue` | 4h | **CRITICO** |
| FIX-V05 | **Tooltips ausentes nos icones de acao** — adicionar `v-tooltip` nos 8 icones sem tooltip (email, telefone, agenda, copiar, comparar, favoritar, desabilitar, notas) | VUE-BUG-05 | `preview.vue` | 2h | MEDIO |
| FIX-V06 | **Remuneracao BRL 0,00** — ocultar secao de remuneracao ou mostrar "Nao informado" quando Salario Mensal = 0 em vez de calcular 13.33x * 0 | VUE-NEW-02 | `remunerations.vue` | 1h | BAIXO |
| FIX-V07 | **Preview colado ao topo** — adicionar `top: <header-height>px` ou `margin-top` para que o painel de preview inicie abaixo do header da aplicacao (toolbar "Novo Candidato" + filtros), respeitando a hierarquia de layout. *Sobreposicao parcial com FIX-01 (D01/D03) — consolidar na implementacao* | VUE-BUG-06 | `preview.vue` / CSS layout | 4h | **ALTO** |
| FIX-V08 | **Espacamento preview-tabela** — adicionar gap/margem entre borda esquerda da tabela e borda direita do preview. Incluir `box-shadow` ou `border-left` para separacao visual clara. Garantir que a tabela nao seja "esmagada". *Sobreposicao parcial com FIX-01 (D01/D02) — consolidar na implementacao* | VUE-BUG-07 | `preview.vue` / CSS layout | 2h | **ALTO** |
| FIX-V09 | **Resize handle para largura do preview** — implementar drag handle ou botoes de preset (33%/50%/66%) para o usuario controlar a largura do painel de preview. Alternativa: converter para drawer overlay como no React, sem empurrar a tabela. *Sobreposicao parcial com FIX-01 (D02) — consolidar na implementacao* | VUE-BUG-08 | `preview.vue` / `[id].vue` | 1 dia | MEDIO |

> **Nota de sobreposicao:** FIX-V01/V02/V03 detalham bugs especificos da Sessao 2 que se sobrepoe parcialmente ao FIX-02 (atividades). FIX-V07/V08/V09 detalham bugs de layout da Sessao 2 que se sobrepoe parcialmente ao FIX-01 (layout). Na implementacao Jira, recomenda-se consolidar como sub-tasks dos FIX originais ou manter como cards separados com link "is related to". **Cards unicos descontando sobreposicoes: ~44.**

## Sprint Backport React — Adaptar features superiores do Vue

| # | Correcao | IDs | Arquivo React | Esforco | Impacto |
|---|---------|-----|--------------|---------|---------|
| FIX-R01 | Remuneracao detalhada (13.33x + beneficios) | V02 | `CandidatePreviewProfileTab.tsx` | 2 dias | ALTO |
| FIX-R02 | Score Analysis rico (requisitos expandiveis) | V03 | `CandidatePreviewProfileTab.tsx` | 3 dias | ALTO |
| FIX-R03 | Enriquecimento com creditos | V01 | `candidate-preview.tsx` | 1 dia | MEDIO |
| FIX-R08 | **Insights da Query com evidencias** — implementar secao colapsavel com insights por requisito, badges Essencial/Importante, e citacoes do curriculo como evidencia | VUE-GOOD-01 | `CandidatePreviewProfileTab.tsx` | 3 dias | ALTO |
| FIX-R09 | **Perguntas Sugeridas pela IA** — implementar secao com 3 perguntas contextuais geradas pela IA baseadas nas lacunas do candidato | VUE-GOOD-02 | `CandidatePreviewProfileTab.tsx` | 2 dias | ALTO |

---

# PARTE 7: REFERENCIA TECNICA

## Mapeamento de Componentes — Codigo Real

```
VUE (Producao)                                  REACT (Replit)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pages/user/candidates/[id].vue (102 linhas)     app/funil-de-talentos/page.tsx
features/candidates/preview.vue (855 linhas)    candidate-preview.tsx (858 linhas)
features/candidates/overview.vue (138 linhas)   CandidatePreviewProfileTab.tsx (861 linhas)
features/candidates/lia_assessment.vue (458)    CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/score_analysis (692)  CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/skills.vue (106)      CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/experiences.vue (134) CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/educations.vue (143)  CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/languages.vue (92)    CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/remunerations (191)   CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/addresses.vue (96)    CandidatePreviewProfileTab.tsx (embutido)
features/candidates/cards/layout.vue (53)       Card/CardHeader/CardTitle (shadcn)
features/candidates/applies.vue (30 linhas)     --- (sem equivalente direto)
features/candidates/files/wrapper.vue (120)     CandidateFilesTab.tsx (774 linhas)
features/candidates/files/uploader.vue (125)    CandidateFilesTab.tsx (embutido)
features/candidates/curriculum_text.vue (513)   --- (Replit usa FilePreviewModal)
--- (sem equivalente)                           CandidateActivitiesTab.tsx (278 linhas)
--- (sem equivalente)                           CandidateOpinionsTab.tsx (293 linhas)
--- (sem equivalente)                           OpinionCard.tsx (305 linhas)
--- (sem equivalente)                           LiaChatModal.tsx (315 linhas)
--- (sem equivalente)                           FilePreviewModal.tsx (546 linhas)
--- (sem equivalente)                           activities/ActivityTimeline.tsx (98)
--- (sem equivalente)                           activities/ActivityFilters.tsx (131)
--- (sem equivalente)                           activities/ActivityExpandedDetails.tsx (878)
--- (sem equivalente)                           useCandidatePreviewCore.tsx (666 linhas)
--- (sem equivalente)                           useCandidateFiles.tsx (201 linhas)
features/lia/candidates/sourced-profile-*       --- (Replit unifica no mesmo preview)
  sourced-profile-preview.vue (236)
  sourced-profile-header.vue (339)
  sourced-profile-overview.vue (183)
  sourced-profile-experience.vue (224)
  sourced-profile-education.vue (158)
  sourced-profile-skills.vue (130)
  sourced-profile-evaluation.vue (195)
  sourced-profile-summary.vue (24)
  sourced-profile-actions.vue (334)
composables/useCandidateFilters.ts (300)        useCandidatePreviewCore.tsx (embutido)
composables/useCandidateMatches.ts (39)         ---
stores/candidate_feedbacks.ts (80)              useCandidatePreviewCore.tsx (embutido)
```

## Metricas Comparativas

| Metrica | Vue (Producao) | React (Replit) |
|---------|---------------|----------------|
| Arquivos de preview | 30+ | 13 |
| Linhas totais | ~6.345 | ~6.196 |
| Tabs implementadas | 3 | 4 |
| Modais | 3 | 7+ |
| Botoes de acao | 8 (icones) | 9 (com labels) |
| Sub-componentes atividades | 0 | 3 |
| Cards perfil | 9 | 9 |
| Features exclusivas | 7 | 14 |
| Endpoints consumidos | 7 | 9 |
| Design tokens semanticos | Parcial | Completo |
| Data fetching | N+1 (por card) | Batch (centralizado) |

## State Management — Diferenca Arquitetural

**Vue:** Estado distribuido entre 10+ componentes. Cada card faz `$axios.get()` no `onMounted`. Props e computed fluem por hierarquia.

**React:** Estado centralizado em `useCandidatePreviewCore()` (666 linhas). Um hook retorna 40+ states e handlers. Todos os fetches sao batch.

## Icones — Mapeamento

| Funcao | React (lucide-react) | Vue (mdi + lucide) | Status |
|---|---|---|---|
| Brain/LIA | `Brain` | `lucide-brain` | OK |
| LinkedIn | `Linkedin` | `lucide-linkedin` | OK |
| Download | `Download` | `lucide-download` | OK |
| GitHub | `Code` | Nao existe no preview | **Ausente** |
| Upload | `Upload` | Nao existe | **Ausente** |
| Eye/Preview | `Eye` | Nao existe | **Ausente** |
| Trash/Delete | `Trash2` | Nao existe | **Ausente** |
| Calendar | `Calendar` | Nao existe no preview | **Ausente** |

## Metodologia de Scoring IA

### Pesos do Score Breakdown

| Componente | Peso | Descricao |
|---|---|---|
| Match Tecnico | 35% | Alinhamento de habilidades tecnicas com requisitos |
| Fit de Personalidade | 25% | Compatibilidade Big Five com arquetipo ideal |
| Relevancia de Experiencia | 20% | Experiencias previas similares ao contexto |
| Alinhamento Cultural | 20% | Valores e comportamentos compativeis |

### Niveis de Recomendacao

| Nivel | Score | Acao |
|---|---|---|
| `highly_recommended` | 85-100% | Priorizar para entrevista |
| `recommended` | 70-84% | Considerar para processo |
| `potential` | 55-69% | Avaliar gaps especificos |
| `low_match` | 40-54% | Arquivar para futuras vagas |
| `not_recommended` | 0-39% | Nao prosseguir |

### Archetypes Big Five

| Archetype | Perfil | Roles Ideais |
|---|---|---|
| Catalisador Visionario | Alto O/E, Baixo N | Fundador, PM, Diretor de Inovacao |
| Executor Confiavel | Alto C/A, Baixo N | GP, Analista Senior, Ops Manager |
| Guardiao de Clientes | Alto A/E, Medio O | CS, Account Manager |
| Estrategista Analitico | Alto O/C, Baixo E | Data Scientist, Arquiteto |
| Mediador Adaptavel | Alto A/O, Medio C | HRBP, Scrum Master |
| Rainmaker Audacioso | Alto E/O, Baixo A | Vendedor, BD, Founder |
| Operador Resiliente | Alto C, N controlado | SRE, Suporte Critico |
| Arquiteto Metodico | Alto C/O, Baixo E | Engenheiro Senior, QA Lead |

## Resumo de Arquivos a Modificar

### Frontend (`ats_front/develop`)

| Arquivo | Acao | Fixes |
|---------|------|-------|
| `features/candidates/preview.vue` | Modificar | FIX-01, FIX-07, FIX-08, FIX-25, FIX-29, FIX-31 |
| `features/candidates/lia_assessment.vue` | Modificar | FIX-05 |
| `features/candidates/cards/skills.vue` | Modificar | FIX-10 |
| `features/candidates/cards/experiences.vue` | Modificar | FIX-19 |
| `features/candidates/files/wrapper.vue` | Modificar | FIX-04, FIX-12 |
| `features/candidates/applies.vue` | Rewrite | FIX-02, FIX-11, FIX-20 |
| `features/candidates/opinions/CandidateOpinionsTab.vue` | **CRIAR** | FIX-03 |
| `features/candidates/opinions/OpinionCard.vue` | **CRIAR** | FIX-03, FIX-24 |
| `features/candidates/activities/ActivityFilters.vue` | **CRIAR** | FIX-11 |
| `features/candidates/activities/ActivityTimeline.vue` | **CRIAR** | FIX-20 |
| `features/candidates/LiaChatModal.vue` | **CRIAR** | FIX-09 |
| `features/candidates/files/FilePreviewModal.vue` | **CRIAR** | FIX-12b |

### Backend (FastAPI)

| Arquivo | Acao | Fixes |
|---------|------|-------|
| `app/schemas/analysis.py` | Modificar | FIX-06 |
| `app/domains/cv_screening/services/analysis_service.py` | Modificar | FIX-06, FIX-13, FIX-14 |
| `app/api/v1/opinions.py` | Modificar | FIX-15 |
| Models SQLAlchemy | Migration | FIX-22, FIX-30 |

---

# COMO CRIAR CARDS JIRA

## Template de Card

```
TITULO: [FIX-XX] Descricao curta da correcao
TIPO: Bug / Feature / Improvement
PRIORIDADE: Critico / Alto / Medio / Baixo
SPRINT: 1 / 2 / 3 / 4
ESTIMATIVA: X dias

DESCRICAO:
**Problema:** [Copiar da coluna "Correcao" na Parte 6]
**IDs relacionados:** [Copiar IDs da coluna "IDs"]
**Arquivo(s):** [Copiar da tabela "Arquivos a Modificar"]

**Comportamento atual (Vue):**
[Copiar da coluna "Vue (Producao)" na Parte 2 ou 3]

**Comportamento esperado (React referencia):**
[Copiar da coluna "React (Replit)" na Parte 2 ou 3]

**Correcao sugerida:**
[Copiar bloco de codigo da Parte 2, se disponivel]

**Criterio de aceite:**
- [ ] Comportamento alinhado com referencia React
- [ ] Sem regressao em funcionalidades existentes
- [ ] Teste manual no preview do candidato
```

## Agrupamento sugerido para Epics

| Epic | Cards | Sprint |
|------|-------|--------|
| **Layout & Navigation** | FIX-01, FIX-29, FIX-31 | 1, 4 |
| **Header & Actions** | FIX-07, FIX-08, FIX-09, FIX-25 | 2, 3 |
| **Tab Atividades** | FIX-02, FIX-11, FIX-20 | 1, 2, 3 |
| **Tab Arquivos** | FIX-04, FIX-12 | 1, 2 |
| **Tab Pareceres** | FIX-03, FIX-05, FIX-24 | 1, 2, 3 |
| **IA & Backend** | FIX-06, FIX-13, FIX-14, FIX-15 | 1, 2 |
| **Design System** | FIX-16, FIX-17, FIX-26 | 3, 4 |
| **Perfil Enriquecido** | FIX-10, FIX-18, FIX-19, FIX-21 | 2, 3 |
| **Database** | FIX-22, FIX-30 | 3, 4 |
| **Vue Producao Hotfix** | FIX-V01, FIX-V02, FIX-V03, FIX-V04, FIX-V05, FIX-V06, FIX-V07, FIX-V08, FIX-V09 | **Sprint 0 (hotfix)** |
| **Backport Vue→React** | FIX-R01, FIX-R02, FIX-R03, FIX-R08, FIX-R09 | Backlog |

## Documentos Relacionados

- **Evidencia de testes:** Este documento + screenshots em `attached_assets/` e `plataforma-lia/docs/screenshots/`
- **Componentes React (referencia):** `plataforma-lia/src/components/candidate-preview/` (13 arquivos, 6.196 linhas)
- **Backend (referencia):** `lia-agent-system/app/` (opinions, analysis, profile analysis APIs)
- **Auditoria busca/search:** `.agents/outputs/testes-funcionais-wedotalent.md` + `.agents/outputs/guia-completo-correcoes-wedotalent.md`

---

*Documento gerado a partir de: analise de codigo Vue real (GitHub API, 30+ arquivos), inspecao de codigo React (13 arquivos), testes Playwright e2e, e 48 screenshots de producao (3 candidatos: Lucas Campos, Davi Guides, Carolina Mendez).*
*Revisao FINALIZADA em 2026-04-03. 88 problemas catalogados, ~44 cards Jira unicos, 4 features superiores Vue identificadas para backport.*
