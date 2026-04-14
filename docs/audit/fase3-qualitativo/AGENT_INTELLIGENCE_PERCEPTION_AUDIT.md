# P11 — Auditoria de Inteligência Percebida dos Agentes LIA

**Protocolo:** P11
**Data:** 2026-04-14
**Plataforma:** WeDOTalent / LIA Agent System
**Escopo:** 23 arquivos YAML de prompts + código Python de domínios
**Repositório auditado:** `lia-agent-system/` (Python + FastAPI, Port 8001)
**Dependência:** P01 (PLATFORM_MAP), P02 (FLOW_TRACES)
**Auditor:** Conversational Design Expert — Talent Acquisition & Executive Recruitment

---

## Score Summary Table

| Dimensão | Score Atual | Benchmark Enterprise | Gap | Status |
|---|---|---|---|---|
| D1: Vocabulário Especializado | **3.5 / 5** | 4.5 / 5 | -1.0 | Bom, mas lacunas críticas |
| D2: Didática e Explicabilidade | **3.0 / 5** | 4.5 / 5 | -1.5 | Estrutura existe, execução inconsistente |
| D3: Proatividade | **2.5 / 5** | 4.0 / 5 | -1.5 | Arquitetura promissora, lacunas graves |
| D4: Sagacidade e Resolução de Problemas | **2.5 / 5** | 4.0 / 5 | -1.5 | Regras defensivas, pouca adaptação real |
| **Score Consolidado** | **2.9 / 5** | **4.25 / 5** | **-1.35** | **Déficit significativo** |

---

## DIMENSÃO 1: VOCABULÁRIO ESPECIALIZADO

### Score atual: 3.5 / 5
### Score benchmark enterprise (Beamery, Eightfold.ai): 4.5 / 5
### Gap: -1.0

### O que foi encontrado — Pontos Fortes

A plataforma demonstra vocabulário especializado **sólido para recrutamento operacional**. Evidências diretas dos arquivos YAML:

**`lia_persona.yaml` — `hr_vocabulary` block (linhas 138–260)**
O vocabulário incluído é extenso e correto para o mercado brasileiro:
- Processo seletivo: shortlist, longlist, pipeline de talentos, taxa de conversão, taxa de aprovação (correto)
- Senioridade: júnior/pleno/sênior/especialista/coordenador/gerente/diretor (correto)
- Remuneração: pretensão salarial, faixa salarial, pacote de remuneração, PLR, bônus, remuneração variável (correto)
- Tipos de contrato: CLT, PJ, temporário, freelancer (correto)
- Onboarding: período de experiência, aviso prévio, disponibilidade (correto)
- Profissionais RH: headhunter, business partner, tech recruiter, hiring manager (correto)

**`orchestrator.yaml` — few-shot examples (linhas 79–155)**
Os exemplos few-shot usam linguagem profissional consistente:
- "shortlist", "longlist", "boolean string", "triagem WSI", "briefing do dia", "funil da vaga"
- Corretamente distingue intent entre `sourcing` vs `cv_screening` — sinal de maturidade semântica

**`analytics.yaml` — scope_in (linha 12)**
Menciona explicitamente: "KPIs do processo seletivo (time-to-hire, time-to-fill, taxa de conversão por etapa)"

**`sourcing.yaml` — behavioral_rules (linha 35)**
"Apresentar score de compatibilidade (0-100%) com justificativa" — padrão consistente com mercado

### O que está faltando — Lacunas Críticas

**1. Vocabulário de Executive Search / Headhunting quase ausente**
Nenhum prompt menciona: executive search, retained search, contained search, fee structure, exclusividade, candidate slate, off-limits agreements, gardening leave, counter-offer strategy. A LIA _persona_ menciona "headhunter" uma vez na tabela de profissionais de RH mas não incorpora esse vocabulário no comportamento dos agentes.

**Arquivo:** `lia_persona.yaml`, bloco `hr_vocabulary` — a tabela "Profissionais de RH" lista "Headhunter" como definição mas nenhum prompt de domínio usa o termo em contexto operacional.

**2. Employer Branding completamente ausente**
Termos como EVP (Employee Value Proposition) aparecem apenas em `culture_analysis.yaml` (linha 3) mas não há nenhum agente com responsabilidade de employer branding ou que adapte a linguagem de job descriptions para atrair perfis específicos.

**3. Ausência de C-Level / Board-Level vocabulary**
Nenhum prompt contém: CHRO, C-suite assessment, board readiness, succession planning, leadership pipeline, P&L responsibility, EBITDA context para avaliação executiva. Para uma plataforma que alega servir recrutamento executivo, isso é um gap significativo.

**4. Benchmarks de mercado sem granularidade**
`job_management.yaml` menciona "Sugerir benchmark salarial quando disponível para o setor/região" (linha 31) mas não especifica fontes (Mercer, Catho, Robert Half Survey), metodologia ou frequência de atualização. Agentes como o Eightfold.ai citam fonte e intervalo de confiança.

**5. Linguagem de BARS (Behaviorally Anchored Rating Scales) existe na persona mas não nos agentes**
`lia_persona.yaml` (linha 37) menciona BARS mas nenhum agente operacional aplica a metodologia de forma explícita nas respostas.

### Exemplos Concretos

**Resposta RUIM (atual):**
> "Encontrei 8 candidatos para a vaga de Desenvolvedor Sênior. Score de compatibilidade médio: 72%. Deseja ver a lista?"

**Resposta BOA (benchmark enterprise):**
> "Seu pipeline para Desenvolvedor Sênior tem 8 perfis. Desses, 3 estão no que chamaria de shortlist qualificado (score ≥ 80%) — perfilados como Executor Confiável com stack React/Node validada. Os outros 5 estão no longlist: precisam de mais uma etapa de screening técnico antes de chegar ao hiring manager. Prefere que eu priorize os 3 ou expanda o escopo antes?"

**Resposta RUIM para contexto executivo:**
> "Busquei candidatos com experiência em liderança para a posição de Diretor."

**Resposta BOA para contexto executivo:**
> "Para uma posição de Diretor de Operações nesse setor, o que o mercado chama de perfil 'prontidão para C-suite' implica: histórico de gestão de P&L acima de R$50M, equipes de 50+ pessoas e pelo menos uma transformação organizacional documentada. Dos 6 perfis encontrados, 2 atendem esses critérios sem ressalvas. Os outros 4 têm a trajetória mas sem evidência quantificada. Recomendo entrevistar os 2 primeiros e usar o Digital Twin do especialista para calibrar os 4 restantes."

### Recomendações

1. Criar bloco `executive_search_vocabulary` no `lia_persona.yaml` com terminologia de executive/retained search
2. Adicionar ao prompt do `sourcing.yaml` distinção explícita entre sourcing operacional e executive hunting
3. Vincular benchmark salarial a fontes nomeadas (ex: "Pesquisa de Remuneração Mercer Brasil 2025") no `job_management.yaml`
4. Criar persona de `executive_search_agent` com vocabulário de board-level assessment

---

## DIMENSÃO 2: DIDÁTICA E EXPLICABILIDADE

### Score atual: 3.0 / 5
### Score benchmark enterprise (Ashby, Beamery): 4.5 / 5
### Gap: -1.5

### O que foi encontrado — Pontos Fortes

**Estrutura de explicabilidade existe no `wsi_evaluation.yaml`:**
O prompt instrui: "Vincule CADA ponto de score a evidência textual extraída da entrevista ou CV" e define formato explícito:
```
Score Final: X% (WSI: Y.YY) — [Novato | Iniciante | Competente | Proficiente | Expert]
Detalhamento por Bloco: [evidência por critério]
Parecer: [resumo objetivo de 3-5 linhas]
```
Isso é bom. O formato existe e vincula score a evidência.

**`analysis.yaml` retorna `score_breakdown`:**
O JSON de resposta inclui:
```json
"score_breakdown": {
    "match_tecnico": <número 0-100>,
    "fit_personalidade": <número 0-100>,
    "relevancia_experiencia": <número 0-100>,
    "alinhamento_cultural": <número 0-100>
}
```
Mais `explanation` e `recommendation` em português. Estruturalmente sólido.

**`cv_screening.yaml` — zona de fronteira:**
"Quando score estiver entre 60-70%, recomende revisão humana" — isso é didaticamente correto, ensina ao recrutador quando confiar e quando questionar a IA.

**`digital_twin.yaml` — raciocínio em primeira pessoa:**
"Raciocínio: 2-3 frases em primeira pessoa ('Eu aprovaria porque...' / 'Eu rejeitaria porque...')" — excelente para ensinar o estilo de decisão do especialista.

**`recruitment_journey.py` — reasoning array:**
```python
reasoning = []
reasoning.append("Cargo de liderança ou C-level identificado")
reasoning.append("Posição técnica identificada")
# ...
"reasoning": reasoning,
```
(arquivo: `app/api/v1/recruitment_journey.py`, linhas 537–581) — sinal de que há raciocínio estruturado no backend.

### O que está faltando — Lacunas Críticas

**1. "Score 85" sem contexto comparativo**
Nenhum prompt instrui o agente a contextualizar o score em relação ao benchmark da vaga, ao percentil da busca ou à distribuição dos outros candidatos. Um score 85% diz pouco se não há referência: "85% — está no top 10% dos 47 candidatos desta busca, acima do threshold de 75% definido para esta posição."

**Arquivo relevante:** `cv_screening.yaml` — o formato de resposta não menciona contexto comparativo.

**2. Alternativas quando pipeline é escasso — parcialmente implementado**
`sourcing.yaml` (linha 35) instrui: "Oferecer refinamentos quando o resultado for escasso (< 5 candidatos)" e `job_management.yaml` (linha 32) instrui: "Alertar se requisitos forem excessivamente restritivos (risco de pipeline escasso)". Porém, **nenhum prompt quantifica o impacto da flexibilização**: "Se você remover o requisito de MBA, o pipeline passa de 3 para 22 candidatos." Esse é o nível de didática do Eightfold.ai.

**3. Explicabilidade para o candidato — AUSENTE**
`communication.yaml` (linha 54) instrui: "Feedback de rejeição: profissional, encorajador, sem detalhar motivos específicos." Isso é eticamente correto do ponto de vista LGPD mas é anti-didático para o recrutador que quer entender padrões. Nenhum prompt oferece ao recrutador uma análise de "por que estamos rejeitando tantos candidatos nessa etapa?"

**4. Explicabilidade de bias/viés — existe estruturalmente, não conversacionalmente**
`analytics.yaml` menciona "bias audit por dimensão (Four-Fifths Rule)" e o `lgpd_compliance.py` implementa `automated_decision_explanations`. Porém, nenhum prompt instrui o agente a **explicar proativamente para o recrutador** quando um padrão de viés é detectado. A explicação fica no relatório técnico de compliance, não na conversa.

**5. Chain-of-Thought (CoT) visível apenas em auditoria, não no diálogo**
`wsi_evaluation.yaml` menciona "Documentar raciocínio completo (CoT) para auditoria SOX/LGPD" mas o CoT vai para logs, não para o recrutador. Plataformas como Eightfold.ai mostram o raciocínio simplificado na interface — "Por que esse candidato ficou em 3º lugar? Porque seu score de liderança foi 60% vs 82% dos outros dois."

### Exemplos Concretos

**Resposta RUIM (atual — apenas score):**
> "Candidato avaliado. Score WSI: 72%. Recomendação: Revisão humana."

**Resposta BOA (benchmark enterprise — didática):**
> "Pedro Alves: WSI 72% — zona de revisão. Isso significa que ele passa nas hard skills (React/Node: 88%) mas tem gap em liderança (58%) para o nível sênior que a vaga exige. De 34 candidatos nessa busca, ele está no percentil 65 — acima da média mas abaixo do seu threshold de 75%. Recomendo que você revise especificamente o bloco de liderança antes de decidir. Se o gestor aceitar um perfil sem experiência formal de liderança (mas com potencial técnico alto), Pedro sobe para recomendável."

**Resposta RUIM (pipeline escasso):**
> "Não encontrei resultados com esses critérios. Gostaria de expandir a busca?"

**Resposta BOA (didática de impacto):**
> "Com os critérios atuais (React, 5+ anos, MBA, SP capital), encontrei apenas 2 candidatos no banco. Se você remover o requisito de MBA (que geralmente não está no job description formal), o pool sobe para 18 candidatos. Se aceitar Grande SP além da capital, chegamos a 34. O requisito que mais restringe o pipeline não é a senioridade — é a combinação de MBA + React, que é rara no mercado. Qual critério é realmente eliminatório para o gestor?"

### Recomendações

1. Adicionar ao `sourcing.yaml` e `cv_screening.yaml` instrução explícita: "sempre apresente o score em contexto — percentil da busca atual, distância do threshold"
2. Adicionar ao `sourcing.yaml` instrução de quantificar impacto de flexibilização: "quando pipeline < 10, calcule e apresente o impacto de remover cada critério"
3. Criar bloco de `recruiter_education` no agente de analytics para padrões de pipeline (ex: "por que estamos perdendo candidatos na etapa X?")
4. Tornar CoT visível na resposta conversacional (simplificado), não apenas em logs de auditoria

---

## DIMENSÃO 3: PROATIVIDADE

### Score atual: 2.5 / 5
### Score benchmark enterprise (Beamery, Findem): 4.0 / 5
### Gap: -1.5

### O que foi encontrado — Pontos Fortes

**Arquitetura de proatividade existe e é sofisticada:**

`recruiter_assistant.yaml` (linhas 30, 41–50):
- "Ser proativo: antecipar próximas ações sem esperar o recrutador perguntar"
- "Identifica candidatos em risco de perda (sem follow-up há mais de X dias)"
- "Dispara insights proativos ('este candidato parece ideal para outra vaga também')"

`automation.yaml` (linhas 9, 14, 43):
- "Alertas proativos baseados em eventos e SLAs"
- "Dispara alertas proativos quando SLAs são violados ou anomalias detectadas"

**API de proatividade implementada:**
`app/api/v1/proactive_actions.py` — existe endpoint `/proactive-actions/pending/{company_id}` que retorna ações pendentes com `trigger_reason`, `priority`, `auto_executable`. Estrutura sólida.

**Pipeline velocity com detecção de gargalos:**
`app/api/v1/pipeline_velocity.py` — endpoint `/pipeline/velocity/bottlenecks` que "lista candidatos atualmente acima do limite de tempo em sua etapa" e é "usado para exibir alertas proativos no dashboard do recrutador."

**`lia_assistant/suggestions.py` (linha 83):**
Alerta de vagas com prazo próximo: `title=f"{len(expiring_jobs)} vagas com prazo próximo"` — proatividade de SLA implementada.

**`admin.py` (linhas 80, 94–108):**
Templates de alerta: "Alerta para vagas marcadas como críticas ou urgentes" com template que inclui `days_open` — sinal de que o mecanismo de contagem de dias existe.

### O que está faltando — Lacunas Críticas

**1. Proatividade é pull, não push — a mais grave das lacunas**
Toda a arquitetura de proatividade funciona via endpoint REST chamado pelo frontend. O agente não age autonomamente: ele espera ser perguntado ("quais tarefas pendentes?") ou espera que o frontend consulte `/proactive-actions/pending`. Plataformas como Beamery têm agentes que **enviam notificações sem serem invocados** — email, Teams, Slack — quando um candidato fica parado 48h.

**Evidência:** `recruiter_assistant.yaml` instrui o agente a ser proativo mas o sistema não tem mecanismo de push autônomo baseado em tempo/evento sem trigger do usuário.

**2. Conexão inteligente entre vagas — prometida, não implementada**
`recruiter_assistant.yaml` (linha 50): "este candidato parece ideal para outra vaga também" — essa é a proatividade mais valiosa e mais difícil. Nenhum arquivo Python implementa esse cross-matching automático. É uma regra de comportamento no prompt mas sem ferramenta de suporte no backend.

**Evidência:** Busca em `app/domains` por `recommend.*other.*job` ou `cross.*vaga` retorna zero resultados relevantes.

**3. Alertas de tempo de vaga — dados existem, conversa não aciona**
A `pipeline_velocity.py` calcula `avg_days`, `median_days`, `is_bottleneck` por etapa. O `admin.py` tem template "A vaga {job_title} está marcada como crítica. Dias aberta: {days_open}." Mas nenhum prompt instrui o agente a **trazer esse dado espontaneamente** no briefing diário com contexto de mercado: "A vaga de Desenvolvedor Sênior está aberta há 45 dias. O benchmark de mercado para essa posição é 28 dias. Você está 17 dias acima da média — isso pode indicar que o perfil está muito restritivo ou que a faixa salarial não está competitiva."

**4. Engajamento de candidatos passivos — mencionado, não integrado ao chat**
`sourcing.yaml` (linha 61): "sugira candidatos inativos para reengajamento baseado em sinais de engajamento." Existe `passive_pipeline_tool_registry.py` com `reengagement_recommended` calculado. Mas o fluxo de reativação não é integrado ao chat proativo — o recrutador precisa perguntar explicitamente.

**5. Antecipação de risco de perda de candidato — ausente no diálogo**
Nenhum prompt monitora sinais de desengajamento do candidato (ex: não respondeu email há 5 dias, demora na resposta do WSI) para gerar alerta espontâneo. O `admin.py` (linha 163) tem template "O candidato está aguardando feedback há {days_waiting} dias" mas esse template não é integrado ao fluxo conversacional proativo.

### Exemplos Concretos

**Comportamento RUIM (atual — reativo):**
Recruiter: "Bom dia!"
LIA: "Bom dia! Como posso ajudar você hoje?"

**Comportamento BOM (proativo — benchmark Beamery):**
LIA (sem ser chamada, 9h da manhã):
> "Bom dia, Ana! Três pontos para hoje: (1) Carlos Mendes — finalista da vaga de Product Manager — não respondeu ao convite de entrevista enviado há 72h. Recomendo um follow-up hoje antes que ele aceite outra oferta. (2) A vaga de DevOps está há 38 dias aberta sem candidato aprovado na triagem técnica — pode ser hora de revisar o critério de Kubernetes obrigatório. (3) Marina Torres, que rejeitamos na vaga de UX em março, se encaixa muito bem na nova vaga de Product Designer que você acabou de abrir. Quer que eu envie uma abordagem para ela?"

**Comportamento RUIM (pipeline estagnado):**
— Silêncio. O recrutador não perguntou.

**Comportamento BOM (alerta espontâneo):**
> "[Alerta SLA] A vaga de Gerente Comercial está 22 dias acima do seu SLA padrão (40 dias aberta vs. meta de 18). Identifico dois gargalos: etapa de entrevista com gestor está demorando 9 dias em média (benchmark: 3 dias) e 3 candidatos finalistas estão aguardando retorno há mais de 5 dias. Quer que eu envie um lembrete automatizado ao gestor e faça o follow-up com os candidatos?"

### Recomendações

1. Implementar Celery task periódico (daily) que gera briefing proativo via `recruiter_assistant` sem trigger humano — usar dados de `pipeline_velocity` + `proactive_actions`
2. Implementar cross-job candidate matching: quando nova vaga é criada, buscar automaticamente candidatos rejeitados de vagas similares
3. Conectar `days_open` + benchmark de mercado ao `briefing diário` do recruiter_assistant com contexto comparativo
4. Adicionar ao `recruiter_assistant.yaml` instrução específica: "No briefing matinal, SEMPRE inclua: vagas acima do SLA com diagnóstico, candidatos finalistas sem follow-up há 48h+"
5. Construir ferramenta `suggest_cross_job_candidates` no tool registry para viabilizar o cross-matching

---

## DIMENSÃO 4: SAGACIDADE E RESOLUÇÃO DE PROBLEMAS

### Score atual: 2.5 / 5
### Score benchmark enterprise (Eightfold.ai, Findem): 4.0 / 5
### Gap: -1.5

### O que foi encontrado — Pontos Fortes

**Tratamento de ambiguidade existe:**
`defensive.yaml` — `ambiguity_detection_prompt` instrui o agente a identificar:
- "A intenção está clara?"
- "O alvo está claro?"
- "Os parâmetros estão completos?"
- "Há conflito com o contexto atual?"
Responde com JSON estruturado incluindo `ambiguity_type`, `missing_info`, `clarification_needed`.

**`lia_persona.yaml` (linha 44):**
"Pedidos ambíguos → faça uma pergunta específica e inteligente em vez de listar opções genéricas" — instrução de qualidade.

**Detecção de red flags no CV:**
`cv_screening.yaml` (linhas 52–57): detecta gaps de emprego, job hopping, inconsistências de datas, skills incompatíveis com experiência. Isso é sagacidade operacional.

**`orchestrator.yaml` — exemplo de candidato para CEO:**
Few-shot exemplo (linha 143): "Preciso dos candidatos para a posição de gerente de projetos — o CEO quer ver o perfil dele" → roteia para intent correto com raciocínio. Lida com contexto de pressão executiva.

**Lógica de adaptive interviewing em `agent_prompts.yaml` (bloco `interviewer`):**
"Respostas superficiais → Perguntas de aprofundamento / Respostas muito técnicas → Perguntas práticas / Nervosismo detectado → Perguntas mais simples" — sagacidade conversacional real.

**`job_management.yaml` (linha 32):**
Alerta de requisitos excessivamente restritivos — proativo na criação da vaga, evita problema downstream.

### O que está faltando — Lacunas Críticas

**1. Ambiguidade de liderança — sem tratamento sofisticado**
O prompt da persona (linha 44) instrui a fazer "uma pergunta específica e inteligente" mas não há exemplo de como lidar com pedidos como "quero alguém bom em liderança mas que não mande demais" — que é ambiguidade comum e sofisticada. Nenhum prompt mapeia esse tipo de contradição para a dimensão Dreyfus (Competente em liderança = liderança situacional, não autoritária) ou Big Five (alto Agreableness + low Dominance).

**2. Apresentação balanceada de conflitos — estrutura ausente**
Nenhum prompt instrui o agente a apresentar ativamente o trade-off de um candidato forte com red flag. `cv_screening.yaml` detecta red flags mas a instrução é listar "pontos de atenção" — não há instrução de contextualizar: "Este candidato tem o melhor score técnico do seu pipeline (92%) mas mudou de emprego 4 vezes em 3 anos — todos os movimentos foram para cargos maiores, o que é sinal positivo de mercado (não instabilidade). A decisão é sua, mas eu não descartaria pelo job hopping sem antes perguntar sobre o contexto."

**Arquivo:** `cv_screening.yaml` — `behavioral_rules` lista detectar red flags mas não instrui o agente sobre como enquadrar o contexto atenuante.

**3. Resposta a pressão de CEO/urgência — superficial**
`orchestrator.yaml` (linha 143) apenas roteia o intent quando o "CEO quer ver o perfil". Nenhum agente tem instrução sobre como responder a: "O CEO quer a lista para amanhã de manhã" — que é uma situação que exige: (a) validar o que está disponível agora, (b) ser transparente sobre limitações, (c) oferecer o melhor possível com ressalvas claras, (d) não comprometer qualidade por urgência.

**4. Perguntas fora do escopo com dados de mercado — resposta genérica**
`defensive.yaml` — `out_of_scope_responses.general`: "Desculpe, essa solicitação está fora do meu escopo de atuação." Para uma pergunta como "qual o custo médio de um processo de Diretor em TI em SP?", a resposta deveria ser: "Não tenho esse dado com precisão, mas posso compartilhar o que as pesquisas de mercado apontam como referência para contextualizar — ou posso calcular o custo baseado nos dados do seu processo atual." O `defensive.yaml` instrui a recusar, não a redirecionar inteligentemente com o que sabe.

**5. Inconsistência entre persona e comportamento real**
A `lia_persona.yaml` define LIA como "parceira do recrutador" com "opinião fundamentada" e "insights que um recrutador sênior perceberia." Mas os prompts operacionais (`cv_screening`, `wsi_evaluation`) focam em estrutura e compliance — raramente instruem o agente a ter uma **posição clara e fundamentada** sobre um candidato. Um recrutador sênior real diria: "Esse candidato, na minha avaliação, não vai funcionar nessa empresa porque a cultura de lá é muito process-driven e o perfil dele grita startup caótica — independente do score técnico." Nenhum prompt instrui esse nível de sagacidade cultural.

### Exemplos Concretos

**Pergunta ambígua — tratamento RUIM (atual):**
Recruiter: "Quero alguém bom em liderança mas que não mande demais"
LIA: "Não tenho certeza do que você quer dizer. Você poderia reformular sua solicitação?"

**Pergunta ambígua — tratamento BOM (benchmark):**
> "Entendo — você está descrevendo liderança facilitadora, não autoritária. No Big Five, isso corresponde a alto Agreeableness combinado com abertura a colaboração (alto Openness). No modelo Dreyfus, seria alguém no nível 'Proficiente' em liderança — tem julgamento próprio mas ainda busca consenso antes de decidir. Posso configurar o WSI para avaliar especificamente essa dimensão: 'Como você tomou uma decisão importante em que precisou do buy-in da equipe?' Isso vai separar os facilitadores dos autoritários. Quer que eu ajuste as perguntas da entrevista com esse foco?"

**Pressão de CEO — tratamento RUIM (atual):**
> [Roteia para intent de busca de candidatos — sem reconhecer o contexto de urgência]

**Pressão de CEO — tratamento BOM:**
> "Entendido — o CEO precisa ver algo amanhã cedo. Tenho 3 candidatos já avaliados que posso montar num resumo executivo agora: um perfil forte sem ressalvas, um com ótimo técnico mas gap em liderança, e um que precisa de mais validação. O que NÃO tenho ainda é o candidato externo que buscamos no Pearch — esse vai demorar mais 2 dias para triagem completa. Apresento os 3 disponíveis com ressalvas claras, ou prefere esperar para ter o quadro completo?"

**Red flag com contexto — tratamento RUIM (atual):**
> "Candidato: Score 89%. Pontos de atenção: 4 mudanças de emprego em 3 anos."

**Red flag com contexto — tratamento BOM:**
> "Marina tem o maior score técnico do seu pipeline: 89%. O ponto que merece discussão são as 4 mudanças em 3 anos — mas olhando os detalhes: foram três promoções para cargos maiores e uma saída voluntária de empresa que faliu. Esse padrão é de alguém que o mercado quer, não de instabilidade. Em executive search, isso seria visto como sinal positivo de demand. A pergunta certa na entrevista é: 'O que te faria ficar aqui por 3+ anos?' — não 'por que você saiu tão rápido?'"

### Recomendações

1. Adicionar ao `cv_screening.yaml` instrução de contextualização de red flags: "Quando red flag detectado, apresentar sempre com contexto atenuante possível antes de recomendar rejeição"
2. Criar bloco de `pressure_handling` no `recruiter_assistant.yaml` para situações de urgência executiva
3. Adicionar ao `lia_persona.yaml` (seção de sagacidade) exemplos de tradução de liderança ambígua para dimensões WSI/Dreyfus/Big Five
4. Revisar `out_of_scope_responses.general` no `defensive.yaml` — substituir recusa direta por "o que posso oferecer sobre isso é X, para mais detalhe você precisaria de Y"
5. Adicionar instrução no `wsi_evaluation.yaml`: "Quando score alto + red flag, não apenas listar — contextualizar e oferecer perspectiva de recrutador sênior sobre o trade-off"

---

## Score Consolidado e Impacto em NPS / Adoção

### Avaliação Geral: 2.9 / 5

A plataforma LIA está em um **estágio de maturidade intermediário** de inteligência percebida. A infraestrutura está correta — arquitetura multi-agente, fairness guard, auditoria, vocabulário técnico de RH, scoring WSI com evidências. Mas há um gap entre o que está **instruído nos prompts** e o que é **experienciado pelo recrutador** no diálogo.

### Posicionamento Competitivo

| Plataforma | Score Estimado | Diferencial |
|---|---|---|
| Eightfold.ai | 4.5 / 5 | Explicabilidade de ranking + dados de mercado integrados + CoT visível |
| Beamery | 4.0 / 5 | Proatividade push nativa + nurture inteligente |
| Findem | 3.8 / 5 | Cross-job matching + candidate intent signals |
| Ashby | 3.5 / 5 | Didática forte + documentação de decisão |
| **LIA (WeDOTalent)** | **2.9 / 5** | WSI methodology + fairness + vocabulário BR sólido |
| SmartRecruiters IA | 2.5 / 5 | Vocabulário genérico, pouca explicabilidade |

A LIA tem um **diferencial competitivo real**: a metodologia WSI (Bloom + Dreyfus + Big Five) é mais profunda que qualquer concorrente listado acima. O problema é que essa profundidade **não chega ao recrutador de forma conversacional** — fica nos logs de auditoria e nos JSONs de resposta.

### Impacto em NPS e Adoção

Com score 2.9/5 em inteligência percebida, o risco real é:

1. **Churn por frustração**: Recrutadores experientes (5+ anos) vão sentir que a LIA é "mais uma ferramenta" que executa comandos, não uma parceira que pensa junto. NPS de recrutadores sênior tende a ser baixo.
2. **Under-utilization de features**: Capacidades avançadas (Digital Twin, Skills Ontology, Workforce Planning) não serão usadas se o agente não as apresentar proativamente no momento certo.
3. **Baixa diferenciação percebida**: O recrutador que vem do Gupy ou do Greenhouse vai sentir que a LIA é "mais inteligente" operacionalmente (automação, scoring) mas não estrategicamente (insights, opinião fundamentada, antecipação).

### Top 5 Ações Prioritárias (ROI em NPS)

| Prioridade | Ação | Esforço | Impacto Esperado |
|---|---|---|---|
| 1 | Briefing matinal proativo com diagnóstico de SLA + candidatos em risco | Médio | +0.8 no score D3 |
| 2 | Contextualização de score: percentil + distância do threshold | Baixo | +0.7 no score D2 |
| 3 | Quantificação do impacto de flexibilização de critérios | Médio | +0.6 no score D2 |
| 4 | Red flag com contexto atenuante antes de recomendar rejeição | Baixo | +0.5 no score D4 |
| 5 | Vocabulário de executive search nos agentes de sourcing | Baixo | +0.4 no score D1 |

### Conclusão

A LIA está construída sobre **alicerces sólidos de inteligência**: WSI, FairnessGuard, auditoria, multi-agente especializado. O gap não é técnico — é **conversacional e perceptual**. O recrutador não vê o raciocínio que existe nos bastidores. A prioridade não é construir mais features: é fazer o que já existe **chegar à superfície da conversa** de forma que um recrutador sênior reconheça como perspicaz, fundamentado e proativo.

O benchmark de 4.25/5 do mercado enterprise é atingível em 2-3 sprints de trabalho focado em prompts e na construção de 3-4 ferramentas de suporte (cross-job matching, briefing automático, contextualização de score). A metodologia WSI, quando bem explicada conversacionalmente, pode ser o maior diferencial competitivo da plataforma.

---

**Arquivos auditados:**
- `/home/runner/workspace/lia-agent-system/app/prompts/shared/lia_persona.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/shared/agent_prompts.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/shared/defensive.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/domains/orchestrator.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/domains/recruiter_assistant.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/domains/sourcing.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/domains/analysis.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/domains/analytics.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/domains/cv_screening.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/domains/wsi_evaluation.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/domains/wsi_interview.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/domains/communication.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/domains/automation.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/domains/job_management.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/domains/digital_twin.yaml`
- `/home/runner/workspace/lia-agent-system/app/prompts/domains/pipeline_transition.yaml`
- `/home/runner/workspace/lia-agent-system/app/api/v1/proactive_actions.py`
- `/home/runner/workspace/lia-agent-system/app/api/v1/pipeline_velocity.py`
- `/home/runner/workspace/lia-agent-system/app/api/v1/recruitment_journey.py`
- `/home/runner/workspace/lia-agent-system/app/api/v1/lia_assistant/_shared.py`
- `/home/runner/workspace/lia-agent-system/app/domains/sourcing/agents/sourcing_system_prompt.py`
- `/home/runner/workspace/lia-agent-system/app/domains/sourcing/services/sourcing_pipeline.py`
- `/home/runner/workspace/lia-agent-system/app/docs/audit/fase1-reconhecimento/PLATFORM_MAP.md`
- `/home/runner/workspace/lia-agent-system/app/docs/audit/fase1-reconhecimento/FLOW_TRACES.md`
