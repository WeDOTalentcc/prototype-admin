# Auditoria QA — Candidate Preview Panel
## Producao WeDOTalent (app.wedotalent.cc) vs Referencia Replit

**Data:** 2026-04-03
**Objetivo:** Identificar todos os problemas do **produto WeDOTalent em producao** que precisam ser corrigidos para atingir a qualidade da **implementacao de referencia no Replit**.
**Convencao:** Cada item marca claramente:
- **[PROD]** = problema encontrado na producao WeDOTalent (precisa corrigir)
- **[REF]** = como esta no Replit (o design correto/desejado)

**Ambientes:**
- **Producao:** app.wedotalent.cc (Vue 3 / Vuetify 3 / Nuxt 3)
- **Referencia Replit:** plataforma-lia (React / Tailwind / Next.js + FastAPI)

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

### B.3 Mapeamento React (Replit) ↔ Vue (Producao Estimado)

**Nota:** O codebase Vue da producao (repositorios `ats_front`/`wedo-nuxt`) nao esta disponivel neste ambiente Replit. O mapeamento abaixo e estimado com base nos screenshots de producao e convencoes padrao Vue/Vuetify/Nuxt.

| Componente React (Replit) | Arquivo Replit | Componente Vue Estimado (Producao) | Base da Estimativa |
|---|---|---|---|
| `CandidatePreview` | `candidate-preview.tsx` (858 linhas) | `CandidatePreviewDrawer.vue` ou `CandidateDetailPanel.vue` | Screenshots mostram drawer lateral |
| `CandidatePreviewProfileTab` | `CandidatePreviewProfileTab.tsx` (861 linhas) | `CandidateProfileTab.vue` | Tab "Perfil Completo" visivel em P1-P3 |
| `CandidateActivitiesTab` | `CandidateActivitiesTab.tsx` (277 linhas) | `CandidateActivitiesTab.vue` ou `ActivityTimeline.vue` | Tab "Atividades" visivel em P4-P7 |
| `CandidateFilesTab` | `CandidateFilesTab.tsx` (774 linhas) | `CandidateFilesTab.vue` | Tab "Arquivos" confirmada via Playwright |
| `CandidateOpinionsTab` | `CandidateOpinionsTab.tsx` (292 linhas) | `CandidateOpinionsTab.vue` ou `ParecerTab.vue` | Tab "Pareceres" confirmada via screenshots |
| `OpinionCard` | `OpinionCard.tsx` (305 linhas) | Inline no componente Vue ou `OpinionCard.vue` | Producao exibe Parecer LIA como card |
| `ActivityFilters` | `ActivityFilters.tsx` (131 linhas) | Inline ou `ActivityFilters.vue` | Filtros visiveis em P4, P7 |
| `ActivityExpandedDetails` | `ActivityExpandedDetails.tsx` (878 linhas) | Inline ou nao implementado | Cards NAO expandem em producao (D29) |
| `LiaChatModal` | `LiaChatModal.tsx` (315 linhas) | Nao identificado em producao | Funcionalidade ausente (D57) |
| `FilePreviewModal` | `FilePreviewModal.tsx` (546 linhas) | Nao identificado em producao | Funcionalidade ausente (D42) |
| `useCandidatePreviewCore` | `useCandidatePreviewCore.tsx` (666 linhas) | Composable Vuex/Pinia | Logica de negocio |
| `useCandidateFiles` | `useCandidateFiles.tsx` (201 linhas) | Composable Vuex/Pinia | Logica de arquivos |

**Para mapeamento exato**, acesso aos repositorios `ats_front` ou `wedo-nuxt` e necessario.

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
