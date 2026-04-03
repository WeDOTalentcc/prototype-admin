# Auditoria QA — Candidate Preview Panel
## Producao WeDOTalent (app.wedotalent.cc) vs Referencia Replit

**Data:** 2026-04-03 | **Atualizado:** 2026-04-03 (consolidacao com comparacao codigo-a-codigo)
**Objetivo:** Identificar todos os problemas do **produto WeDOTalent em producao** que precisam ser corrigidos para atingir a qualidade da **implementacao de referencia no Replit**, com **comparacao direta do codigo Vue real** obtido do repositorio `wedotalent/ats_front` via GitHub API.

**Convencao:** Cada item marca claramente:
- **[PROD]** = problema encontrado na producao WeDOTalent (precisa corrigir)
- **[REF]** = como esta no Replit (o design correto/desejado)

**Ambientes:**
- **Producao:** app.wedotalent.cc (Vue 3 / Vuetify 3 / Nuxt 3)
- **Referencia Replit:** plataforma-lia (React / Tailwind / Next.js + FastAPI)
- **Fonte Vue Real:** Repositorio `wedotalent/ats_front` branch `develop` (30+ arquivos, ~6.345 linhas)

**Evidencia Visual (Producao):**
- `Screen_Shot_1.23.34_PM` — Preview aberto, tab Perfil Completo (topo)
- `Screen_Shot_1.23.56_PM` — Perfil Completo scrollado (skills, requisitos)
- `Screen_Shot_1.24.14_PM` — Perfil Completo scrollado (idiomas, remuneracao)
- `Screen_Shot_1.24.35_PM` — Tab Atividades (modo preview, timeline)
- `Screen_Shot_1.25.00_PM` — Tab Atividades (mais entries no preview)
- `Screen_Shot_1.25.58_PM` — Tab Atividades (modo expandido/full page)

**Evidencia Visual (Replit):**
- `replit-ref-home.jpg` — Pagina principal Funil de Talentos
- `replit-ref-atividades-tab.jpg` — Tab Atividades com filtros e layout de referencia

**Estrutura do Documento:**
- **Secoes 1-8:** Problemas de Design/Frontend (63 issues)
- **Secoes 9-11:** Backend API, IA e Banco de Dados
- **Secao 12:** Verificacao funcional Playwright
- **Secao 13:** Plano de correcao priorizado (4 sprints)
- **Apendice A:** Mapeamento de componentes (React + Backend + DB)
- **Apendice B:** Evidencia visual + Mapeamento Vue real (codigo GitHub)
- **Apendice C:** Metodologia de Scoring IA
- **Apendice D:** Comparacao codigo-a-codigo — Header, Tabs e Perfil
- **Apendice E:** Comparacao codigo-a-codigo — Atividades, Arquivos, Pareceres e Acoes
- **Apendice F:** State Management, APIs e Design Tokens
- **Apendice G:** Features exclusivas e Plano de Convergencia

---

## Sumario Executivo

A producao WeDOTalent apresenta **divergencias significativas** em relacao ao design de referencia do Replit. Os problemas cobrem 4 dimensoes:

| Dimensao | Criticos | Altos | Medios | Baixos | Total |
|---|---|---|---|---|---|
| **1. Design/Frontend** | 6 | 12 | 15 | 8 | 41 |
| **2. Backend API** | 2 | 4 | 3 | 1 | 10 |
| **3. Inteligencia Artificial** | 1 | 3 | 1 | 1 | 6 |
| **4. Banco de Dados** | 0 | 0 | 4 | 2 | 6 |
| **Total** | **9** | **19** | **23** | **12** | **63** |

---

## 1. DESIGN — Estetica, Morfologia e Layout

### 1.1 Layout Geral do Preview Panel

| ID | Problema [PROD] | Referencia [REF] | Evidencia | Prioridade |
|---|---|---|---|---|
| D01 | **Preview empurra botoes da tabela para cima.** O painel lateral se estende ate o topo da pagina, comprimindo o header da tabela de candidatos e deslocando os botoes "Novo Candidato", "Nova Busca", "Salvar Busca" para fora da area visivel | O preview panel e um drawer lateral que **nao altera** o layout da tabela de candidatos. A tabela permanece intacta com seus botoes de acao visiveis | `Screen_Shot_1.23.34_PM` — botoes "Novo Candidato", "Nova Busca", "Salvar Busca" empurrados para cima, tabela truncada | **Critico** |
| D02 | **Largura do preview inconsistente.** Em modo preview (dentro da tabela), o painel ocupa ~50% da tela. Em modo expandido (full page), ocupa 100%. Nao ha transicao suave entre os dois modos | O Replit usa um drawer lateral com largura fixa que abre sobre a tabela (overlay), ou redireciona para pagina full `/funil-de-talentos/candidato/{id}` ao expandir | `Screen_Shot_1.23.34_PM` vs `Screen_Shot_1.25.58_PM` | **Alto** |
| D03 | **Header do preview fixo colado ao topo da viewport.** O header com nome/avatar/botoes fica preso ao topo quando o painel esta aberto, mesmo ao scrollar a tabela de candidatos ao lado | Na referencia, o header do candidato faz parte do scroll natural da pagina de detalhe, nao e sticky | `Screen_Shot_1.23.34_PM` — header fixo no topo | **Alto** |
| D04 | **Proporcao do conteudo desbalanceada.** O conteudo do preview (Parecer LIA, Score, Skills) ocupa muito espaco vertical com cards grandes, forcando scroll excessivo | O Replit usa cards compactos com `space-y-3` (12px), `p-2.5` (10px), `text-xs` (12px) como base, maximizando densidade de informacao | `Screen_Shot_1.23.34_PM` — card "Parecer LIA" ocupa ~30% da viewport | **Medio** |

### 1.2 Header do Candidato

| ID | Problema [PROD] | Referencia [REF] | Prioridade |
|---|---|---|---|
| D05 | **Avatar sem anel indicador.** Avatar circular com iniciais em fundo colorido, sem qualquer indicador visual de status | Componente `CandidateAvatar` com prop `showRing` que exibe anel de status (ativo, inativo, etc.) | **Baixo** |
| D06 | **Badge de ID numerico puro.** Exibe `4681` como badge numerico simples | Gera ID curto formatado `A72E80` (2 letras + 4 digitos) via `generateShortId()` com estilo mono | **Baixo** |
| D07 | **Redes sociais limitadas.** Apenas icone LinkedIn visivel no header | Header exibe LinkedIn + GitHub + StackOverflow + X/Twitter + Behance + Portfolio quando disponiveis | **Medio** |
| D08 | **Sem datas no header.** Nao exibe data de cadastro, ultima atualizacao ou ultimo contato | Row de datas com tooltips: "Cadastrado em", "Atualizado em", "Ultimo contato em" | **Alto** |
| D09 | **Sem botao LIA no header.** Falta icone Brain que abre o chat/analise da LIA | Botao Brain icon no header top-right que abre `LiaAnalysisModal` para gerar analise IA | **Alto** |

### 1.3 Botoes de Acao

| ID | Problema [PROD] | Referencia [REF] | Prioridade |
|---|---|---|---|
| D10 | **Botoes de acao como icones sem label.** Row de icones pequenos (email, telefone, calendario, etc.) sem texto descritivo, dificultando identificacao | Botoes com icone + texto: "Email", "WhatsApp", "Agendar Entrevista", "Triagem WSI", "Adicionar a Vaga", "Favoritar", "Adicionar a Lista", "Ocultar", "Feedback" | **Alto** |
| D11 | **Faltam acoes importantes.** Producao nao exibe botoes de "Triagem WSI", "Adicionar a Lista", "Ocultar", "Feedback" | Referencia tem 9 botoes de acao rapida com callbacks configurados | **Alto** |

### 1.4 Navegacao de Tabs

| ID | Problema [PROD] | Referencia [REF] | Prioridade |
|---|---|---|---|
| D12 | **Tab "Arquivos" truncada como "Arq...".** Em modo preview, o nome da tab e cortado por falta de espaco | Tabs com nomes completos: "Perfil Completo", "Atividades", "Arquivos", "Pareceres e Analises" | **Medio** |
| D13 | **Setas de navegacao < > entre candidatos existem mas nao estao no Replit.** Producao tem setas para navegar entre candidatos da lista sem fechar o preview | Replit nao possui esta funcionalidade — deve ser mantida na producao como feature positiva | **Informativo** (manter) |
| D14 | **Tab "Curriculo" aparece em modo expandido mas nao no preview.** Em full page, aparece uma tab extra "Curriculo" que nao existe no modo preview | Referencia nao tem tab "Curriculo" separada — arquivos de curriculo estao dentro da tab "Arquivos" | **Medio** |

---

## 2. DESIGN — Tab Perfil Completo

### 2.1 Parecer LIA

| ID | Problema [PROD] | Referencia [REF] | Evidencia | Prioridade |
|---|---|---|---|---|
| D15 | **Estado vazio sem acao.** Exibe "Aguardando triagem do candidato" com animacao de loading, sem botao para iniciar triagem | Card com Score, Archetype, Summary, botao "Atualizar" e timestamp. Se sem dados, exibe botao "Gerar Parecer" | `Screen_Shot_1.23.34_PM` — card "Parecer LIA" com estado vazio | **Critico** |
| D16 | **Score badge 87 sem contexto visual.** Badge numerico "87" no header sem escala de cores, sem label "Alta Confianca", sem indicacao do metodo | Score com barra circular colorida (verde/amarelo/vermelho), label "Alta Confianca", badge "Baseado em Rubrica" ou "WSI Score" | `Screen_Shot_1.23.34_PM` — badge "87" no header | **Alto** |

### 2.2 Analise de Score

| ID | Problema [PROD] | Referencia [REF] | Evidencia | Prioridade |
|---|---|---|---|---|
| D17 | **Card "Analise de Score" com layout desproporcionado.** O card ocupa muito espaco vertical. O grafico circular de 87% e grande demais em relacao ao conteudo textual | Referencia usa grid compacto 2 colunas para score breakdown, sem graficos grandes. Cada metrica e uma linha com label + valor + barra de progresso | `Screen_Shot_1.23.34_PM` — card "Analise de Score" com grafico desproporcional | **Medio** |
| D18 | **Resumo por Prioridade com cores inconsistentes.** Badges "Essencial" (vermelho), "Importante" (laranja), "Desejavel" (laranja claro) — escala de cores nao segue semaforo padrao | Design tokens do Replit usam: success (verde), warning (amarelo/laranja), error (vermelho) com semantica clara via `badgeStyles` | `Screen_Shot_1.23.56_PM` | **Medio** |

### 2.3 Mapa de Skills

| ID | Problema [PROD] | Referencia [REF] | Evidencia | Prioridade |
|---|---|---|---|---|
| D19 | **Skills como lista plana sem categorizacao.** "37 itens" exibidos como badges em fluxo continuo sem agrupamento ou hierarquia | Mapa categorizado por: Backend, Frontend, Data, DevOps, Design, Mobile + separacao entre CV Skills, LinkedIn Expertise, Soft Skills (LIA), Interesses, Tags com legenda colorida | `Screen_Shot_1.23.56_PM` — "Mapa de Skills 37 itens" plano | **Alto** |
| D20 | **Sem diferenciar fonte da skill.** Todas as badges tem mesmo estilo visual, impossivel saber se veio do CV, LinkedIn ou inferencia LIA | Referencia usa cores distintas: `wedo-cyan` para Soft Skills LIA, `wedo-magenta` para Interesses, badges normais para CV, e tooltips explicando a fonte | **Medio** |

### 2.4 Secoes Acordeao

| ID | Problema [PROD] | Referencia [REF] | Evidencia | Prioridade |
|---|---|---|---|---|
| D21 | **Secoes colapsaveis com contagem mas sem preview.** "Avaliacao por Requisitos (7)", "Insights da Query (7)", "Perguntas Sugeridas (3)" — apenas titulo + chevron | Referencia nao usa acordeoes para estas secoes — exibe o conteudo diretamente com scroll natural | `Screen_Shot_1.23.56_PM` | **Medio** |

### 2.5 Secoes Ausentes na Producao

| ID | Secao ausente [PROD] | Como esta no [REF] | Prioridade |
|---|---|---|---|
| D22 | **ExperienceHighlightCard** nao existe | Card no topo do perfil com resumo da experiencia gerado pela LIA em uma frase | **Medio** |
| D23 | **Perfil LinkedIn card** nao existe | Card com headline, idade estimada, seguidores, conexoes do LinkedIn | **Medio** |
| D24 | **Indicadores especiais** nao existem | Badges: Open to Work, Top University, Decision Maker, LCNU (blacklist) | **Medio** |
| D25 | **Preferencias Pessoais** nao visivel | Card com: Genero, Modelo Trabalho, Contrato, Remoto, Mudanca, Viagens, Consentimento LGPD | **Medio** |

### 2.6 Experiencia Profissional e Formacao

| ID | Problema [PROD] | Referencia [REF] | Prioridade |
|---|---|---|---|
| D26 | **Cards de experiencia simples.** Titulo, empresa, datas, descricao em texto plano | Cards com `border-left` colorida por industria, badges de startup/company size/tech stack, duracao calculada | **Alto** |
| D27 | **Remuneracao sem detalhamento.** Card "Remuneracao e Beneficios" exibe "BRL 0,00" para todos os campos | Card com separacao: Salario Atual, Pretensao (min/max), CLT, PJ, Freelance com formatacao monetaria | `Screen_Shot_1.24.14_PM` | **Medio** |
| D28 | **Idiomas sem nivel.** Exibe "Nao informado" em itálico | Referencia trata `null` graciosamente e exibe nivel de proficiencia quando disponivel | `Screen_Shot_1.24.14_PM` | **Baixo** |

---

## 3. DESIGN — Tab Atividades

### 3.1 Layout e Proporcoes

| ID | Problema [PROD] | Referencia [REF] | Evidencia | Prioridade |
|---|---|---|---|---|
| D29 | **Cards de atividade NAO abrem/expandem ao clicar.** Os cards exibem informacoes estaticas sem interacao — nao e possivel expandir para ver detalhes da atividade | Referencia tem cards expandiveis com `ChevronDown` icon. Ao clicar, renderiza `ActivityExpandedDetails` com conteudo especifico por tipo (email body, entrevista details, LIA evaluation scores, etc.) | `Screen_Shot_1.24.35_PM` — cards nao interativos | **Critico** |
| D30 | **Informacoes desconfiguradas nos cards.** O card "Inscrito em vaga" mostra dados raw do JSON no "Resumo das Alteracoes" (ex: `"url": "/recruiter/candidates/39825"`, `"skill_name": "weblogic"`) em vez de informacao formatada | Referencia formata cada tipo de atividade com layout especifico: email mostra From/To/Subject/Body, entrevista mostra data/duracao/local/entrevistadores, etc. | `Screen_Shot_1.25.58_PM` — JSON raw visivel no card "Log de Atualizacao" | **Critico** |
| D31 | **Cards desproporcionais.** O card "Log de Atualizacao" com "Resumo das Alteracoes" ocupa tela inteira com texto nao formatado, quebrando a proporcao visual | Cards na referencia tem altura maxima consistente com overflow scroll. Detalhes longos ficam dentro do card expandido com scroll interno | `Screen_Shot_1.25.58_PM` — card ocupando tela inteira | **Critico** |
| D32 | **Timeline com dots sem contexto de cor.** Dots verdes e roxos na timeline sem legenda explicando o significado das cores | Referencia usa dots color-coded por tipo de atividade com legenda visual: verde = sucesso, vermelho = erro, roxo = entrevista, cyan = LIA | `Screen_Shot_1.24.35_PM` | **Medio** |

### 3.2 Filtros de Atividade

| ID | Problema [PROD] | Referencia [REF] | Evidencia | Prioridade |
|---|---|---|---|---|
| D33 | **Filtros truncados no modo preview.** Em modo preview, apenas "Todas", "Emails", "Entrevistas" visiveis. Os demais ficam ocultos atras de scroll horizontal sem setas | Referencia exibe todos os filtros: Todas, Emails, Entrevistas, Testes, LIA, Ofertas, Inscricoes, Notas — todos visiveis | `Screen_Shot_1.24.35_PM` (preview: 3 filtros) vs `Screen_Shot_1.25.58_PM` (full: 8 filtros) | **Alto** |
| D34 | **Filtros diferentes entre preview e full page.** Preview mostra "Todas, Emails, Entrevistas" + chips ocultos. Full page mostra "Todas, Emails, Entrevistas, Testes, LIA, Ofertas, Inscricoes, Avaliacoes, Etapas" | Referencia tem os mesmos 8 filtros em ambos os modos: Todas, Emails, Entrevistas, Testes, LIA, Ofertas, Inscricoes, Notas | `Screen_Shot_1.25.58_PM` — filtros extras "Avaliacoes", "Etapas" que nao existem na referencia | **Medio** |
| D35 | **Falta botao "Nova Atividade".** Em producao nao ha botao para adicionar atividade manualmente | Referencia tem botao "Nova Atividade" com dropdown de categoria (Nota Geral) e textarea para adicionar nota sobre o candidato | **Alto** |
| D36 | **Falta campo de nota rapida.** Producao nao permite adicionar notas/anotacoes sobre o candidato diretamente na tab | Referencia tem campo "Adicione uma nota sobre este candidato..." com seletor de categoria e botao "Salvar" | **Alto** |

### 3.3 Feed de Atividades

| ID | Problema [PROD] | Referencia [REF] | Prioridade |
|---|---|---|---|
| D37 | **Sem agrupamento por data.** Atividades listadas cronologicamente sem separadores de periodo | Timeline com agrupamento: "Hoje", "Ontem", "Esta Semana", "Ultimas Semanas", "Anteriormente" | **Medio** |
| D38 | **Sem toggle Timeline/Lista.** Apenas visualizacao de timeline disponivel | Dois modos de visualizacao: Timeline (com linha vertical e dots) e Lista (cards compactos) | **Medio** |
| D39 | **Sem marcador "Inicio do processo".** Timeline comeca diretamente com o primeiro evento | Timeline termina com marcador "Inicio do processo" com ponto final | **Baixo** |

---

## 4. DESIGN — Tab Arquivos

| ID | Problema [PROD] | Referencia [REF] | Prioridade |
|---|---|---|---|
| D40 | **"Failed to fetch" em producao.** Tab Arquivos nao carrega arquivos, exibe erro | Referencia carrega lista de arquivos do backend com categorias e preview | **Critico** |
| D41 | **Sem drag-and-drop upload.** Producao nao tem area de upload arrastar-e-soltar | Referencia tem zona dashed de drag-and-drop com progress bar e suporte a multiplos formatos | **Alto** |
| D42 | **Sem preview de midia.** Nao e possivel visualizar PDF, imagem ou video inline | Referencia tem `FilePreviewModal` com: PDF page navigation, imagem com zoom/rotacao, video/audio com player, transcricao IA | **Alto** |
| D43 | **Tab "Curriculo" separada em full page.** Em modo expandido, producao cria uma tab separada "Curriculo" | Referencia mantem todos os arquivos (incluindo CV) dentro da tab "Arquivos" unificada | **Medio** |

---

## 5. DESIGN — Tab Pareceres e Analises

| ID | Problema [PROD] | Referencia [REF] | Prioridade |
|---|---|---|---|
| D44 | **Sem sub-tabs.** Producao exibe pareceres em lista unica sem separacao | Referencia separa em 2 sub-tabs: "Pareceres da LIA" (historico de avaliacoes) e "Analises" (analises salvas bullet_points, short_paragraph, detailed_bullets) | **Alto** |
| D45 | **Sem score breakdown visual.** Scores exibidos como numero simples | Referencia usa grid 2 colunas com label + valor + barra de progresso para cada metrica (Match Tecnico, Fit Personalidade, etc.) | **Alto** |
| D46 | **Sem secoes qualitativas expansiveis.** Producao nao exibe Pontos Fortes, Pontos de Atencao, Gaps, Skills Match separadamente | Referencia tem secoes expansiveis com listas bulleted: Pontos Fortes, Pontos de Atencao, Gaps Identificados, Skills Match (verde/vermelho), Proximos Passos | **Alto** |
| D47 | **Sem copiar/colar parecer.** Nao ha botao para copiar parecer formatado para clipboard | Referencia tem botao copiar com formatacao limpa para compartilhamento | **Medio** |
| D48 | **Sem historico de versoes.** Producao exibe apenas o parecer atual | Referencia exibe historico completo com versoes, timestamps, e score de cada avaliacao | **Alto** |

---

## 6. DESIGN — Tipografia, Cores e Design System

### 6.1 Tipografia

| ID | Problema [PROD] | Referencia [REF] | Prioridade |
|---|---|---|---|
| D49 | **Font family Roboto (Vuetify default).** Toda a interface usa Roboto como fonte primaria | Design System LIA v4.2.1 define: Open Sans 85% (UI) + Inter 10% (numeros/metricas, tabular-nums) + JetBrains Mono 5% (IDs, codigo) | **Medio** |
| D50 | **Tamanho base ~14px.** Textos de corpo usam 14px padrao Vuetify | Referencia usa `text-xs` (12px) como base, `text-micro` (10px) para badges e metadata — maximizando densidade informacional | **Medio** |
| D51 | **Sem hierarquia tipografica clara.** Titulos, labels e corpo com pesos similares | Hierarquia definida: `textStyles.label` (12px font-medium), `textStyles.bodySmall` (12px font-normal), `textStyles.caption` (10px micro) | **Medio** |

### 6.2 Cores e Tokens

| ID | Problema [PROD] | Referencia [REF] | Prioridade |
|---|---|---|---|
| D52 | **Cores de badge inconsistentes.** Badge "senior" em ciano, scores em verde, sem padrao semantico claro | Design tokens semanticos: `badgeStyles.success` (verde), `badgeStyles.warning` (amarelo), `badgeStyles.error` (vermelho), `badgeStyles.info` (azul) | **Medio** |
| D53 | **Sombras Vuetify (elevation).** Cards usam box-shadow do Material Design | Referencia usa borders sem sombras: `border-lia-border-subtle`, `border-lia-border-default` | **Baixo** |
| D54 | **Sem suporte dark mode.** Interface apenas em modo claro | Tokens adaptaveis: `--lia-bg-primary` (white/dark), `--lia-text-primary` (dark/white) | **Baixo** |

### 6.3 Espacamento e Proporcoes

| ID | Problema [PROD] | Referencia [REF] | Prioridade |
|---|---|---|---|
| D55 | **Cards com padding excessivo.** Espacamento interno dos cards visivelmente maior que o necessario, reduzindo conteudo util visivel | Referencia: cards com `p-2.5` (10px), headers com `py-1.5 px-2.5`, `space-y-3` (12px) entre cards | **Medio** |
| D56 | **Border radius Material Design (~4px).** Cantos arredondados com raio pequeno padrao Vuetify | Referencia usa `rounded-md` (6px) como padrao | **Baixo** |

---

## 7. DESIGN — Nomenclatura e Terminologia

### 7.1 Nomes das Tabs

| Contexto | Producao [PROD] | Referencia [REF] | Divergencia | Prioridade |
|---|---|---|---|---|
| Tab 1 | `Perfil Completo` | `Perfil Completo` | Igual | -- |
| Tab 2 | `Atividades` | `Atividades` | Igual | -- |
| Tab 3 (preview) | `Arq...` (truncado) | `Arquivos` | Truncamento por espaco, nome igual | **Medio** |
| Tab 3 (full page) | `Arquivos` | `Arquivos` | Igual | -- |
| Tab 4 (preview) | Nao visivel (truncado apos "Arq...") | `Pareceres e Analises` | Producao trunca, nao exibe | **Alto** |
| Tab 4 (full page) | `Pareceres` (sem "e Analises") | `Pareceres e Analises` | **Diferente** — producao omite "e Analises" | **Alto** |
| Tab extra (full page only) | `Curriculo` | Nao existe | **Producao adiciona tab extra** que nao existe na referencia | **Medio** |

### 7.2 Headers de Secao

| Secao | Producao [PROD] | Referencia [REF] | Divergencia | Prioridade |
|---|---|---|---|---|
| Resumo IA do candidato | `Parecer LIA` | `Parecer LIA` | Igual | -- |
| Card de score numerico | `Analise de Score` | Nao existe como card separado — score fica dentro do `Parecer LIA` | **Diferente** — producao separa em card proprio | **Medio** |
| Requisitos por prioridade | `Resumo por Prioridade` | Nao existe como secao separada — dados integrados no score breakdown do OpinionCard | **Diferente** — producao tem secao extra | **Medio** |
| Secoes acordeao de requisitos | `Avaliacao por Requisitos (7)` / `Insights da Query (7)` / `Perguntas Sugeridas (3)` | Nao existem como secoes acordeao — conteudo similar aparece dentro do OpinionCard expandido | **Diferente** — producao usa acordeoes, referencia usa cards expandiveis | **Alto** |
| Competencias tecnicas | `Mapa de Skills` | `Mapa de Skills` | Igual no titulo, diferente no conteudo (plano vs categorizado) | -- |
| Historico profissional | `Experiencia Profissional` (implicito) | `Experiencia Profissional` | Igual | -- |
| Compensacao | `Remuneracao e Beneficios` | `Remuneracao` | **Diferente** — producao inclui "e Beneficios" | **Baixo** |
| Subtotal financeiro | `Remuneracao Total Anual` | Nao existe como campo unico — exibe por tipo (CLT/PJ/Freelance) | **Diferente** — producao calcula total anual, referencia mostra por modalidade | **Medio** |
| Idiomas | `Idiomas` | `Idiomas` | Igual | -- |
| Endereco | `Endereco` | `Endereco` | Igual | -- |

### 7.3 Feed de Atividades

| Elemento | Producao [PROD] | Referencia [REF] | Divergencia | Prioridade |
|---|---|---|---|---|
| Titulo da secao | `Feed de Atividades` (com contagem: `6`) | `Feed de Atividades` (com contagem: `0`) | Igual no nome | -- |
| Filtro de periodo | `Todo periodo` (dropdown) | `Todo periodo` (dropdown) com opcoes: Ultimos 7 dias, 30 dias, 3 meses | Igual no label, referencia tem mais opcoes | **Baixo** |
| Filtros de tipo (preview) | `Todas`, `Emails`, `Entrevistas` (demais ocultos) | `Todas`, `Emails`, `Entrevistas`, `Testes`, `LIA`, `Ofertas`, `Inscricoes`, `Notas` (todos visiveis) | **Diferente** — producao trunca, referencia mostra todos | **Alto** |
| Filtros de tipo (full page) | `Todas`, `Emails`, `Entrevistas`, `Testes`, `LIA`, `Ofertas`, `Inscricoes`, `Avaliacoes`, `Etapas` | `Todas`, `Emails`, `Entrevistas`, `Testes`, `LIA`, `Ofertas`, `Inscricoes`, `Notas` | **Diferente** — producao tem `Avaliacoes` e `Etapas` que nao existem na referencia. Referencia tem `Notas` que nao existe na producao | **Alto** |
| Tipo de card "Inscricao" | `Inscrito em vaga - {nome da vaga}` | `Inscrito em vaga - {nome da vaga}` | Igual no titulo | -- |
| Badge de tipo | `Criacao` (badge verde) | Badges coloridos por tipo de atividade com cores semanticas | Label igual, estilo visual diferente | **Medio** |
| Card "Log de Atualizacao" | `Log de Atualizacao` com badge `Atualizacao` (rosa) | Nao existe como tipo separado — atualizacoes integradas nos cards de atividade | **Diferente** — producao tem tipo de card extra com dados raw | **Alto** |
| Secao "Resumo das Alteracoes" | `Resumo das Alteracoes` com JSON raw (Name: X -> Y, Email: X -> Y, etc.) | Nao existe — referencia formata mudancas de forma legivel dentro do card expandido | **Critico** — producao exibe dados brutos |

### 7.4 Botoes de Acao (Header)

| Producao [PROD] | Referencia [REF] | Divergencia | Prioridade |
|---|---|---|---|
| Icones-only: email, telefone, calendario, clipboard, kanban, estrela, olho, mensagem | Labels: `Email`, `WhatsApp`, `Agendar Entrevista`, `Triagem WSI`, `Adicionar a Vaga`, `Favoritar`, `Adicionar a Lista`, `Ocultar`, `Feedback` | **Diferente** — producao usa so icones, referencia usa icone + texto | **Alto** |
| 8 icones em row horizontal | 9 botoes com labels em row horizontal com overflow | **Diferente** — referencia tem 1 acao a mais (Feedback) | **Medio** |

### 7.5 Pareceres e Analises

| Elemento | Producao [PROD] | Referencia [REF] | Divergencia | Prioridade |
|---|---|---|---|---|
| Sub-tabs | Nao existem — lista unica | `Pareceres da LIA` + `Analises` (2 sub-tabs) | **Diferente** — referencia separa | **Alto** |
| Tipo de analise | Nao visivel na producao | `bullet_points`, `short_paragraph`, `detailed_bullets` | **Diferente** — referencia oferece 3 formatos | **Alto** |
| Score label | `87` (badge numerico simples) | `Score: 85/100` ou `WSI: 4.2/5` com label descritivo | **Diferente** — referencia indica escala e tipo | **Alto** |
| Metodo de scoring | `Metodo de Scoring: Baseado em Rubrica` | Nao exibe metodo explicitamente, inferido pelo tipo de parecer (general vs wsi) | **Diferente** — producao explicita o metodo | **Informativo** (manter) |
| Nivel de confianca | `Alta Confianca` (badge verde) | Nao exibe nivel de confianca | **Diferente** — producao mostra, referencia nao | **Informativo** (manter) |

### 7.6 Campos de Dados (Backend -> Frontend)

| Campo API | Producao usa como | Referencia usa como | Divergencia |
|---|---|---|---|
| `candidate.id` | ID numerico ATS (ex: `4681`) | Short ID gerado `A72E80` via `generateShortId()` | **Diferente** — producao usa ID real, referencia gera formato curto |
| `candidate.seniority_level` | Badge ciano `senior` | Badge `badgeStyles.warning` (amarelo/laranja) | **Diferente** — cor inconsistente |
| `candidate.lia_score` | Badge numerico `87` no header | Score dentro do card Parecer LIA com barra circular | **Diferente** — posicionamento diferente |
| `opinion.score` | Grafico circular com `87%` no card Analise de Score | Grid 2 colunas no OpinionCard com breakdown por metrica | **Diferente** — visualizacao diferente |
| `opinion.recommendation` | `Alta Confianca` (badge) | `highly_recommended` / `recommended` / `potential` / etc. mapeado para label PT-BR | **Diferente** — producao usa "confianca", referencia usa "recomendacao" |
| `activity.changes` | JSON raw no "Resumo das Alteracoes" | Formatado por tipo de atividade no `ActivityExpandedDetails` | **Diferente** — producao nao formata |

---

## 8. DESIGN — Interacoes e Funcionalidades

### 8.1 Funcionalidades Ausentes na Producao

| ID | Feature ausente [PROD] | Implementacao [REF] | Prioridade |
|---|---|---|---|
| D57 | **LIA Chat Modal** — chat individual com IA por candidato | `LiaChatModal.tsx` (315 linhas) — modal overlay com historico de conversa | **Alto** |
| D58 | **LIA Analysis Modal** — gerar nova analise IA sob demanda | `lia-analysis-modal.tsx` com tipos: bullet_points, short_paragraph, detailed_bullets | **Alto** |
| D59 | **Screening Media Modal** — player video/audio com transcricao IA | Dynamic import com transcricao timestamp, metricas de confianca/comunicacao/clareza | **Alto** |
| D60 | **DISC Assessment Modal** — resultado avaliacao DISC visual | Dynamic import com grafico DISC detalhado | **Alto** |
| D61 | **Big Five Modal** — resultado avaliacao Big Five visual | Dynamic import com radar chart Big Five | **Alto** |
| D62 | **Alertas de confirmacao** para acoes destrutivas | Dialogs para: "Gerar novo parecer substituira o atual", "Excluir analise?", etc. | **Medio** |
| D63 | **Toast notifications** de feedback | Sonner toasts para: sucesso de copia, erro de rede, confirmacao de acao | **Baixo** |

### 8.2 Funcionalidades Exclusivas da Producao (manter)

| ID | Feature [PROD] | Status |
|---|---|---|
| D64 | **Setas < > para navegar entre candidatos** sem fechar preview | Manter — UX positiva, adicionar ao Replit |
| D65 | **Dados reais de atividades** do ATS (inscricao em vaga, log de atualizacao) | Manter — producao tem dados reais vs demo no Replit |

---

## 9. BACKEND API — Problemas Identificados

### 9.1 Problemas Criticos

| ID | Problema | Onde | Impacto |
|---|---|---|---|
| B01 | **`company_id` hardcoded como `demo_company`** em todas as chamadas API do frontend Replit. Na producao Vue, o company_id vem da sessao do usuario, mas pode haver mismatch entre o que o frontend envia e o backend espera (`default`) | `useCandidatePreviewCore.tsx` linhas 77, 92, 105, 145 | Multi-tenancy comprometida — pareceres podem nao ser encontrados |
| B02 | **Analise IA nao filtra por `company_id`** — o `AnalysisRequest` schema nao tem campo company_id. Qualquer request analisa qualquer candidato sem isolamento de tenant | `app/schemas/analysis.py`, `analysis_service.py` | Vazamento de dados entre empresas |

### 9.2 Problemas de Alta Prioridade

| ID | Problema | Onde | Impacto |
|---|---|---|---|
| B03 | **N+1 query no opinions history.** Para cada opinion retornada, o backend faz query separada para buscar `job_vacancy.title` | `app/api/v1/opinions.py:110-117` | Performance degradada com muitos pareceres |
| B04 | **Count query ineficiente.** `list_candidate_opinions` carrega todos os records para contar em vez de `SELECT COUNT(*)` | `app/api/v1/opinions.py` | Carga desnecessaria de dados |
| B05 | **Files endpoint usa `BACKEND_URL` diretamente** no frontend, bypassing o proxy Next.js que adiciona headers de autenticacao | `useCandidateFiles.tsx:44,51,102,145,169` | CORS errors em producao, sem auth headers |
| B06 | **Tab Arquivos retorna "Failed to fetch" em producao.** Confirmado via Playwright no ambiente de producao | Endpoint `/api/v1/candidates/{id}/files` | Funcionalidade de arquivos inacessivel para usuarios |

### 9.3 Problemas de Media/Baixa

| ID | Problema | Onde | Impacto | Prioridade |
|---|---|---|---|---|
| B07 | **`recruiter_override` sem validacao de permissao.** API permite qualquer usuario sobrescrever override de parecer sem verificar role | `app/api/v1/opinions.py` | Seguranca — usuarios sem permissao podem alterar pareceres | **Medio** |
| B08 | **Tipo inconsistente de `candidate_id`** entre tabelas — UUID em `lia_opinions`, String(255) em `lia_profile_analyses` e `candidate_attachments` | Models SQLAlchemy | JOINs complicados entre tabelas relacionadas | **Medio** |
| B09 | **Sem FK entre `lia_profile_analyses`/`candidate_attachments` e `candidates`** | Models SQLAlchemy | Sem CASCADE delete, dados orfaos possiveis | **Medio** |
| B10 | **8 endpoints backend disponiveis mas NAO consumidos pelo frontend:** paginacao de opinions, PATCH opinion, POST opinion manual, cultural-fit, rubric evaluation, bias audit, experience highlights, profile-analysis save | Varios em `app/api/v1/` | Funcionalidade implementada no backend sem UI | **Baixo** |

---

## 10. INTELIGENCIA ARTIFICIAL — Problemas Identificados

### 10.1 Arquitetura IA

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
    |-- Big Five -> Archetype classification (8 tipos)
    |-- Score Breakdown -> match_tecnico (35%), fit_personalidade (25%),
    |                      relevancia_experiencia (20%), alinhamento_cultural (20%)
    |-- Recommendation -> highly_recommended / recommended / potential / low_match / not_recommended
    v
CandidateAnalysisResult -> Frontend
```

### 10.2 Problemas (IA)

| ID | Problema | Onde | Impacto | Prioridade |
|---|---|---|---|---|
| IA01 | **Sem multi-tenancy na analise IA.** `AnalysisRequest` nao tem campo `company_id` — analise nao e isolada por empresa | `app/schemas/analysis.py` | Sem separacao de dados entre tenants na geracao IA | **Critico** |
| IA02 | **FairnessGuard NAO integrado na geracao de parecer.** Existe no feedback personalizado mas nao e aplicado na analise do preview | `personalized_feedback_service.py` vs `analysis_service.py` | Parecer pode conter bias nao detectado (genero, etnia, idade) | **Alto** |
| IA03 | **Prompt Injection Guard existe mas nao aplicado nos inputs.** Nome do candidato, skills, experiencia nao sao sanitizados antes de enviar ao Claude | `app/shared/prompt_injection.py` nao chamado em `analysis_service.py` | Candidato com campos maliciosos pode manipular a analise | **Alto** |
| IA04 | **Score sem nivel de confianca.** Frontend exibe scores (ex: 87%) sem indicar se baseado em evidencia EXPLICIT ou INFERRED | `rubric_evaluation_service.py:331-392` usa regras anti-alucinacao, mas frontend nao mostra isso | **Alto** |
| IA05 | **Pesos fixos sem customizacao.** Score breakdown e sempre 35/25/20/20 independente da empresa ou vaga | `app/schemas/analysis.py:38-43` | Toda empresa recebe mesma ponderacao | **Medio** |
| IA06 | **Archetypes hardcoded.** 8 archetypes fixos no endpoint `/analysis/archetypes` | `app/api/v1/analysis.py:56-112` | Nao customizavel por empresa/vaga | **Baixo** |

---

## 11. BANCO DE DADOS — Problemas de Schema

| ID | Problema | Tabelas | Impacto | Prioridade |
|---|---|---|---|---|
| DB01 | **Tipo inconsistente de `candidate_id`** — UUID nativo em `lia_opinions`, String(255) em `lia_profile_analyses` e `candidate_attachments` | 3 tabelas | JOINs entre tabelas requerem conversao de tipo | **Medio** |
| DB02 | **`CandidateAttachment.id` e String** (gerado via `lambda: str(uuid4())`) em vez de UUID nativo PostgreSQL | `candidate_attachments` | Performance reduzida em indexacao e buscas | **Medio** |
| DB03 | **Sem Foreign Key entre `lia_profile_analyses.candidate_id` e `candidates.id`** | `lia_profile_analyses` | Sem CASCADE delete — analises orfas possiveis | **Medio** |
| DB04 | **Sem Foreign Key entre `candidate_attachments.candidate_id` e `candidates.id`** | `candidate_attachments` | Sem CASCADE delete — anexos orfaos possiveis | **Medio** |
| DB05 | **`languages` definido como `JSON, default={}`** no model mas producao pode retornar `null`** | `candidates` | Frontend precisa tratar tanto `null` quanto `{}` | **Baixo** |
| DB06 | **`past_locations` usa mutable default `default=[]`** no SQLAlchemy model | `candidates` | Potencial shared state entre instancias | **Baixo** |

---

## 12. Verificacao Funcional (Playwright e2e)

### 12.1 Resultados — Producao WeDOTalent

| Passo | Resultado | Observacao |
|---|---|---|
| Navegar para /user/candidates | PASS | Lista de candidatos carregada |
| Abrir preview de candidato | PASS | Drawer lateral com dados reais |
| Tab Perfil Completo | PASS | Header, skills, experiencia visiveis |
| Tab Atividades | PASS | Conteudo visivel, MAS cards nao expandem |
| Tab Arquivos | FAIL | Erro "Failed to fetch" — arquivos nao carregados |
| Tab Pareceres | PASS | Conteudo basico visivel |
| Fechar painel | PASS | Painel fecha corretamente |

### 12.2 Resultados — Replit (Referencia)

| Passo | Resultado | Observacao |
|---|---|---|
| Navegar para home | PASS | Pagina "Funil de Talentos" carregada |
| Abrir candidato via URL direta | PASS | Pagina de detalhe com dados do candidato |
| Tab Perfil Completo | PASS | Header, badges, skills, experiencia visiveis |
| Tab Atividades | PASS | Filtros e timeline renderizados (dados demo) |
| Tab Arquivos | PASS | Area de upload e lista de arquivos |
| Tab Pareceres e Analises | PASS | Sub-tabs e empty states funcionais |

---

## 13. Plano de Correcao Priorizado

### 13.1 Sprint 1 — Criticos (bloqueia uso)

| # | Correcao | IDs Relacionados | Esforco |
|---|---|---|---|
| FIX-01 | **Corrigir layout do preview panel** — drawer nao deve empurrar header/botoes da tabela. Usar overlay ou fixed positioning | D01, D02, D03 | Alto |
| FIX-02 | **Corrigir cards de atividade** — implementar expansao ao clicar, formatar dados corretamente (nao exibir JSON raw), definir altura maxima | D29, D30, D31 | Alto |
| FIX-03 | **Implementar acao no Parecer LIA** — adicionar botao "Gerar Parecer" quando estado vazio, conectar com API `POST /analysis/candidates` | D15 | Medio |
| FIX-04 | **Corrigir tab Arquivos** — resolver "Failed to fetch" em producao, implementar proxy correto | D40, B05, B06 | Medio |
| FIX-05 | **Corrigir proporcoes dos cards** — reduzir padding, usar tipografia menor, maximizar densidade | D04, D17, D31, D55 | Medio |
| FIX-06 | **Adicionar multi-tenancy na analise IA** — incluir company_id no AnalysisRequest | B02, IA01 | Medio |

### 13.2 Sprint 2 — Alta Prioridade (funcionalidade core)

| # | Correcao | IDs Relacionados | Esforco |
|---|---|---|---|
| FIX-07 | **Implementar botoes de acao com labels** — trocar icones-only por icone + texto | D10, D11 | Medio |
| FIX-08 | **Adicionar datas no header** — cadastro, atualizacao, ultimo contato | D08 | Baixo |
| FIX-09 | **Implementar botao LIA no header** e conectar com modal de chat/analise | D09 | Alto |
| FIX-10 | **Categorizar Mapa de Skills** — agrupar por Backend/Frontend/Data/etc. com cores por fonte | D19, D20 | Medio |
| FIX-11 | **Implementar todos os filtros de atividade** — mostrar 8 filtros visiveis, add "Nova Atividade" e campo de nota | D33, D34, D35, D36 | Medio |
| FIX-12 | **Implementar sub-tabs em Pareceres** — separar "Pareceres da LIA" e "Analises", add score breakdown visual | D44, D45, D46, D48 | Alto |
| FIX-13 | **Implementar upload drag-and-drop** e preview de midia | D41, D42 | Alto |
| FIX-14 | **Integrar FairnessGuard** na geracao de parecer | IA02 | Medio |
| FIX-15 | **Aplicar Prompt Injection Guard** nos inputs | IA03 | Medio |
| FIX-16 | **Corrigir N+1 query** no opinions history | B03, B04 | Medio |

### 13.3 Sprint 3 — Media Prioridade (polish)

| # | Correcao | IDs Relacionados | Esforco |
|---|---|---|---|
| FIX-17 | Implementar tipografia DS v4.2.1 (Open Sans + Inter + JetBrains Mono) | D49, D50, D51 | Medio |
| FIX-18 | Implementar design tokens semanticos de cores | D52, D53 | Medio |
| FIX-19 | Adicionar secoes ausentes no perfil (ExperienceHighlight, LinkedIn, Indicadores, Preferencias) | D22, D23, D24, D25 | Alto |
| FIX-20 | Melhorar cards de experiencia profissional (border colorida, tech stack, startup badge) | D26 | Medio |
| FIX-21 | Implementar agrupamento por data no timeline | D37, D38 | Medio |
| FIX-22 | Implementar modais avancados (LIA Chat, DISC, Big Five, Screening) | D57-D61 | Alto |
| FIX-23 | Corrigir FKs e tipos inconsistentes no banco | DB01-DB04 | Medio |
| FIX-24 | Adicionar copiar/colar parecer | D47 | Baixo |
| FIX-25 | Adicionar score com nivel de confianca | IA04 | Medio |

### 13.4 Sprint 4 — Baixa Prioridade (nice-to-have)

| # | Correcao | IDs Relacionados | Esforco |
|---|---|---|---|
| FIX-26 | Suporte dark mode | D54 | Alto |
| FIX-27 | Toast notifications | D63 | Baixo |
| FIX-28 | Alertas de confirmacao para acoes destrutivas | D62 | Baixo |
| FIX-29 | Tab overflow com setas | D12 | Baixo |
| FIX-30 | Corrigir defaults mutaveis no schema | DB05, DB06 | Trivial |

---

## Apendice A — Mapeamento de Componentes

### A.1 Frontend (Replit — Referencia)

| Componente | Arquivo | Linhas |
|---|---|---|
| `CandidatePreview` | `candidate-preview.tsx` | 858 |
| `CandidatePreviewProfileTab` | `candidate-preview/CandidatePreviewProfileTab.tsx` | 861 |
| `CandidateActivitiesTab` | `candidate-preview/CandidateActivitiesTab.tsx` | 277 |
| `CandidateFilesTab` | `candidate-preview/CandidateFilesTab.tsx` | 774 |
| `CandidateOpinionsTab` | `candidate-preview/CandidateOpinionsTab.tsx` | 292 |
| `OpinionCard` | `candidate-preview/OpinionCard.tsx` | 305 |
| `LiaChatModal` | `candidate-preview/LiaChatModal.tsx` | 315 |
| `FilePreviewModal` | `candidate-preview/FilePreviewModal.tsx` | 546 |
| `ActivityTimeline` | `candidate-preview/activities/ActivityTimeline.tsx` | 98 |
| `ActivityFilters` | `candidate-preview/activities/ActivityFilters.tsx` | 131 |
| `ActivityExpandedDetails` | `candidate-preview/activities/ActivityExpandedDetails.tsx` | 878 |
| `useCandidatePreviewCore` | `candidate-preview/useCandidatePreviewCore.tsx` | 666 |
| `useCandidateFiles` | `candidate-preview/useCandidateFiles.tsx` | 201 |

**Total frontend referencia:** ~6.196 linhas (13 arquivos)

### A.2 Backend (FastAPI)

| Modulo | Arquivo | Linhas |
|---|---|---|
| Opinions API | `app/api/v1/opinions.py` | 574 |
| Analysis API | `app/api/v1/analysis.py` | 151 |
| Profile Analysis API | `app/api/v1/lia_profile_analysis.py` | ~120 |
| Rubric Evaluation | `app/domains/cv_screening/services/rubric_evaluation_service.py` | 1386 |
| CV Scoring | `app/domains/cv_screening/services/cv_scoring_service.py` | ~200 |
| Fairness Guard | `app/shared/compliance/fairness_guard.py` | ~150 |

### A.3 Banco de Dados (SQLAlchemy Models)

| Tabela | Arquivo | Linhas |
|---|---|---|
| `candidates` + `experiences` + `education` | `libs/models/lia_models/candidate.py` | 616 |
| `lia_opinions` | `libs/models/lia_models/lia_opinion.py` | 164 |
| `lia_profile_analyses` | `libs/models/lia_models/lia_profile_analysis.py` | 66 |
| `candidate_attachments` | `libs/models/lia_models/candidate_attachment.py` | 106 |

---

## Apendice B — Evidencia Visual e Comparacao Lado a Lado

### B.1 Comparacao Direta por Componente (Producao vs Replit)

| Componente | Screenshot Producao | Screenshot/Componente Replit | Divergencias Principais |
|---|---|---|---|
| **Header + Perfil Completo (topo)** | `attached_assets/Screen_Shot_2026-04-03_at_1.23.34_PM.png` — Preview aberto com header fixo, Parecer LIA vazio, Analise de Score 87%, botoes icone-only | `CandidatePreview.tsx` linhas 193-606 + `CandidatePreviewProfileTab.tsx` linhas 69-170 — Header com avatar ring, badges, labels nos botoes, Parecer LIA com score+archetype+summary, botao "Atualizar" | D01 layout empurra botoes, D10 icones sem label, D15 parecer vazio, D16 score sem contexto |
| **Perfil Completo (meio: skills, requisitos)** | `attached_assets/Screen_Shot_2026-04-03_at_1.23.56_PM.png` — Skills planas 37 itens, Resumo por Prioridade, acordeoes Avaliacao/Insights/Perguntas | `CandidatePreviewProfileTab.tsx` linhas 170-397 — Mapa de Skills categorizado (Backend/Frontend/Data/DevOps/Design/Mobile), Soft Skills LIA com cor cyan, sem acordeoes separados | D19 skills nao categorizadas, D21 acordeoes vs cards expandiveis |
| **Perfil Completo (fundo: remuneracao)** | `attached_assets/Screen_Shot_2026-04-03_at_1.24.14_PM.png` — Idiomas "Nao informado", Remuneracao e Beneficios BRL 0,00, Remuneracao Total Anual | `CandidatePreviewProfileTab.tsx` linhas 680-858 — Idiomas com nivel, Remuneracao por tipo (CLT/PJ/Freelance), Preferencias Pessoais, Endereco | D27 remuneracao zerada, D25 preferencias ausentes |
| **Tab Atividades (preview)** | `attached_assets/Screen_Shot_2026-04-03_at_1.24.35_PM.png` — Timeline com 3 filtros visiveis, dots verde/roxo sem legenda, cards estaticos | `replit-ref-atividades-tab.jpg` + `CandidateActivitiesTab.tsx` — 8 filtros visiveis, campo nota, botao "Nova Atividade", cards expandiveis | D29 cards nao abrem, D33 filtros truncados, D35 sem Nova Atividade |
| **Tab Atividades (entries)** | `attached_assets/Screen_Shot_2026-04-03_at_1.25.00_PM.png` — Card "Inscrito em vaga" com badge "Criacao", "Log de Atualizacao" com dados raw | `ActivityExpandedDetails.tsx` — Cards formatados por tipo com layout especifico (email body, entrevista detalhes, LIA scores) | D30 JSON raw, D31 cards desproporcionais |
| **Tab Atividades (full page)** | `attached_assets/Screen_Shot_2026-04-03_at_1.25.58_PM.png` — 8 filtros + "Avaliacoes"/"Etapas", Log de Atualizacao com JSON completo visivel | `ActivityFilters.tsx` — 8 filtros com "Notas" em vez de "Avaliacoes"/"Etapas", sem JSON raw | D30 dados brutos, D34 filtros diferentes |
| **Pagina Principal** | (Producao: /user/candidates com lista de candidatos) | `replit-ref-home.jpg` — Funil de Talentos com busca inteligente multimodal | Layout e navegacao distintos |

### B.2 Inventario de Screenshots

**Producao WeDOTalent** (7 screenshots fornecidos pelo usuario, em `attached_assets/`):

| # | Arquivo | Conteudo | IDs de Problemas |
|---|---|---|---|
| P1 | `Screen_Shot_2026-04-03_at_1.23.34_PM_1775233423155.png` | Preview aberto, Perfil Completo (topo) | D01, D10, D15, D16, D17 |
| P2 | `Screen_Shot_2026-04-03_at_1.23.56_PM_1775233443459.png` | Perfil scrollado (skills, requisitos) | D19, D21, D18 |
| P3 | `Screen_Shot_2026-04-03_at_1.24.14_PM_1775233458231.png` | Perfil scrollado (idiomas, remuneracao) | D27, D28, D55 |
| P4 | `Screen_Shot_2026-04-03_at_1.24.35_PM_1775233481048.png` | Atividades (preview mode) | D29, D32, D33 |
| P5 | `Screen_Shot_2026-04-03_at_1.25.00_PM_1775233511917.png` | Atividades (mais entries) | D30, D31 |
| P6 | `Screen_Shot_2026-04-03_at_1.25.00_PM_1775233539908.png` | Atividades (duplicata, entries) | D30, D31 |
| P7 | `Screen_Shot_2026-04-03_at_1.25.58_PM_1775233561500.png` | Atividades (full page expandido) | D30, D34, D37 |

**Replit Referencia** (4 screenshots capturados, em `plataforma-lia/docs/screenshots/`):

| # | Arquivo | Conteudo |
|---|---|---|
| R1 | `replit-ref-home.jpg` | Pagina principal Funil de Talentos |
| R2 | `replit-ref-atividades-tab.jpg` | Tab Atividades com filtros, nota, "Nova Atividade" |
| R3 | `replit-01-funil-de-talentos.jpg` | Busca com sugestoes |
| R4 | `replit-02-search-with-query.jpg` | Busca com query preenchida |

**Nota sobre cobertura de screenshots Replit:** Screenshots das tabs Perfil Completo, Arquivos e Pareceres nao puderam ser capturados via screenshot tool devido a timeout de carregamento do Next.js (>10s). A analise dessas tabs foi feita via inspecao direta do codigo-fonte dos componentes React (6.196 linhas) e testes Playwright que confirmaram renderizacao correta.

### B.3 Mapeamento React (Replit) ↔ Vue (Producao) — Codigo Real

**Fonte Vue:** Repositorio `wedotalent/ats_front` branch `develop` (obtido via GitHub API)
**Fonte React:** `plataforma-lia/src/components/candidate-preview/` (Replit)

#### B.3.1 Arvore de Componentes

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
features/candidates/curriculum_text.vue (513)   --- (sem equivalente; Replit usa FilePreviewModal)
--- (sem equivalente)                           CandidateActivitiesTab.tsx (278 linhas)
--- (sem equivalente)                           CandidateOpinionsTab.tsx (293 linhas)
--- (sem equivalente)                           OpinionCard.tsx
--- (sem equivalente)                           LiaChatModal.tsx
--- (sem equivalente)                           FilePreviewModal.tsx
--- (sem equivalente)                           activities/ActivityTimeline.tsx
--- (sem equivalente)                           activities/ActivityFilters.tsx
--- (sem equivalente)                           activities/ActivityExpandedDetails.tsx (878)
--- (sem equivalente)                           useCandidatePreviewCore.tsx (666 linhas)
--- (sem equivalente)                           useCandidateFiles.tsx
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
composables/useCandidateMatches.ts (39)         --- (sem equivalente direto)
stores/candidate_feedbacks.ts (80)              useCandidatePreviewCore.tsx (embutido)
```

#### B.3.2 Contagem Total

| Metrica | Vue (Producao) | React (Replit) |
|---|---|---|
| Arquivos de preview | 30+ | 13 |
| Linhas totais | ~6.345 | ~6.196 |
| Tabs implementadas | 3 (Perfil, Atividades, Arquivos) | 4 (Perfil, Atividades, Arquivos, Pareceres) |
| Modais | 3 (Email, Enrich, AddToJob) | 7+ (LIA, Screening, DISC, BigFive, FilePreview, InsufficientData, LiaChat) |
| Cards de dados | 9 | 9 (embutidos no ProfileTab) |
| Sub-componentes atividades | 0 (tab basica) | 3 (Timeline, Filters, ExpandedDetails) |

---

## Apendice C — Metodologia de Scoring IA (Referencia)

### C.1 Pesos do Score Breakdown

| Componente | Peso | Descricao |
|---|---|---|
| Match Tecnico | 35% | Alinhamento de habilidades tecnicas com requisitos |
| Fit de Personalidade | 25% | Compatibilidade Big Five com arquetipo ideal |
| Relevancia de Experiencia | 20% | Experiencias previas similares ao contexto |
| Alinhamento Cultural | 20% | Valores e comportamentos compativeis |

### C.2 Niveis de Recomendacao

| Nivel | Score | Acao |
|---|---|---|
| `highly_recommended` | 85-100% | Priorizar para entrevista |
| `recommended` | 70-84% | Considerar para processo |
| `potential` | 55-69% | Avaliar gaps especificos |
| `low_match` | 40-54% | Arquivar para futuras vagas |
| `not_recommended` | 0-39% | Nao prosseguir |

### C.3 Archetypes Big Five

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

---

## Apendice D — Comparacao Codigo-a-Codigo: Header, Tabs e Perfil

**Fonte Vue:** Repositorio `wedotalent/ats_front` branch `develop` (GitHub API)
**Fonte React:** `plataforma-lia/src/components/candidate-preview/` (Replit)

### D.1 Header do Candidato — Vue (preview.vue linhas 140-230)

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
    <span class="tiny-circle"></span>
    <span>{{ candidate_record.current_company }}</span>
    <Icon name="lucide-linkedin" :color="candidate_record.linkedin ? 'primary' : 'body-light'" />
  </div>
</div>
```

### D.2 Header do Candidato — React (candidate-preview.tsx linhas 220-350)

```tsx
<div className="p-3 border-b border-lia-border-subtle bg-lia-bg-primary">
  <div className="flex items-start gap-3 mb-1.5">
    <CandidateAvatar name={c.name} avatarUrl={c.avatar_url} size="lg" showRing />
    <div className="flex-1 min-w-0">
      <div className="flex items-center gap-1.5 mb-0.5 flex-wrap">
        <h3 className={`${textStyles.title} truncate`}>{c.name}</h3>
        <Badge className="text-micro font-mono bg-lia-bg-tertiary">
          {generateShortId(c.name, c.id)}
        </Badge>
        {c.seniority_level && <Badge className={badgeStyles.warning}>{c.seniority_level}</Badge>}
        {c.years_of_experience && <Badge>{c.years_of_experience} anos</Badge>}
        {c.communication_consent !== undefined && (
          <Badge className={c.communication_consent ? 'bg-status-success/10' : 'bg-status-error/10'}>
            {c.communication_consent ? <CheckCircle /> : <AlertCircle />} LGPD
          </Badge>
        )}
      </div>
      <div className="flex items-center gap-1.5 flex-wrap">
        <p className={textStyles.bodySmall}>{c.position || 'Cargo nao informado'}</p>
        <span>•</span>
        <p>{c.current_company || 'Empresa'}</p>
        {c.industry && <><span>•</span><p>{c.industry}</p></>}
      </div>
    </div>
    <div className="flex items-center gap-1">
      <LiaAnalysisModal><Button><Brain className="w-5 h-5 text-wedo-cyan" /></Button></LiaAnalysisModal>
      <Button onClick={onOpenFullPage}><Expand /></Button>
      <Button onClick={onClose}><X /></Button>
    </div>
  </div>
  <div className="flex items-center gap-2 flex-wrap">
    {createdAt && <span><Calendar /> Cadastrado em {formatDate(createdAt)}</span>}
    {updatedAt && <span><Clock /> Atualizado em {formatDate(updatedAt)}</span>}
    {lastContactedAt && <span><Mail /> Ultimo contato {formatDate(lastContactedAt)}</span>}
  </div>
</div>
```

**NOTA:** O header React real e significativamente mais complexo que o resumo acima. Inclui 7 "rows" de informacao: nome/badges, cargo/empresa, datas, indicadores especiais (Open to Work, Top University, Decision Maker, LCNU), localizacao + redes, scores + contato, e botoes de acao.

### D.3 Diferencas Criticas do Header

| Aspecto | Vue (Producao) | React (Replit) | Impacto |
|---|---|---|---|
| **Avatar** | `v-avatar size="40"`, iniciais inline | `CandidateAvatar` com `showRing` para status, `size="lg"` | Ring de status ausente |
| **ID Badge** | ID numerico raw (`4681`) | `generateShortId(name, id)` → `A72E80` alfanumerico mono | UX confusa com ID numerico |
| **Badges extras** | Nenhum | Seniority level + Anos experiencia + LGPD consent | **3 badges ausentes** |
| **Indicadores** | Nenhum | Open to Work, Top University, Decision Maker, LCNU | **4 indicadores ausentes** |
| **Redes sociais** | Apenas LinkedIn | LinkedIn + GitHub + StackOverflow + X + Portfolio | 4 redes ausentes |
| **Datas** | Nenhuma data exibida | Cadastrado, Atualizado, Ultimo contato com icones | Info temporal ausente |
| **Scores header** | Score circular `v-progress-circular` (apenas 1) | LIA Score + Fit Score lado a lado com cores | Vue tem 1, React tem 2 |
| **Contato direto** | Nenhum no header | Email + telefone copiaveis inline | **Ausente** |
| **Localizacao** | Nao exibida no header | Cidade, Estado, Pais com icone MapPin | **Ausente** |
| **Tipografia** | `f13 font-weight-semibold font-serif` | `textStyles.title` (sans-serif) | Serif vs Sans-serif |

### D.4 Correcao Sugerida — Header Vue

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
      {{ candidate_record.role_name }}
      <span class="mx-1">•</span>
      {{ candidate_record.current_company }}
    </p>
    <div class="d-flex align-center ga-2 f9 text-body-light mb-1">
      <span class="d-flex align-center ga-1">
        <Icon name="lucide-calendar" size="10" color="body-light" />
        Cadastrado em {{ formatDate(candidate_record.created_at) }}
      </span>
      <span class="d-flex align-center ga-1">
        <Icon name="lucide-clock" size="10" color="body-light" />
        Atualizado em {{ formatDate(candidate_record.updated_at) }}
      </span>
    </div>
    <div class="d-flex align-center ga-1">
      <Icon name="lucide-linkedin" size="14"
        :color="candidate_record.linkedin ? 'primary' : 'body-light'"
        @click="openUrl(candidate_record.linkedin)" />
      <Icon name="lucide-github" size="14"
        :color="candidate_record.github ? 'on-surface' : 'body-light'"
        @click="openUrl(candidate_record.github)" />
      <Icon name="lucide-globe" size="14"
        :color="candidate_record.portfolio ? 'on-surface' : 'body-light'"
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

### D.5 Tabs e Navegacao — Vue (preview.vue linhas 260-300)

```vue
<div class="candidate-preview-tabs">
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
</div>
```

### D.6 Tabs e Navegacao — React (candidate-preview.tsx linhas 300-340)

```tsx
<div className="flex border-b border-lia-border-subtle bg-lia-bg-primary sticky top-0 z-10">
  {['perfil', 'atividades', 'arquivos', 'pareceres'].map((tab) => (
    <button key={tab}
      onClick={() => setActiveTab(tab)}
      className={`flex-1 flex items-center justify-center gap-1 py-2 text-xs font-medium
        border-b-2 transition-colors ${
          activeTab === tab
            ? 'border-lia-btn-primary-bg text-lia-text-primary bg-lia-bg-secondary'
            : 'border-transparent text-lia-text-tertiary hover:text-lia-text-secondary'
        }`}
    >
      {tabIcons[tab]} {tabLabels[tab]}
      {tab === 'pareceres' && opinionsCount > 0 && (
        <Badge className="text-micro px-1 py-0 ml-1">{opinionsCount}</Badge>
      )}
    </button>
  ))}
</div>
```

### D.7 Diferencas Criticas das Tabs

| Aspecto | Vue (Producao) | React (Replit) | Impacto |
|---|---|---|---|
| **Numero de tabs** | 4 (Perfil, Atividades, Arquivos, Curriculo) | 4 (Perfil, Atividades, Arquivos, Pareceres) | Tab "Pareceres" **ausente** no Vue; tab "Curriculo" **ausente** no React |
| **Tab Pareceres** | **NAO EXISTE** | Historico de pareceres LIA + Analises com subtabs | **Critico** — perda de historico |
| **Badge de contagem** | Nenhuma tab mostra contador | Tab Pareceres mostra `opinionsCount` | Info util ausente |
| **Componente** | `v-tabs` Vuetify com `grow density="compact"` | `button` customizado com Tailwind | Vuetify fornece animacao built-in |

### D.8 Correcao Sugerida — Tab Pareceres no Vue

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

### D.9 Tab Perfil — Estrutura Vue (overview.vue)

```
overview.vue
  ├── LiaAssessment (Parecer LIA — 458 linhas)
  ├── ScoreAnalysis (Score — 692 linhas, condicional)
  ├── Skills (106 linhas)
  ├── Experiences (134 linhas)
  ├── Educations (143 linhas)
  ├── Languages (92 linhas)
  ├── Remunerations (191 linhas)
  └── Addresses (96 linhas)
```

### D.10 Tab Perfil — Estrutura React (CandidatePreviewProfileTab.tsx)

```
CandidatePreviewProfileTab.tsx (861 linhas, tudo embutido)
  ├── ExperienceHighlightCard (card destaque)
  ├── Card "Parecer LIA" (~150 linhas)
  │   ├── Score circular SVG
  │   ├── WSI badge
  │   ├── Dimensoes com progress bars
  │   ├── Resumo/Highlights/Red Flags
  │   └── Botao "Analisar com LIA"
  ├── Card "Mapa de Skills" (~80 linhas)
  ├── Card "Experiencia Profissional" (~90 linhas)
  ├── Card "Formacao Academica" (~60 linhas)
  ├── Card "Idiomas" (~40 linhas)
  ├── Card "Remuneracao" (~80 linhas)
  └── Card "Endereco" (~30 linhas)
```

### D.11 Diferencas no Conteudo do Perfil

| Card | Vue (Producao) | React (Replit) | Delta |
|---|---|---|---|
| **Parecer LIA** | `lia_assessment.vue` (458 linhas) — Score circular `v-progress-circular size=72`, Recomendacao chip, WSI chip, Dimensoes com `v-progress-linear`, Highlights/Red Flags, Skills agrupadas por tipo | `CandidatePreviewProfileTab` — Score SVG customizado, WSI badge, Dimensoes com barras Tailwind, Highlights/Red Flags colapsaveis, Botao re-analise | Vue mais detalhado com 458 vs ~150 linhas; React mais compacto |
| **Score Analysis** | `score_analysis.vue` (692 linhas!) — Card separado com score detalhado, metodo de scoring, requisitos expandiveis, metricas de confianca | **Nao existe como card separado** — embutido no Parecer LIA | **Vue tem score analysis independente e mais rico** |
| **Skills** | `skills.vue` (106 linhas) — Chips `v-chip` com cores por `level` | Inline — Chips com cores + barras de proficiencia | React adiciona barras visuais |
| **Remunerations** | `remunerations.vue` (191 linhas) — **Muito detalhado**: salario base, anualizado (13.33x), componentes variaveis, beneficios valor/dia vs /mes, subtotal, total anual | Inline ~80 linhas — Salario atual + pretensao + modelo simples | **Vue significativamente superior** |
| **ExperienceHighlight** | **Nao existe** | `ExperienceHighlightCard` no topo do perfil | Feature exclusiva React |

### D.12 INSIGHT — Vue Superior em Remuneracao e Score Analysis

O **card de Remuneracao** do Vue (`remunerations.vue`) e **significativamente mais completo** que o React: calcula remuneracao anualizada (13.33x), lista componentes variaveis, mostra beneficios com valor diario vs mensal, subtotais por categoria e card de "Remuneracao Total Anual" com destaque visual. O React deveria adaptar esta logica.

O **card de Score Analysis** do Vue (`score_analysis.vue`, 692 linhas) e o componente mais complexo do preview inteiro: score circular com confianca, metodo de scoring, requisitos expandiveis, metricas de confianca, grid de skills matched vs missing. O React nao tem equivalente direto.

---

## Apendice E — Comparacao Codigo-a-Codigo: Atividades, Arquivos, Pareceres e Acoes

### E.1 Tab Atividades — Vue (BASICA)

O Vue **nao tem componente dedicado de atividades** no preview. O `applies.vue` (30 linhas) e apenas:

```vue
<template>
  <div class="pa-3">
    <AppliesTable :candidate_id="candidate_record.id" />
  </div>
</template>
```

### E.2 Tab Atividades — React (RICA)

```
CandidateActivitiesTab.tsx (278 linhas)
  ├── ActivityFilters.tsx — Filtros por tipo + periodo + view mode
  │   Tipos: todos, emails, entrevistas, lia, candidaturas, testes, ofertas, avaliacoes
  │   Periodos: todos, 7 dias, 30 dias, 3 meses
  │   Views: timeline, lista
  ├── ActivityTimeline.tsx — Timeline visual com dots coloridos
  └── ActivityExpandedDetails.tsx (878 linhas!) — Detalhes expandidos
      Tipos: email-sent, interview-scheduled, video-interview, lia-analysis,
      assessment, job-application, rubric_evaluation, test-result, onboarding,
      screening-audio/video, disc-assessment, big-five
```

**NOTA IMPORTANTE:** O React usa **dados demo** (`getDemoActivities()`) na tab Atividades via flag `NEXT_PUBLIC_USE_DEMO_DATA`. Os 15+ tipos de atividade sao **aspiracionais** — o backend nao tem endpoint real de timeline. O Vue `applies.vue` usa `AppliesTable` que busca dados **reais** de candidaturas.

### E.3 Correcao Sugerida — Atividades Vue (Estrutura)

```vue
<!-- NOVO: features/candidates/activities/ActivityFilters.vue -->
<template>
  <div class="d-flex align-center ga-2 flex-wrap">
    <v-chip-group v-model="selectedFilter" mandatory selected-class="text-primary">
      <v-chip v-for="filter in filters" :key="filter.value" :value="filter.value"
        size="small" variant="tonal" class="f10">
        <Icon :name="filter.icon" size="12" class="mr-1" />
        {{ filter.label }}
        <span v-if="filter.count > 0" class="ml-1 f9">({{ filter.count }})</span>
      </v-chip>
    </v-chip-group>
    <v-select v-model="periodFilter" :items="periods" density="compact"
      variant="outlined" class="f10" style="max-width: 140px;" hide-details />
  </div>
</template>
```

```vue
<!-- NOVO: features/candidates/activities/ActivityTimeline.vue -->
<template>
  <div class="d-flex flex-column">
    <div v-for="activity in activities" :key="activity.id"
      class="d-flex ga-3 position-relative mb-4 cursor-pointer"
      @click="$emit('expand', activity.id)">
      <div class="d-flex flex-column align-center" style="width: 24px;">
        <div class="rounded-circle d-flex align-center justify-center"
          :style="{ backgroundColor: getBgColor(activity.color), width: '24px', height: '24px' }">
          <Icon :name="activity.icon" size="12" :color="activity.color" />
        </div>
        <div v-if="!isLast(activity)" class="flex-grow-1"
          style="width: 2px; background: rgb(var(--v-theme-border-color));" />
      </div>
      <div class="flex-grow-1 pb-2">
        <div class="d-flex align-center justify-space-between">
          <span class="f11 font-weight-medium">{{ activity.title }}</span>
          <span class="f9 text-body-light">{{ formatRelativeTime(activity.timestamp) }}</span>
        </div>
        <v-chip size="x-small" :color="activity.chipColor" variant="tonal" class="mt-1 f9">
          {{ activity.typeLabel }}
        </v-chip>
      </div>
    </div>
  </div>
</template>
```

### E.4 Tab Arquivos — Vue (files/wrapper.vue, 120 linhas)

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

**API Vue:** `GET /users/data_files?where[reference_type]=Candidate&where[reference_id]={id}`

### E.5 Tab Arquivos — React (CandidateFilesTab.tsx, 774 linhas)

Funcionalidade rica: categorias automaticas (7), drag-drop upload, preview inline (PDF/imagem/video), tags, delete, tamanho formatado, data relativa.

### E.6 Diferencas Tab Arquivos

| Feature | Vue (120 linhas) | React (774 linhas) | Delta |
|---|---|---|---|
| **Upload** | `uploader.vue` separado, botao simples | Drag-drop + click, progress bar | React UX melhor |
| **Categorias** | Nenhuma | 7 categorias automaticas com icones | **Ausente** |
| **Preview** | Download apenas (nova aba) | Modal inline com viewer PDF/imagem/video | **Ausente** |
| **Delete** | Nao implementado | Botao com confirmacao | **Ausente** |
| **Tags** | Nao implementado | Tags automaticas por tipo | **Ausente** |
| **Tamanho** | Nao exibido | `formatFileSize()` | **Ausente** |
| **Data relativa** | Nao exibida | `formatRelativeTime()` | **Ausente** |
| **Drag & Drop** | Nao implementado | Area visual com feedback | **Ausente** |

### E.7 Correcao Sugerida — Arquivos Vue (Enriquecimento)

```vue
<template>
  <div class="pa-3">
    <div class="d-flex align-center justify-space-between mb-3">
      <div class="d-flex align-center ga-2">
        <Icon name="lucide-file-text" size="14" />
        <p class="f12 font-weight-medium">Arquivos e Documentos</p>
        <v-chip size="x-small" variant="tonal">{{ files.length }}</v-chip>
      </div>
      <v-btn size="small" variant="tonal" color="primary" @click="triggerUpload">
        <Icon name="lucide-plus" size="12" class="mr-1" />Adicionar
      </v-btn>
    </div>

    <div class="d-flex ga-1 flex-wrap mb-3">
      <v-chip v-for="cat in categories" :key="cat.value"
        :variant="selectedCategory === cat.value ? 'flat' : 'outlined'"
        size="x-small" @click="toggleCategory(cat.value)" class="cursor-pointer">
        {{ cat.icon }} {{ cat.label }} ({{ cat.count }})
      </v-chip>
    </div>

    <div class="border-dashed border-2 rounded-lg pa-4 text-center mb-3 cursor-pointer"
      :class="isDragging ? 'border-primary bg-primary-lighten-5' : 'border-border-color'"
      @dragover.prevent="isDragging = true" @dragleave="isDragging = false"
      @drop.prevent="handleDrop">
      <Icon name="lucide-upload" size="20" color="body-light" class="mb-1" />
      <p class="f10 text-body-light">Arraste arquivos aqui</p>
    </div>

    <div v-for="file in filteredFiles" :key="file.id"
      class="d-flex align-center ga-2 pa-2 border border-border-color rounded-lg mb-2">
      <Icon :name="getFileIcon(file)" size="16" :color="getCategoryColor(file)" />
      <div class="flex-grow-1">
        <p class="f11 text-on-surface">{{ file.name }}</p>
        <div class="d-flex align-center ga-2 f9 text-body-light">
          <span>{{ formatFileSize(file.size) }}</span>
          <span>{{ formatRelativeTime(file.created_at) }}</span>
        </div>
      </div>
      <v-btn icon variant="text" size="x-small" @click="previewFile(file)">
        <Icon name="lucide-eye" size="14" />
      </v-btn>
      <v-btn icon variant="text" size="x-small" @click="downloadFile(file)">
        <Icon name="lucide-download" size="14" />
      </v-btn>
    </div>
  </div>
</template>
```

### E.8 Tab Pareceres (Exclusiva React)

`CandidateOpinionsTab.tsx` (293 linhas) — **nao existe no Vue**:
1. **Subtabs**: "Pareceres da LIA" e "Analises"
2. **Historico de pareceres**: Lista cronologica com score, recomendacao, texto completo
3. **OpinionCard**: Card expandivel com botao copiar
4. **Analises salvas**: Analises versus vagas especificas
5. **Acoes**: Copiar, deletar, expandir/colapsar

### E.9 Correcao Sugerida — Tab Pareceres Vue

```vue
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

### E.10 Botoes de Acao — Vue (preview.vue linhas 230-260)

```vue
<div class="d-flex align-center ga-1 py-1 px-3 border-b border-border-color">
  <v-menu>
    <template #activator="{ props }">
      <v-btn v-bind="props" size="small" variant="tonal" color="primary" class="f11">
        <Icon name="lucide-ellipsis" size="14" />
      </v-btn>
    </template>
    <v-list density="compact">
      <v-list-item @click="openFullPage"><v-list-item-title>Abrir Completo</v-list-item-title></v-list-item>
      <v-list-item @click="addToJob"><v-list-item-title>Adicionar a Vaga</v-list-item-title></v-list-item>
      <v-list-item @click="sendEmail"><v-list-item-title>Enviar Email</v-list-item-title></v-list-item>
      <v-list-item @click="startEnrich"><v-list-item-title>Enriquecer</v-list-item-title></v-list-item>
    </v-list>
  </v-menu>
  <v-tooltip location="bottom" v-for="action in quickActions">
    <template #activator="{ props }">
      <v-btn v-bind="props" icon variant="text" size="small" @click="action.handler">
        <Icon :name="action.icon" size="16" />
      </v-btn>
    </template>
    <span>{{ action.tooltip }}</span>
  </v-tooltip>
</div>
```

### E.11 Diferencas nos Botoes

| Botao/Acao | Vue | React | Delta |
|---|---|---|---|
| **Email** | Via menu dropdown | Botao direto com icone | React mais acessivel |
| **WhatsApp** | Nao implementado | Botao direto | **Ausente** |
| **Triagem WSI** | Nao implementado | Botao com callback | **Ausente** |
| **Agendamento** | Nao implementado | Botao com callback | **Ausente** |
| **Feedback** | Nao implementado | Botao com callback | **Ausente** |
| **LIA Chat** | Nao implementado | Botao "Perguntar a LIA" abre modal | **Ausente** — feature principal |
| **Adicionar a Vaga** | Menu dropdown item | Menu dropdown item | Equivalente |
| **Enriquecer** | Menu dropdown + dialog com creditos | Nao implementado | **Vue tem, React nao** |
| **Favoritar** | Nao implementado | Toggle com coracao | **Ausente** |
| **Navegacao prev/next** | Nao implementado | Setas `<` `>` com `1 de 42` | **Ausente** |

### E.12 Modais — Comparacao

| Modal | Vue | React | Status |
|---|---|---|---|
| **SendEmailDialog** | Componente externo importado | Botao direto | Ambos tem |
| **Enrich Confirm** | Inline `v-dialog` com creditos | Nao implementado | **Vue exclusivo** |
| **Add to Job** | Inline `v-dialog` | Menu dropdown | Ambos tem |
| **LIA Chat** | Nao existe | `LiaChatModal.tsx` | **React exclusivo** |
| **LIA Analysis** | Nao existe | `lia-analysis-modal.tsx` (dynamic import) | **React exclusivo** |
| **Screening Media** | Nao existe | `screening-media-modal.tsx` (dynamic import) | **React exclusivo** |
| **DISC Assessment** | Nao existe | `disc-assessment-modal.tsx` (dynamic import) | **React exclusivo** |
| **Big Five** | Nao existe | `big-five-modal.tsx` (dynamic import) | **React exclusivo** |
| **File Preview** | Nao existe | `FilePreviewModal.tsx` | **React exclusivo** |

---

## Apendice F — State Management, APIs e Design Tokens

### F.1 State Management — Vue

```
preview.vue (script setup)
  ├── Props: candidate_id, candidate_record (recebidos do pai)
  ├── Refs locais: active_tab, showEnrichConfirm, showAddToJobDialog...
  ├── Computed: candidateScore, scoreColor, hasScore
  ├── Watch: candidate_record (recarrega dados)
  └── Methods: openFullPage, sendEmail, confirmEnrich, saveAddToJob

overview.vue (script setup)
  ├── Props: candidate_record, is_fullscreen
  ├── Reactive: candidate = reactive(setCandidate())
  └── Computed: hasScoreAnalysis

Cada card (experiences, educations, etc.):
  ├── Props: candidate
  ├── onMounted: fetch dados via $axios
  └── Refs locais para dados
```

### F.2 State Management — React

```
candidate-preview.tsx
  └── useCandidatePreviewCore(candidate) — 666 linhas de logica centralizada
      ├── States: activeTab, showLiaModal, liaConversation, selectedFile...
      ├── States: opinionsData, isLoadingOpinions, opinionsHistory...
      ├── States: screeningModalOpen, discModalOpen, bigFiveModalOpen...
      ├── Effects: useEffect para carregar opinions, analyses, messages
      ├── Handlers: sendLiaMessage, generateNewOpinion, handleAnalyzeWithLia
      ├── Formatters: formatAnalysisDate, formatCurrency, generateShortId
      └── Return: 40+ states + handlers exportados
```

### F.3 Diferencas Arquiteturais

| Aspecto | Vue | React | Impacto |
|---|---|---|---|
| **Centralizacao** | Estado distribuido entre 10+ componentes | Estado centralizado em `useCandidatePreviewCore` | Vue mais modular mas fragmentado |
| **Data fetching** | Cada card faz `$axios.get()` no `onMounted` | Hook centralizado faz todos os fetches | Vue: N+1 requests; React: batch |
| **Opinoes/Pareceres** | Nao implementado | Fetch completo com historico | **Gap critico** |
| **Chat LIA** | Nao implementado | Gerenciado no core hook | **Gap critico** |
| **Error handling** | `toast.error()` por componente | Centralizado no hook | Vue inconsistente |

### F.4 Endpoints Vue (observados no codigo real)

| Endpoint | Componente | Uso |
|---|---|---|
| `GET /users/data_files` | files/wrapper.vue | Buscar arquivos |
| `GET /users/experiences` | cards/experiences.vue | Buscar experiencias |
| `GET /users/educations` | cards/educations.vue | Buscar formacoes |
| `GET /users/skill_relationships` | cards/skills.vue | Buscar skills |
| `GET /users/addresses/Candidate/{id}` | cards/addresses.vue | Buscar enderecos |
| `GET /users/candidates/{id}/calculate_remunerations` | cards/remunerations.vue | Calcular remuneracao |
| `GET /users/candidates/{id}/calculate_benefits` | cards/remunerations.vue | Calcular beneficios |

### F.5 Endpoints React (observados no codigo real)

**NOTA:** O React usa `/api/backend-proxy/...` como proxy para o backend FastAPI.

| Endpoint | Componente | Uso |
|---|---|---|
| `GET /api/backend-proxy/opinions/candidate/{id}/summary` | useCandidatePreviewCore | Resumo pareceres |
| `POST /api/backend-proxy/opinions/generate` | useCandidatePreviewCore | Gerar novo parecer |
| `GET /api/backend-proxy/opinions/candidate/{id}/history` | useCandidatePreviewCore | Historico pareceres |
| `GET /api/backend-proxy/analyses/candidate/{id}` | useCandidatePreviewCore | Analises salvas |
| `DELETE /api/backend-proxy/analyses/{aid}` | useCandidatePreviewCore | Deletar analise |
| `POST /api/backend-proxy/lia/chat` | useCandidatePreviewCore | Chat com LIA |
| `GET {BACKEND_URL}/api/v1/candidates/{id}/files` | useCandidateFiles | Buscar arquivos |
| `POST {BACKEND_URL}/api/v1/candidates/{id}/files` | useCandidateFiles | Upload arquivo |
| `DELETE {BACKEND_URL}/api/v1/candidates/{id}/files/{fid}` | useCandidateFiles | Deletar arquivo |

**IMPORTANTE:** Tab Atividades React usa **dados demo** via `getDemoActivities()`. O Vue `applies.vue` usa dados **reais** de candidaturas.

### F.6 Endpoints Ausentes no Backend Vue

| Endpoint Necessario | Prioridade | Descricao |
|---|---|---|
| `GET /opinions/history` | **Critico** | Historico de pareceres LIA |
| `POST /opinions/generate` | **Critico** | Gerar novo parecer |
| `POST /lia/chat` | **Critico** | Chat conversacional com LIA |
| `GET /activities` (timeline) | **Alto** | Timeline de atividades |
| `DELETE /files/{id}` | **Medio** | Deletar arquivo |
| `GET /analyses` | **Alto** | Analises salvas por vaga |

### F.7 Design Tokens — Sistema de Cores

| Token React | Uso | Equivalente Vue |
|---|---|---|
| `--lia-bg-primary` | Fundo principal | `rgb(var(--v-theme-surface))` |
| `--lia-bg-secondary` | Fundo secundario | `rgb(var(--v-theme-background))` |
| `--lia-bg-tertiary` | Fundo terciario | `bg-border-color` (nao ideal) |
| `--lia-text-primary` | Texto principal | `text-on-surface` |
| `--lia-text-secondary` | Texto secundario | `text-body-medium` |
| `--lia-text-tertiary` | Texto terciario | `text-body-light` |
| `--lia-border-subtle` | Borda sutil | `border-border-color border-opacity-100` |
| `--wedo-cyan` | Cor LIA | `wedo-cyan` (custom) |
| `--wedo-purple` | Cor brand | `primary` |

### F.8 Tipografia

| Classe React | Tamanho | Classe Vue Equivalente |
|---|---|---|
| `text-micro` | 9px | `f9` |
| `text-xs` | 10px | `f10` |
| `textStyles.body` | 11px | `f11` |
| `textStyles.label` | 12px | `f12` |
| `text-sm` | 14px | `f13` / `f14` |

### F.9 Espacamento

| Padrao React | Valor | Padrao Vue | Delta |
|---|---|---|---|
| `p-2.5` | 10px | `pa-3` (12px) | Vue **2px maior** |
| `gap-1.5` | 6px | `ga-2` (8px) | Vue **2px maior** |
| `rounded-md` | 6px | `rounded-lg` (8px) | Vue **2px maior** |

**Conclusao:** O Vue usa espacamento sistematicamente ~20% maior, resultando em menor densidade de informacao.

### F.10 Icones — Mapeamento

| Funcao | React (lucide-react) | Vue (mdi + lucide custom) | Status |
|---|---|---|---|
| Brain/LIA | `Brain` | `lucide-brain` | OK |
| Score | SVG inline | `v-progress-circular` | Diferente impl |
| Check | `CheckCircle` | `mdi-check` (MDI) | Biblioteca diferente |
| LinkedIn | `Linkedin` | `lucide-linkedin` | OK |
| GitHub | `Code` | Nao existe no preview | **Ausente** |
| Upload | `Upload` | Nao existe | **Ausente** |
| Eye/Preview | `Eye` | Nao existe | **Ausente** |
| Trash/Delete | `Trash2` | Nao existe | **Ausente** |
| Calendar | `Calendar` | Nao existe no preview | **Ausente** |
| Clock | `Clock` | Nao existe no preview | **Ausente** |

**Nota:** O Vue usa componente `Icon` customizado que suporta `lucide-*` e `mdi-*`. Para consistencia visual, migrar para Lucide em novos componentes.

---

## Apendice G — Features Exclusivas e Plano de Convergencia

### G.1 Features que SO EXISTEM NO VUE

| Feature | Componente | Descricao |
|---|---|---|
| **Enriquecimento** | `preview.vue` dialog | Enriquecer perfil com creditos (email, telefone) |
| **Busca IA** | `preview.vue` dialog | Gerar perfil IA para candidatos sem origem IA |
| **Remuneracao detalhada** | `remunerations.vue` (191 linhas) | Calculo completo: salario base, anualizado 13.33x, componentes variaveis, beneficios, subtotais, total anual |
| **Score Analysis separado** | `score_analysis.vue` (692 linhas) | Analise de score detalhada com requisitos, confianca, metodo de scoring |
| **Curriculo como tab** | `curriculum_text.vue` (513 linhas) | Tab dedicada para texto do curriculo |
| **Sourced Profile** | `sourced-profile-*.vue` (9 arquivos) | Preview especifico para candidatos de sourcing LIA |
| **Candidatos similares** | `similar_candidates_modal.vue` | Modal de candidatos similares |

### G.2 Features que SO EXISTEM NO REACT

| Feature | Componente | Descricao |
|---|---|---|
| **LIA Chat** | `LiaChatModal.tsx` | Chat conversacional com IA sobre o candidato |
| **Tab Pareceres** | `CandidateOpinionsTab.tsx` (293 linhas) | Historico de pareceres + analises salvas |
| **Timeline Atividades** | `ActivityTimeline.tsx` + `ActivityExpandedDetails.tsx` | Timeline visual com 15+ tipos expandiveis |
| **Filtros Atividades** | `ActivityFilters.tsx` | Filtros por tipo + periodo + modo |
| **File Preview Modal** | `FilePreviewModal.tsx` | Preview inline de PDFs, imagens, videos |
| **Drag & Drop Upload** | `CandidateFilesTab.tsx` | Area drag-drop com progress bar |
| **Categorias Arquivo** | `useCandidateFiles.tsx` | Categorizacao automatica de arquivos |
| **DISC Modal** | `disc-assessment-modal.tsx` | Resultado DISC com grafico radar |
| **Big Five Modal** | `big-five-modal.tsx` | Resultado Big Five com visualizacao |
| **Screening Media** | `screening-media-modal.tsx` | Player audio/video com transcricao |
| **Navegacao candidatos** | `candidate-preview.tsx` | Setas prev/next com `1 de 42` |
| **ExperienceHighlight** | `experience-highlight-card.tsx` | Card destaque de experiencia |
| **ID alfanumerico** | `generateShortId()` | `A72E80` em vez de `4681` |
| **Favoritar** | `candidate-preview.tsx` | Toggle favorito com coracao |

### G.3 Plano de Convergencia — Prioridades

#### Sprint 1 — Critico (1-2 semanas)

| # | Item | Esforco | Descricao |
|---|---|---|---|
| 1 | Tab Pareceres | 3 dias | Criar `CandidateOpinionsTab.vue` com historico + subtabs |
| 2 | LIA Chat Modal | 3 dias | Criar `LiaChatModal.vue` com chat conversacional |
| 3 | Corrigir header | 2 dias | Adicionar datas, redes sociais, badges, ID formatado |
| 4 | Corrigir Atividades | 2 dias | Cards expandiveis, formatar JSON, altura maxima |

#### Sprint 2 — Alto (2-3 semanas)

| # | Item | Esforco | Descricao |
|---|---|---|---|
| 5 | File Preview Modal | 3 dias | Criar modal de preview inline |
| 6 | Drag & Drop Upload | 2 dias | Adicionar ao wrapper.vue |
| 7 | Activity Timeline | 3 dias | Criar timeline visual com filtros |
| 8 | Botoes de Acao | 2 dias | Adicionar labels, WhatsApp, Triagem WSI |

#### Sprint 3 — Medio (2-3 semanas)

| # | Item | Esforco | Descricao |
|---|---|---|---|
| 9 | Skills categorizadas | 2 dias | Agrupar por Backend/Frontend/Data/etc |
| 10 | Design tokens | 3 dias | Implementar tipografia DS v4.2.1 |
| 11 | DISC/BigFive modais | 3 dias | Visualizacoes de assessment |
| 12 | Screening Media | 2 dias | Player com transcricao |

#### Sprint 4 — Backport React (1-2 semanas)

| # | Item | Esforco | Descricao |
|---|---|---|---|
| 13 | Remuneracao detalhada | 2 dias | Adaptar logica Vue 13.33x para React |
| 14 | Score Analysis rico | 3 dias | Adaptar requisitos expandiveis para React |
| 15 | Enriquecimento | 1 dia | Implementar dialog com creditos no React |

### G.4 Metricas Comparativas Finais

| Metrica | Vue (Producao) | React (Replit) |
|---|---|---|
| Tabs implementadas | 3 | 4 |
| Modais | 3 | 7+ |
| Botoes de acao | 8 (icones) | 9 (com labels) |
| Filtros atividade | 8 (truncados) | 8 (todos visiveis) |
| Sub-componentes atividades | 0 | 3 |
| Cards perfil | 9 | 9 |
| Linhas totais preview | ~6.345 | ~6.196 |
| Features exclusivas | 7 | 14 |
| Endpoints consumidos | 7 | 9 |
| Design tokens semanticos | Parcial | Completo |
| Dark mode | Nao | Preparado |
| Data fetching | N+1 (por card) | Batch (centralizado) |

**Conclusao geral:** O React tem mais features implementadas (14 vs 7 exclusivas), melhor UX em atividades/arquivos/pareceres, e estado centralizado. O Vue tem cards de dados superiores (remuneracao 13.33x, score analysis 692 linhas) e features de enriquecimento. A convergencia deve priorizar trazer as features React para o Vue (Tab Pareceres, LIA Chat, Timeline) enquanto preserva as superiores do Vue (remuneracao, score analysis, enriquecimento).
