# Roteiro de Smoke Test — Componentes de IA
**Data:** 2026-04-03 | **Versão:** 1.0
**Objetivo:** Validar o que funciona / não funciona em cada componente de IA antes de automatizar testes.
**Tempo estimado:** 3–4 horas para executar todos os 6 componentes
**Como usar:** Para cada teste, marcar ✅ PASSOU / ❌ FALHOU / ⚠️ PARCIAL. Anotar comportamento observado no campo "Observação".

---

## Instruções Gerais

### Preparação do Ambiente
1. Abra o navegador (Chrome recomendado) e acesse a plataforma LIA.
2. Faça login com uma conta que tenha permissão de recrutador/admin.
3. Verifique se o token de autenticação está presente: abra o Console do navegador (F12) e execute:
   ```js
   localStorage.getItem('access_token')
   ```
   O retorno deve ser uma string não vazia. Se retornar `null`, faça login novamente.

### Como Usar o DevTools
- **Console (F12 > Console):** Monitore erros JavaScript em tempo real. Antes de cada componente, limpe o console com `Ctrl+L` ou clicando no ícone de lixeira.
- **Aba Network (F12 > Network):** Filtre por `Fetch/XHR` para capturar chamadas de API. Para streaming, observe requisições com duração longa e resposta incremental (EventStream ou chunked).
- **Como registrar problemas:**
  - Copie a mensagem de erro completa do console.
  - Capture screenshot da aba Network mostrando o status HTTP da requisição problemática (ex: 401, 500, timeout).
  - Anote o payload enviado (aba "Request") e a resposta recebida (aba "Response" ou "Preview").
  - Registre no campo "Observação" do teste correspondente.

### Convenções
- **✅ PASSOU:** Comportamento exatamente conforme esperado.
- **❌ FALHOU:** Comportamento ausente, erro visível, ou crash.
- **⚠️ PARCIAL:** Funciona com ressalvas (lentidão, resposta incompleta, comportamento inesperado não crítico).

### Red Flags Globais (aplicáveis a todos os componentes)
- Loading infinito (spinner que nunca para após 30 segundos)
- Erros no console JavaScript (especialmente `401 Unauthorized`, `500 Internal Server Error`, `TypeError`)
- Respostas em inglês quando o contexto é em português
- Resposta genérica sem usar contexto da plataforma (ex: menciona "candidatos" sem dados reais)
- Interface congela ou não responde após envio de mensagem
- Token expirado não tratado graciosamente (crash ao invés de redirecionar para login)

---

## COMPONENTE 1 — LIA Float (ícone cérebro, canto inferior direito)

### Pré-condições
1. Estar logado na plataforma com perfil de recrutador.
2. Navegar para qualquer página principal (ex: Dashboard ou lista de vagas).
3. Confirmar que o ícone de cérebro está visível no canto inferior direito da tela.
4. Abrir a aba Network no DevTools e filtrar por `XHR` ou `Fetch`.
5. Limpar o console do navegador.

### Testes Funcionais

**T1.1 — Abertura do painel flutuante**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Clique no ícone de cérebro no canto inferior direito.
  2. Verifique se um painel de chat abre com dimensões aproximadas de 420×580px.
  3. Verifique se há um campo de texto para digitar mensagens na parte inferior do painel.
  4. Verifique se há um cabeçalho com o nome/logo da LIA.
- **Critérios de sucesso:** Painel abre sem erro, campo de input está habilitado, sem erros no console.
- **Observação:** _______________________________________________

**T1.2 — Envio de mensagem simples e recebimento de resposta**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Com o painel aberto, clique no campo de texto.
  2. Digite: `Olá, pode me ajudar?`
  3. Pressione Enter ou clique no botão de envio.
  4. Observe a aba Network — deve aparecer uma requisição `POST /api/backend-proxy/chat`.
  5. Aguarde a resposta aparecer no painel (máx. 30 segundos).
- **Critérios de sucesso:** Mensagem enviada aparece no chat, resposta da LIA aparece, requisição HTTP retorna 200.
- **Payload esperado na requisição:** `{ "content": "Olá, pode me ajudar?" }`
- **Observação:** _______________________________________________

**T1.3 — Streaming de resposta (texto aparece progressivamente)**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Envie a mensagem: `Me explique como funciona o pipeline de candidatos nessa plataforma.`
  2. Observe se o texto da resposta aparece palavra por palavra / chunk por chunk (streaming) ou apenas de uma vez após longa espera.
  3. Na aba Network, verifique se a requisição fica em estado "pendente" por alguns segundos enquanto o texto aparece (indicativo de streaming via WebSocket ou SSE).
- **Critérios de sucesso:** Texto aparece progressivamente, sem espera de resposta completa antes de exibir.
- **Red flag:** Nenhum texto aparece por 15+ segundos e depois aparece tudo de uma vez (streaming quebrado).
- **Observação:** _______________________________________________

**T1.4 — Abertura do Super Prompt (modal fullscreen)**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Com o painel flutuante aberto, procure por um botão de expandir (ícone de seta para fora, maximizar, ou texto "Expandir").
  2. Clique nesse botão.
  3. Verifique se um modal fullscreen abre sobrepondo a página inteira.
  4. Verifique se o histórico de conversa (se houver) é mantido no modal expandido.
  5. Feche o modal com o botão de fechar (X) ou tecla Escape.
- **Critérios de sucesso:** Modal abre em fullscreen, histórico preservado, fecha corretamente.
- **Observação:** _______________________________________________

**T1.5 — HITL (Human-in-the-Loop): Card de confirmação para ações reais**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. No painel flutuante, envie: `Mova o candidato João Silva para a etapa de entrevista técnica.`
  2. Observe se a LIA apresenta um "card de confirmação" (botões Confirmar/Cancelar) antes de executar a ação.
  3. Clique em "Cancelar" e verifique se nenhuma ação foi executada.
  4. Repita e clique em "Confirmar", verifique se a ação ocorre.
- **Critérios de sucesso:** Card de confirmação aparece antes de ações destrutivas/irreversíveis. Cancelar não executa a ação.
- **Observação:** _______________________________________________

**T1.6 — Estado de erro: falha na API**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Abra o DevTools > Network > clique em "Block request URL" (Chrome) e bloqueie `*/api/backend-proxy/chat*`.
  2. Tente enviar uma mensagem no painel.
  3. Observe se aparece mensagem de erro amigável (ex: "Não foi possível conectar. Tente novamente.").
  4. Remova o bloqueio e tente novamente.
- **Critérios de sucesso:** Erro tratado graciosamente, mensagem de fallback exibida, interface não congela.
- **Observação:** _______________________________________________

**T1.7 — Persistência de conversa (conversation_id)**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Envie 3 mensagens em sequência no painel flutuante.
  2. Na aba Network, inspecione o payload de cada requisição `POST /api/backend-proxy/chat`.
  3. Verifique se o campo `conversation_id` está presente a partir da segunda mensagem e é o mesmo nas 3 requisições.
- **Critérios de sucesso:** `conversation_id` consistente mantém contexto da conversa.
- **Observação:** _______________________________________________

### Testes de Qualidade de Resposta

**Q1.1 — Consulta sobre pipeline de candidatos**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Prompt:** `Quantos candidatos estão parados há mais de 7 dias no triagem?`
- **Comportamento esperado:** A LIA deve buscar dados reais do pipeline e retornar números ou indicar que está consultando. Não deve inventar números. Se não tiver acesso, deve informar claramente.
- **Red flags:** Responde "Não tenho acesso a esses dados" sem tentar buscar; inventa números sem fonte; responde em inglês.
- **Observação:** _______________________________________________

**Q1.2 — Ação contextual sobre candidato específico**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Prompt:** `Quais são os próximos passos para o candidato com melhor score na vaga de Dev Backend?`
- **Comportamento esperado:** Deve mencionar o candidato pelo nome (se acessível), sugerir próximo passo no fluxo, usar contexto da plataforma (etapas do pipeline).
- **Red flags:** Resposta genérica sem dados da plataforma; menciona candidatos fictícios.
- **Observação:** _______________________________________________

**Q1.3 — Pergunta sobre vaga específica**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Prompt:** `Qual é o status atual da vaga de Engenheiro de Dados?`
- **Comportamento esperado:** Deve retornar status real (ativa, pausada, fechada), número de candidatos, etapa predominante.
- **Red flags:** Inventa status; responde "não sei" sem tentar consultar.
- **Observação:** _______________________________________________

**Q1.4 — Solicitação de resumo executivo**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Prompt:** `Me dê um resumo das vagas abertas com mais urgência essa semana.`
- **Comportamento esperado:** Lista vagas com prazo ou alta prioridade, menciona dados como quantidade de candidatos e SLA.
- **Red flags:** Lista vagas fictícias; não usa dados da plataforma; resposta em inglês.
- **Observação:** _______________________________________________

**Q1.5 — Manutenção de contexto em conversa multi-turno**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Envie: `Fale sobre a vaga de Product Manager.`
  2. Aguarde resposta.
  3. Envie em seguida: `E quantos candidatos ela tem no momento?`
- **Comportamento esperado:** Na segunda mensagem, a LIA deve entender que "ela" refere-se à vaga de Product Manager mencionada anteriormente (contexto mantido).
- **Red flags:** Segunda resposta ignora o contexto e pergunta "sobre qual vaga?"; perde o fio da conversa.
- **Observação:** _______________________________________________

### Checklist de Regressão — Componente 1

| Item | Status | Observação |
|------|--------|------------|
| Painel abre sem erro de JavaScript | | |
| Campo de input está habilitado e recebe texto | | |
| Requisição POST para `/api/backend-proxy/chat` é feita | | |
| Token Bearer está no header Authorization | | |
| Streaming funciona (texto aparece progressivamente) | | |
| HITL card aparece antes de ações reais | | |
| Erros de API são tratados graciosamente | | |
| Histórico de conversa é mantido (conversation_id) | | |
| Respostas estão em português (pt-BR) | | |
| Super Prompt (fullscreen) abre e fecha corretamente | | |

---

## COMPONENTE 2 — Expandable AI Prompt (ao lado da tabela de vagas)

### Pré-condições
1. Navegar para a lista/tabela de vagas (Jobs) na plataforma.
2. Localizar o painel "Expandable AI Prompt" (EAP) posicionado ao lado direito ou acima da tabela de vagas.
3. Se o painel estiver recolhido, clicar para expandi-lo.
4. Confirmar que as 6 abas estão visíveis: **Natural, Boolean, Filtros, JD, Similar, Arquétipos**.
5. Abrir DevTools > Network para monitorar requisições.

### Testes Funcionais

**T2.1 — Painel abre e exibe as 6 abas corretamente**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Clique no componente EAP para expandi-lo.
  2. Verifique se as 6 abas estão presentes: Natural, Boolean, Filtros, JD, Similar, Arquétipos.
  3. Clique em cada aba e verifique se o conteúdo/input muda.
- **Critérios de sucesso:** Todas as 6 abas visíveis, clicáveis e com conteúdo distinto.
- **Observação:** _______________________________________________

**T2.2 — Aba Natural: busca por linguagem natural**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Clique na aba "Natural".
  2. No campo SmartSearchInput, digite: `Backend sênior em São Paulo, 5+ anos Node.js, disponível para híbrido`
  3. Execute a busca (Enter ou botão buscar).
  4. Observe a aba Network — verifique qual endpoint é chamado.
  5. Aguarde resultados aparecerem na tabela de vagas ou painel de resultados.
- **Critérios de sucesso:** Busca executada, resultados retornados e relevantes ao query, sem erro 4xx/5xx.
- **Observação:** _______________________________________________

**T2.3 — Aba Boolean: busca com operadores lógicos**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Clique na aba "Boolean".
  2. Digite: `python AND (django OR fastapi) AND sênior NOT júnior`
  3. Execute a busca.
  4. Verifique se os resultados respeitam os operadores (candidatos com Python e Django/FastAPI, sem juniores).
- **Critérios de sucesso:** Operadores booleanos processados corretamente, resultados filtrados conforme lógica.
- **Red flags:** Operadores ignorados, resultados incluem "júnior" mesmo com NOT júnior.
- **Observação:** _______________________________________________

**T2.4 — Aba Filtros: busca com filtros estruturados**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Clique na aba "Filtros".
  2. Preencha os filtros disponíveis (ex: localidade = "São Paulo", nível = "Sênior", modalidade = "Híbrido").
  3. Aplique os filtros.
  4. Verifique se os resultados correspondem aos filtros selecionados.
- **Critérios de sucesso:** Filtros aplicados refletem nos resultados, combinações múltiplas funcionam.
- **Observação:** _______________________________________________

**T2.5 — Aba JD (Job Description): busca por descrição de vaga**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Clique na aba "JD".
  2. Cole ou digite uma descrição de cargo: `Buscamos Engenheiro de Software Sênior com experiência em sistemas distribuídos, Kubernetes e Go. Trabalho 100% remoto.`
  3. Execute a busca.
  4. Verifique se candidatos retornados têm perfil compatível com a JD.
- **Critérios de sucesso:** Busca semântica por JD retorna candidatos com skills relevantes.
- **Observação:** _______________________________________________

**T2.6 — Aba Similar: busca por candidato similar**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Clique na aba "Similar".
  2. Selecione ou informe um candidato existente como referência (ex: busque pelo nome ou ID de um candidato aprovado).
  3. Execute a busca.
  4. Verifique se os resultados apresentam candidatos com perfil semelhante ao de referência.
- **Critérios de sucesso:** Candidatos retornados têm habilidades/experiência similar ao candidato de referência.
- **Observação:** _______________________________________________

**T2.7 — Aba Arquétipos: busca por perfil arquetípico**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Clique na aba "Arquétipos".
  2. Selecione um arquétipo disponível (ex: "Líder Técnico", "Executor Ágil", "Especialista Deep").
  3. Execute a busca.
  4. Verifique se candidatos retornados correspondem ao arquétipo selecionado.
- **Critérios de sucesso:** Arquétipo selecionado filtra candidatos com características comportamentais correspondentes.
- **Observação:** _______________________________________________

**T2.8 — Limpeza de busca e reset do painel**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Após realizar qualquer busca, clique no botão de limpar/reset (X ou "Limpar").
  2. Verifique se o campo de input foi zerado.
  3. Verifique se a tabela de vagas voltou ao estado original (sem filtros ativos).
- **Critérios de sucesso:** Reset completo do estado do componente sem erro.
- **Observação:** _______________________________________________

### Testes de Qualidade de Resposta

**Q2.1 — Precisão da busca natural**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Prompt (aba Natural):** `Desenvolvedor fullstack com React e Node, pelo menos 3 anos de experiência, preferencialmente no Rio de Janeiro`
- **Comportamento esperado:** Resultados devem incluir candidatos com React E Node, 3+ anos, localizados no Rio. Candidatos sem essas características não devem aparecer nos primeiros resultados.
- **Red flags:** Retorna candidatos sem correspondência; ignora a localização; resultados vazios sem mensagem explicativa.
- **Observação:** _______________________________________________

**Q2.2 — Boolean com negação**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Prompt (aba Boolean):** `java AND (spring OR quarkus) AND pleno NOT estagiário NOT júnior`
- **Comportamento esperado:** Apenas candidatos plenos com Java e Spring/Quarkus, excluindo estagiários e juniores.
- **Red flags:** Operador NOT ignorado; candidatos juniores presentes nos resultados.
- **Observação:** _______________________________________________

**Q2.3 — Busca por JD complexa com múltiplos requisitos**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Prompt (aba JD):** `Preciso de um Cientista de Dados com experiência em machine learning, Python, SQL e visualização de dados (Power BI ou Tableau). Diferencial: experiência com LLMs e MLOps. Vaga híbrida em São Paulo, salário até R$ 18.000.`
- **Comportamento esperado:** Candidatos retornados possuem Python e SQL obrigatórios; ML como critério relevante; localização ou modalidade considerada.
- **Red flags:** Ignora stack técnica; retorna candidatos sem Python/SQL.
- **Observação:** _______________________________________________

**Q2.4 — Coerência entre abas para mesmo perfil**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Busque na aba Natural: `Gerente de Produto sênior com experiência em B2B SaaS`
  2. Anote os 3 primeiros resultados.
  3. Busque na aba Filtros com: cargo = "Product Manager", nível = "Sênior", setor = "SaaS/Tech".
  4. Compare os resultados.
- **Comportamento esperado:** Há sobreposição razoável entre os resultados (candidatos relevantes aparecem em ambas as buscas).
- **Red flags:** Resultados completamente distintos sem justificativa; uma aba retorna 0 resultados.
- **Observação:** _______________________________________________

**Q2.5 — Busca sem resultados: mensagem adequada**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Prompt (aba Natural):** `Neurocirurgião especialista em robótica com 20 anos de experiência em Manaus`
- **Comportamento esperado:** Sem resultados ou com mensagem informando que nenhum candidato foi encontrado. Não deve retornar candidatos irrelevantes apenas para preencher a lista.
- **Red flags:** Retorna candidatos sem nenhuma relação; crash da interface; mensagem de erro técnico exposta.
- **Observação:** _______________________________________________

### Checklist de Regressão — Componente 2

| Item | Status | Observação |
|------|--------|------------|
| Painel EAP abre sem erro | | |
| Todas as 6 abas estão presentes e clicáveis | | |
| Aba Natural processa linguagem natural | | |
| Aba Boolean respeita operadores AND/OR/NOT | | |
| Aba Filtros aplica combinações de filtros | | |
| Aba JD faz busca semântica por descrição | | |
| Aba Similar retorna perfis parecidos | | |
| Aba Arquétipos filtra por perfil comportamental | | |
| Reset/limpeza funciona em todas as abas | | |
| Busca sem resultado exibe mensagem amigável | | |
| Respostas em português (pt-BR) | | |

---

## COMPONENTE 3 — Expanded Chat (Wizard de Criação de Vaga)

### Pré-condições
1. Navegar para a área de criação de vagas (ex: "Nova Vaga" ou "Criar Vaga").
2. Selecionar a opção de criar vaga via assistente de IA (Wizard) — pode ser um botão "Criar com IA" ou similar.
3. Confirmar que o Wizard abre em modo de chat expandido (tela cheia ou painel grande).
4. Abrir DevTools > Network e filtrar por requisições para `*/wizard/smart-orchestrate/*`.
5. Ter em mente os 7 estágios do Wizard: **InputEvaluation → Competencies → EnrichedJD → WSIQuestions → Salary → SearchCalibration → ReviewPublish**.

### Testes Funcionais

**T3.1 — Abertura do Wizard e estágio inicial (InputEvaluation)**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Clique em "Criar vaga com IA" ou equivalente.
  2. Verifique se o Wizard abre com uma mensagem de boas-vindas ou prompt inicial.
  3. Observe se há indicação do estágio atual (ex: barra de progresso, label "Passo 1").
  4. Na aba Network, confirme que `current_stage` na requisição indica `InputEvaluation`.
- **Critérios de sucesso:** Wizard abre corretamente, estágio inicial identificado, input habilitado.
- **Observação:** _______________________________________________

**T3.2 — Envio de briefing inicial e progressão para Competencies**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. No campo do Wizard (estágio InputEvaluation), envie: `Preciso de um engenheiro de dados com Python e Spark, remoto, sênior`
  2. Aguarde a resposta do Wizard.
  3. Verifique se o Wizard avança para o próximo estágio (Competencies).
  4. Na aba Network, confirme que o payload da próxima requisição contém `"current_stage": "Competencies"` ou equivalente.
- **Critérios de sucesso:** Briefing processado, transição de estágio ocorre automaticamente ou com confirmação.
- **Observação:** _______________________________________________

**T3.3 — Estágio Competencies: validação de competências sugeridas**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. No estágio Competencies, o Wizard deve sugerir competências técnicas e comportamentais.
  2. Verifique se as sugestões são relevantes ao briefing (Python, Spark, Engenheiro de Dados).
  3. Tente adicionar uma competência manualmente (ex: `Adicione também conhecimento em Kafka`).
  4. Confirme que a competência adicionada é incorporada.
- **Critérios de sucesso:** Competências sugeridas são coerentes com o briefing; usuário pode editar.
- **Observação:** _______________________________________________

**T3.4 — Estágio EnrichedJD: geração de Job Description enriquecida**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Após confirmar competências, aguarde o Wizard avançar para EnrichedJD.
  2. Verifique se uma Job Description completa é gerada (título, resumo, responsabilidades, requisitos, benefícios).
  3. Confirme que a JD usa os dados informados (Python, Spark, remoto, sênior).
  4. Tente editar um trecho da JD e confirmar a edição.
- **Critérios de sucesso:** JD gerada é coerente, completa e editável.
- **Red flags:** JD genérica que não reflete o briefing; JD em inglês; campos obrigatórios vazios.
- **Observação:** _______________________________________________

**T3.5 — Estágio WSIQuestions: geração de perguntas de triagem**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Avance para o estágio WSIQuestions.
  2. Verifique se perguntas de triagem (WSI - screening questions) são geradas automaticamente.
  3. Confirme que a requisição `POST /api/lia/api/wsi/generate-job-screening-questions` é disparada.
  4. Verifique se as perguntas são relevantes ao cargo (Python, Spark, Engenharia de Dados).
  5. Tente remover uma pergunta e adicionar outra customizada.
- **Critérios de sucesso:** Perguntas geradas, endpoint WSI chamado com sucesso (200), perguntas editáveis.
- **Observação:** _______________________________________________

**T3.6 — Estágio Salary: sugestão de faixa salarial**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Avance para o estágio Salary.
  2. Verifique se o Wizard sugere uma faixa salarial (min/max) com base no cargo e mercado.
  3. Confirme que a sugestão é coerente para um Engenheiro de Dados Sênior Remoto no Brasil.
  4. Altere manualmente a faixa e confirme que a alteração é aceita.
- **Critérios de sucesso:** Faixa salarial sugerida e razoável para o mercado; editável.
- **Red flags:** Salário em dólar ou outra moeda; faixa absurda (ex: R$ 500 ou R$ 500.000); campo bloqueado para edição.
- **Observação:** _______________________________________________

**T3.7 — Estágio SearchCalibration e ReviewPublish**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Avance para SearchCalibration — verifique se parâmetros de busca de candidatos são configurados.
  2. Confirme os parâmetros e avance para ReviewPublish.
  3. No ReviewPublish, verifique se um resumo completo da vaga é apresentado para revisão final.
  4. Verifique se há botão "Publicar Vaga" ou "Salvar Rascunho".
  5. Clique em "Salvar Rascunho" e confirme que a vaga é salva sem publicar.
- **Critérios de sucesso:** Fluxo completo do Wizard executado, vaga salva como rascunho.
- **Observação:** _______________________________________________

**T3.8 — Collected data acumulado entre estágios**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Durante o fluxo do Wizard, inspecione o payload das requisições `POST /wizard/smart-orchestrate/`.
  2. Verifique se o campo `collected_data` vai acumulando as informações de cada estágio.
  3. No estágio ReviewPublish, confirme que `collected_data` contém dados de todos os estágios anteriores.
- **Critérios de sucesso:** `collected_data` acumula corretamente, nenhum dado de estágio anterior é perdido.
- **Observação:** _______________________________________________

### Testes de Qualidade de Resposta

**Q3.1 — Coerência do briefing ao longo do Wizard**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Prompt inicial:** `Preciso contratar um Tech Lead de Mobile com experiência em React Native e liderança de times de até 10 pessoas. A vaga é presencial em Curitiba, nível sênior.`
- **Comportamento esperado:** Todos os estágios subsequentes devem refletir: React Native, liderança, presencial, Curitiba, sênior. Nenhum estágio deve "esquecer" o briefing inicial.
- **Red flags:** JD menciona tecnologias diferentes; localização muda para remoto; nível de experiência altera para pleno.
- **Observação:** _______________________________________________

**Q3.2 — Resposta a correção do usuário em mid-wizard**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Inicie o Wizard com: `Analista de Marketing Digital, pleno, São Paulo, híbrido`
  2. No estágio Competencies, envie: `Na verdade, preciso de nível sênior, não pleno. Corrija isso.`
  3. Verifique se o Wizard atualiza o nível para sênior nos estágios seguintes.
- **Comportamento esperado:** Correção aceita e propagada para os estágios seguintes (JD, Salary, etc.).
- **Red flags:** Wizard ignora a correção; ainda apresenta "pleno" nos próximos estágios.
- **Observação:** _______________________________________________

**Q3.3 — Perguntas WSI relevantes ao cargo**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Briefing:** `DevOps Engineer sênior com Kubernetes, Terraform e AWS. Vaga remoto.`
- **Comportamento esperado:** Perguntas WSI devem incluir questões sobre Kubernetes, Terraform, AWS — não perguntas genéricas de RH (ex: "Quais são seus pontos fortes?") sem contexto técnico.
- **Red flags:** Perguntas completamente genéricas; perguntas de outra área (ex: pergunta de vendas).
- **Observação:** _______________________________________________

**Q3.4 — JD enriquecida sem alucinação**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Briefing:** `Designer UX/UI, pleno, foco em design systems e acessibilidade, remoto`
- **Comportamento esperado:** A JD gerada deve falar sobre Design Systems e acessibilidade. Não deve mencionar habilidades não informadas como "Machine Learning" ou "Back-end development".
- **Red flags:** JD inclui requisitos inventados não mencionados no briefing; descrição genérica de "Designer".
- **Observação:** _______________________________________________

**Q3.5 — Faixa salarial contextualizada ao mercado brasileiro**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Briefing:** `Engenheiro de Software Sênior, Python, back-end, remoto`
- **Comportamento esperado:** Faixa salarial sugerida deve ser coerente com o mercado brasileiro (aproximadamente R$ 12.000–R$ 22.000 para este perfil em 2025/2026). Não deve ser em dólar nem absurda.
- **Red flags:** Faixa em USD; valores abaixo de R$ 5.000 ou acima de R$ 50.000 para o perfil; campo vazio.
- **Observação:** _______________________________________________

### Checklist de Regressão — Componente 3

| Item | Status | Observação |
|------|--------|------------|
| Wizard abre corretamente | | |
| Estágio InputEvaluation processa briefing | | |
| Transição entre estágios funciona | | |
| Competencies sugeridas são coerentes | | |
| JD enriquecida gerada sem alucinação | | |
| Endpoint WSI generate-job-screening-questions chamado | | |
| Perguntas WSI relevantes ao cargo | | |
| Faixa salarial em BRL e razoável | | |
| SearchCalibration configurável | | |
| ReviewPublish exibe resumo completo | | |
| collected_data acumula corretamente entre estágios | | |
| Correções do usuário propagadas nos estágios seguintes | | |

---

## COMPONENTE 4 — Prompt Expandido Dentro da Vaga (Tabela/Kanban)

### Pré-condições
1. Navegar para uma vaga específica (clicar em uma vaga na lista ou kanban).
2. Dentro da vaga, localizar o campo de prompt expandido (pode ser um botão "Perguntar à IA", ícone de chat, ou painel lateral).
3. Confirmar que o contexto da vaga está carregado (nome da vaga, candidatos associados visíveis).
4. Abrir DevTools > Network e filtrar por requisições para `*/api/backend-proxy/orchestrator/process*`.

### Testes Funcionais

**T4.1 — Abertura do prompt dentro do contexto da vaga**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Abra uma vaga específica que tenha candidatos no pipeline.
  2. Clique para abrir o prompt de IA dentro da vaga.
  3. Verifique se o contexto da vaga é pré-carregado (ex: nome da vaga aparece no header do chat, ou a primeira mensagem da IA já menciona a vaga).
- **Critérios de sucesso:** Prompt abre com contexto da vaga ativo; sem erros no console.
- **Observação:** _______________________________________________

**T4.2 — Envio de mensagem e chamada ao endpoint correto**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Com o prompt aberto dentro de uma vaga, envie: `Quantos candidatos estão nessa vaga?`
  2. Observe a aba Network — deve aparecer `POST /api/backend-proxy/orchestrator/process`.
  3. Inspecione o payload: deve conter `context_type` (ex: `"job"` ou `"vacancy"`) e `context_id` com o ID da vaga.
- **Critérios de sucesso:** Endpoint correto chamado, payload contém contexto da vaga.
- **Payload esperado:** `{ "user_id": "...", "message": "...", "context_type": "job", "context_id": "<id_da_vaga>" }`
- **Observação:** _______________________________________________

**T4.3 — Resposta contextualizada à vaga específica**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Dentro da vaga "X", envie: `Quais candidatos estão na etapa de triagem?`
  2. Verifique se a resposta menciona candidatos reais dessa vaga, não de outras vagas.
  3. Abra outra vaga "Y" e faça a mesma pergunta.
  4. Confirme que as respostas são diferentes e específicas a cada vaga.
- **Critérios de sucesso:** Respostas são específicas ao contexto da vaga aberta.
- **Red flags:** Mesma resposta genérica para qualquer vaga; menciona candidatos de outras vagas.
- **Observação:** _______________________________________________

**T4.4 — Funcionamento na visualização Kanban**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Alterne a visualização da vaga para modo Kanban (se disponível).
  2. Abra o prompt de IA nesse modo.
  3. Envie: `Qual etapa tem mais candidatos parados?`
  4. Verifique se a resposta faz sentido para o kanban exibido.
- **Critérios de sucesso:** Prompt funciona em modo kanban da mesma forma que em modo tabela.
- **Observação:** _______________________________________________

**T4.5 — Ação sobre candidato específico dentro da vaga**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Dentro de uma vaga com candidatos, envie: `Mova o candidato com melhor score para a próxima etapa.`
  2. Verifique se aparece card de confirmação HITL antes da ação.
  3. Confirme e verifique se o candidato foi movido no pipeline.
- **Critérios de sucesso:** HITL ativo para ações no pipeline; ação executada após confirmação.
- **Observação:** _______________________________________________

**T4.6 — Erro de contexto: vaga sem candidatos**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Abra uma vaga que não tenha candidatos no pipeline.
  2. Envie: `Quais candidatos estão em triagem?`
  3. Verifique se a IA responde adequadamente (ex: "Não há candidatos nessa vaga ainda.") sem inventar dados.
- **Critérios de sucesso:** Resposta honesta sobre ausência de candidatos; não inventa dados.
- **Observação:** _______________________________________________

### Testes de Qualidade de Resposta

**Q4.1 — Análise de funil da vaga**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Prompt:** `Me mostre um resumo do funil dessa vaga: quantos por etapa e qual a taxa de conversão estimada.`
- **Comportamento esperado:** Resposta com dados por etapa (triagem, entrevista, proposta, etc.) baseados nos candidatos reais da vaga.
- **Red flags:** Dados fictícios; resposta sobre outra vaga; "Não tenho acesso a essa informação" sem tentar buscar.
- **Observação:** _______________________________________________

**Q4.2 — Identificação de gargalos no pipeline**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Prompt:** `Quais candidatos estão parados há mais de 5 dias sem movimentação?`
- **Comportamento esperado:** Lista candidatos com nome e dias de inatividade baseados em dados reais. Deve sugerir ação (ex: "Recomendo contato com esses candidatos").
- **Red flags:** Lista candidatos sem verificar data de última movimentação; ignora o critério de 5 dias.
- **Observação:** _______________________________________________

**Q4.3 — Recomendação baseada em fit**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Prompt:** `Qual candidato em triagem tem o melhor fit para essa vaga? Justifique.`
- **Comportamento esperado:** Indica um candidato específico com justificativa baseada nas competências da vaga e no perfil do candidato. Não deve apenas listar todos os candidatos sem ordenação.
- **Red flags:** Resposta genérica sem indicar candidato específico; justificativa sem dados concretos.
- **Observação:** _______________________________________________

**Q4.4 — Pergunta sobre SLA e urgência**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Prompt:** `Essa vaga está dentro do SLA? Quando precisa ser fechada?`
- **Comportamento esperado:** Informa data de abertura, prazo definido (se existente), e se está dentro ou fora do SLA.
- **Red flags:** Inventa datas; "não tenho essa informação" sem explicar o motivo.
- **Observação:** _______________________________________________

**Q4.5 — Manutenção de contexto multi-turno dentro da vaga**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Envie: `Quem é o candidato mais avançado no pipeline?`
  2. Aguarde resposta (ex: "Maria Silva, na etapa de entrevista técnica").
  3. Envie: `Qual é o histórico de movimentações dela?`
- **Comportamento esperado:** "Dela" é corretamente referenciado à candidata mencionada anteriormente (Maria Silva).
- **Red flags:** Perde contexto e pergunta "de qual candidata?"; responde sobre candidato diferente.
- **Observação:** _______________________________________________

### Checklist de Regressão — Componente 4

| Item | Status | Observação |
|------|--------|------------|
| Prompt abre dentro do contexto da vaga | | |
| Endpoint `/orchestrator/process` chamado com context_id | | |
| Payload contém context_type e context_id corretos | | |
| Respostas são específicas à vaga aberta | | |
| Funciona em modo tabela e kanban | | |
| HITL ativo para ações no pipeline | | |
| Vaga sem candidatos tratada graciosamente | | |
| Contexto multi-turno mantido | | |
| Não inventa dados de candidatos | | |
| Respostas em português (pt-BR) | | |

---

## COMPONENTE 5 — Modal de Status da Vaga (Inferência de Substatus)

### Pré-condições
1. Navegar para a lista de vagas.
2. Identificar uma vaga ativa para teste de pausar/fechar, ou uma vaga pausada para reativar.
3. Localizar o controle de status da vaga (dropdown, botão de ação, ou ícone de opções).
4. Abrir DevTools > Network para monitorar requisições relacionadas à inferência de substatus.
5. Ter em mente as ações disponíveis: **Ativar, Pausar, Fechar**.

### Testes Funcionais

**T5.1 — Abertura do modal ao clicar em ação de status**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Na lista de vagas, localize uma vaga ativa.
  2. Clique na opção "Pausar Vaga" (ou equivalente no menu de ações).
  3. Verifique se um modal abre (não apenas uma confirmação direta).
  4. Verifique se o modal contém um campo para informar o motivo da pausa.
- **Critérios de sucesso:** Modal abre, campo de motivo presente, sem erros no console.
- **Observação:** _______________________________________________

**T5.2 — Inferência de substatus ao pausar vaga (PauseOptionsStep)**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. No modal de pause, insira no campo de motivo: `Precisamos pausar essa vaga porque o cliente congelou o budget`
  2. Observe se a IA infere automaticamente um substatus (ex: "Congelamento de Budget", "Decisão do Cliente", etc.).
  3. Verifique se o substatus inferido aparece destacado ou selecionado automaticamente.
  4. Confirme a pausa e verifique se o substatus correto foi aplicado.
- **Critérios de sucesso:** IA infere substatus correto a partir do texto; substatus aplicado na vaga.
- **Observação:** _______________________________________________

**T5.3 — Modal de ativação de vaga (ActivateOptionsStep)**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Localize uma vaga pausada.
  2. Clique em "Ativar Vaga".
  3. Verifique se o modal de ativação (ActivateOptionsStep) abre com opções relevantes.
  4. Selecione ou confirme as opções e ative a vaga.
  5. Confirme que o status da vaga mudou para ativa na lista.
- **Critérios de sucesso:** Modal de ativação funciona, vaga ativada com sucesso.
- **Observação:** _______________________________________________

**T5.4 — Fechamento de vaga com motivo**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Localize uma vaga ativa ou pausada para fechar.
  2. Selecione "Fechar Vaga".
  3. No modal, informe o motivo: `Vaga preenchida internamente após processo seletivo externo`
  4. Verifique se a IA infere substatus adequado (ex: "Preenchimento Interno", "Vaga Encerrada").
  5. Confirme o fechamento e verifique o status na lista.
- **Critérios de sucesso:** Substatus inferido corretamente, vaga fechada, status refletido na lista.
- **Observação:** _______________________________________________

**T5.5 — Cancelamento da ação no modal**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Inicie qualquer ação de status (pausar/fechar/ativar).
  2. No modal, clique em "Cancelar" ou feche o modal com X.
  3. Verifique se o status da vaga não foi alterado.
  4. Verifique se nenhuma requisição de mudança de status foi enviada.
- **Critérios de sucesso:** Cancelamento não altera o status; estado da vaga inalterado.
- **Observação:** _______________________________________________

**T5.6 — Substatus inválido ou não inferível**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. No modal de pause, insira um motivo vago ou sem contexto: `pausa`
  2. Verifique se a IA pede mais informações ou oferece uma lista de substatuses para seleção manual.
  3. Selecione manualmente um substatus e confirme.
- **Critérios de sucesso:** IA solicita esclarecimento ou oferece seleção manual; não aplica substatus genérico incorreto.
- **Observação:** _______________________________________________

### Testes de Qualidade de Resposta

**Q5.1 — Inferência de substatus: budget congelado**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Motivo informado:** `Precisamos pausar essa vaga porque o cliente congelou o budget`
- **Substatus esperado:** Algo equivalente a "Congelamento de Budget" / "Decisão Financeira do Cliente" / "Budget Hold"
- **Red flags:** Substatus genérico como "Outros"; substatus completamente incorreto (ex: "Candidato Desistiu").
- **Observação:** _______________________________________________

**Q5.2 — Inferência de substatus: posição eliminada**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Motivo informado:** `A área foi reestruturada e essa posição foi eliminada do organograma`
- **Substatus esperado:** Algo equivalente a "Reestruturação Organizacional" / "Posição Eliminada" / "Restructuring"
- **Red flags:** Substatus não reflete reestruturação; inferência em inglês quando plataforma está em português.
- **Observação:** _______________________________________________

**Q5.3 — Inferência de substatus: vaga preenchida por indicação**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Motivo informado:** `Fechamos com um candidato que veio por indicação interna, antes de terminar o processo externo`
- **Substatus esperado:** Algo equivalente a "Preenchida por Indicação" / "Contratação Interna" / "Referral Hire"
- **Red flags:** Substatus indica processo externo concluído quando na verdade foi interno.
- **Observação:** _______________________________________________

**Q5.4 — Consistência após múltiplas mudanças de status**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Pause uma vaga ativa com motivo.
  2. Reative essa mesma vaga.
  3. Pause novamente com motivo diferente.
  4. Verifique o histórico de status da vaga (se disponível) — deve refletir todas as mudanças com timestamps.
- **Comportamento esperado:** Cada mudança registrada corretamente; substatus específico a cada transição.
- **Red flags:** Histórico não atualiza; substatus do primeiro pause aparece no segundo.
- **Observação:** _______________________________________________

### Checklist de Regressão — Componente 5

| Item | Status | Observação |
|------|--------|------------|
| Modal abre ao acionar mudança de status | | |
| PauseOptionsStep exibe campo de motivo | | |
| ActivateOptionsStep exibe opções corretas | | |
| IA infere substatus a partir do texto do motivo | | |
| Substatus inferido é exibido antes de confirmar | | |
| Cancelamento não altera o status da vaga | | |
| Motivo vago solicita esclarecimento ou seleção manual | | |
| Status da vaga atualizado na lista após confirmação | | |
| Histórico de status registrado corretamente | | |
| Substatuses em português (pt-BR) | | |

---

## COMPONENTE 6 — Teams Analysis Panel (Painel de Análise de Entrevistas)

### Pré-condições
1. Navegar para a área de candidatos ou entrevistas onde o painel de análise de Teams está disponível.
2. Identificar um candidato que tenha uma transcrição de entrevista via Microsoft Teams disponível.
3. Abrir a seção de notas da entrevista (interview-notes) ou similar.
4. Confirmar que o componente `TeamsAnalysisPanel` está visível (pode estar como aba "Análise IA" ou painel lateral).
5. Abrir DevTools > Network para monitorar requisições a `*/api/lia/api/wsi/analyze-response*`.

### Testes Funcionais

**T6.1 — Painel de análise visível e botão "Analisar" disponível**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Abra o perfil de um candidato com entrevista Teams registrada.
  2. Navegue para a seção de notas ou entrevistas.
  3. Verifique se o `TeamsAnalysisPanel` está visível.
  4. Confirme que há um botão "Analisar" ou equivalente (correspondente ao prop `onAnalyze`).
- **Critérios de sucesso:** Painel visível, botão de análise habilitado, sem erros no console.
- **Observação:** _______________________________________________

**T6.2 — Execução da análise e chamada ao endpoint WSI**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Clique no botão "Analisar" no painel.
  2. Observe a aba Network — deve aparecer `POST /api/lia/api/wsi/analyze-response`.
  3. Aguarde a análise ser processada (pode levar 10–30 segundos para transcrições longas).
  4. Verifique se o resultado aparece no painel após o processamento.
- **Critérios de sucesso:** Endpoint chamado com sucesso (200), análise exibida após processamento.
- **Observação:** _______________________________________________

**T6.3 — Exibição do WSI Score**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Após a análise, verifique se um WSI Score é exibido no painel.
  2. Confirme que o score está em um formato compreensível (ex: número de 0 a 100, ou categoria como "Alto/Médio/Baixo").
  3. Verifique se há alguma explicação ou justificativa para o score atribuído.
- **Critérios de sucesso:** WSI Score visível, formato compreensível, com justificativa.
- **Red flags:** Score ausente após análise; score sempre o mesmo independente da transcrição.
- **Observação:** _______________________________________________

**T6.4 — Exibição do STAR Completeness**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Após a análise, verifique se há um indicador de "STAR Completeness" (Situação, Tarefa, Ação, Resultado).
  2. Confirme que o indicador diferencia quais elementos STAR foram identificados na transcrição.
  3. Verifique se há breakdown por pergunta ou por resposta do candidato.
- **Critérios de sucesso:** STAR Completeness exibida com detalhes por componente (S, T, A, R).
- **Red flags:** Indicador sempre "100% completo" independente da entrevista; breakdown ausente.
- **Observação:** _______________________________________________

**T6.5 — Exibição de Key Insights**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Após a análise, verifique se uma seção de "Key Insights" ou "Principais Insights" é exibida.
  2. Leia os insights e avalie se são específicos à transcrição analisada.
  3. Verifique se os insights mencionam competências e comportamentos observados na entrevista.
- **Critérios de sucesso:** Insights específicos e relevantes à transcrição; não são insights genéricos de template.
- **Red flags:** Insights genéricos que poderiam ser de qualquer entrevista; insights em inglês.
- **Observação:** _______________________________________________

**T6.6 — Análise de transcrição sem respostas suficientes (edge case)**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Se possível, acesse um candidato com transcrição muito curta ou incompleta (ex: entrevista interrompida).
  2. Execute a análise.
  3. Verifique se o painel informa que a transcrição é insuficiente para análise completa.
- **Critérios de sucesso:** Mensagem informativa sobre transcrição incompleta; não gera análise falsa.
- **Observação:** _______________________________________________

**T6.7 — Re-análise (executar análise múltiplas vezes)**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Execute a análise de uma transcrição.
  2. Aguarde o resultado.
  3. Clique em "Analisar" novamente (re-análise).
  4. Verifique se o resultado é consistente com a primeira análise (pode ter pequenas variações por LLM, mas não deve ser drasticamente diferente).
- **Critérios de sucesso:** Re-análise funciona sem erro; resultados consistentes entre execuções.
- **Observação:** _______________________________________________

### Testes de Qualidade de Resposta

**Q6.1 — Relevância dos insights ao cargo**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Cenário:** Analisar transcrição de entrevista para vaga de Engenheiro de Software.
- **Comportamento esperado:** Key Insights mencionam competências técnicas observadas (ou ausentes), capacidade de resolução de problemas, comunicação técnica. Não menciona "habilidades de vendas" ou competências irrelevantes.
- **Red flags:** Insights genéricos de "bom profissional"; competências irrelevantes ao cargo mencionadas.
- **Observação:** _______________________________________________

**Q6.2 — STAR Completeness diferenciado entre candidatos**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:**
  1. Analise a transcrição de um candidato que deu respostas detalhadas (com contexto, ação e resultado claros).
  2. Analise a transcrição de um candidato que deu respostas vagas.
  3. Compare os scores de STAR Completeness.
- **Comportamento esperado:** Candidato com respostas detalhadas deve ter STAR Completeness mais alto. Candidato com respostas vagas deve ter STAR incompleto (falta de R — Resultado, por exemplo).
- **Red flags:** Ambos com mesmo score; candidato com respostas vagas recebe STAR 100%.
- **Observação:** _______________________________________________

**Q6.3 — WSI Score proporcional à qualidade das respostas**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Cenário:** Compare WSI Score de dois candidatos:
  - Candidato A: respondeu todas as perguntas com exemplos concretos e resultados mensuráveis.
  - Candidato B: respondeu superficialmente com respostas evasivas.
- **Comportamento esperado:** WSI Score do candidato A deve ser significativamente maior.
- **Red flags:** Scores iguais ou invertidos; score não diferencia qualidade das respostas.
- **Observação:** _______________________________________________

**Q6.4 — Insights não inventam informações ausentes na transcrição**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Cenário:** Analisar transcrição onde o candidato não foi perguntado sobre liderança de times.
- **Comportamento esperado:** Insights NÃO devem mencionar "capacidade de liderança" como observada, pois o tema não foi abordado na entrevista.
- **Red flags:** IA inventa competências não avaliadas na entrevista ("demonstrou excelente liderança" quando o tema nunca foi abordado).
- **Observação:** _______________________________________________

**Q6.5 — Idioma e qualidade dos textos gerados**
- **Resultado esperado:** [ ] ✅ PASSOU / [ ] ❌ FALHOU / [ ] ⚠️ PARCIAL
- **Passos:** Após qualquer análise, leia os insights gerados e verifique:
  1. Estão em português (pt-BR)?
  2. Gramaticalmente corretos?
  3. Linguagem profissional e adequada ao contexto de RH?
  4. Sem termos técnicos de IA expostos (ex: "token", "embedding", "hallucination")?
- **Comportamento esperado:** Insights em português, gramática correta, linguagem de RH profissional.
- **Red flags:** Insights em inglês; mistura de idiomas; termos técnicos de IA expostos ao usuário.
- **Observação:** _______________________________________________

### Checklist de Regressão — Componente 6

| Item | Status | Observação |
|------|--------|------------|
| TeamsAnalysisPanel visível no perfil do candidato | | |
| Botão "Analisar" habilitado com transcrição disponível | | |
| Endpoint `/api/lia/api/wsi/analyze-response` chamado | | |
| Análise processada em tempo razoável (< 60s) | | |
| WSI Score exibido com justificativa | | |
| STAR Completeness com breakdown por componente | | |
| Key Insights específicos à transcrição | | |
| Transcrição insuficiente tratada com mensagem informativa | | |
| Re-análise funciona sem erro | | |
| Scores diferenciam qualidade de candidatos | | |
| Insights em português (pt-BR) sem alucinação | | |

---

## Resumo de Resultados

Preencher ao final da execução completa do smoke test.

| Componente | Total de Testes | ✅ Passou | ❌ Falhou | ⚠️ Parcial | % Aprovação |
|------------|----------------|-----------|-----------|------------|-------------|
| C1 — LIA Float | 12 | | | | |
| C2 — Expandable AI Prompt | 13 | | | | |
| C3 — Expanded Chat (Wizard) | 13 | | | | |
| C4 — Prompt Dentro da Vaga | 10 | | | | |
| C5 — Modal de Status | 10 | | | | |
| C6 — Teams Analysis Panel | 12 | | | | |
| **TOTAL** | **70** | | | | |

### Componentes Críticos com Falha (preencher após execução)

| Componente | Teste | Falha Observada | Severidade |
|------------|-------|-----------------|------------|
| | | | |
| | | | |

---

## Classificação de Severidade

Use esta tabela para classificar os problemas encontrados durante o smoke test:

| Nível | Nome | Definição | Exemplos | Ação Recomendada |
|-------|------|-----------|----------|------------------|
| **P0** | Crítico | Componente completamente inutilizável. Bloqueia o uso da funcionalidade principal. | Painel não abre; API retorna 500 em todas as requisições; autenticação falha (401); crash da página. | Bloquear deploy. Corrigir antes de qualquer release. Notificar equipe imediatamente. |
| **P1** | Alto | Funcionalidade principal funciona mas com falha grave em um caso de uso chave. | Streaming quebrado (usuário precisa aguardar resposta completa); HITL não aparece para ações destrutivas; substatus nunca inferido; dados inventados. | Corrigir antes do próximo sprint. Não colocar em produção sem correção. |
| **P2** | Médio | Funcionalidade funciona mas com degradação perceptível ou comportamento inesperado não crítico. | Resposta em inglês em vez de português; lentidão acima de 15 segundos; re-análise gera resultados muito divergentes; um dos 6 modos de busca não funciona. | Planejar correção para o próximo sprint. Pode ir para produção com workaround documentado. |
| **P3** | Baixo | Problema cosmético ou de usabilidade sem impacto funcional. | Texto mal formatado na resposta; ícone errado no painel; mensagem de loading desaparece antes da resposta aparecer; tooltip incorreto. | Backlog. Corrigir quando houver capacidade. |

### Critérios de Go/No-Go

- **Go (aprovado para produção):** Todos os testes P0 passando; máximo 2 falhas P1 com workaround documentado.
- **No-Go (bloquear deploy):** Qualquer falha P0; 3 ou mais falhas P1 sem workaround.
- **Go Condicional:** 1–2 falhas P1 com workaround claro e aprovação do PO.

---

*Documento gerado para uso interno da equipe de QA — Plataforma LIA*
*Versão 1.0 — 2026-04-03*
