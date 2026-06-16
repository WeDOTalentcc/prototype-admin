F1

Sub-etapa
O que temos
O que não temos (vs WSI)
O que precisaríamos alterar
F1.A — Preenchimento do JD
Job com título, descrição, senioridade, responsibilities, skills e competências via relacionamentos; field_requirements para completude de publicação.
Regras WSI explícitas no backend (ex.: tamanho mínimo de responsabilidades, mínimos de skills técnicas/comportamentais) como contrato do pipeline F1.
Decidir validação API vs só UI; alinhar estrutura de dados do job ao que F1.B/F1.C esperam.
F1.B — Score determinístico 0–100
Nada equivalente (sem score nem 9 dimensões pré-LLM).
Cálculo antes do LLM; faixas (&lt;30 bloqueio, 30–49 alerta, ≥50 seguir, etc.).
Serviço determinístico + persistência (ex. jsonb com breakdown) + specs table-driven + endpoint de leitura.
F1.C — LLM enriquece o JD
JobSuggestionService usa LLM com ângulo WSI para sugestões de conteúdo.
Passo obrigatório do fluxo de vaga com JSON canônico (enriched_jd, context_signals, quality_report, etc.).
Add novo campo lia_job_description em Job.
Serviço dedicado, schema versionado, armazenamento de rascunho até aprovação humana.
F1.D — Lado a lado + painel
API serializa o job; comparação visual é front.
Painel com F1.B + relatório de qualidade acoplado ao contrato WSI.
Contratos JSON estáveis; opcional endpoint de “preview” sem tornar o JD oficial.
Task front para conseguir gerar o novo lia_job_description e exibir as métricas do description.
F1.E — Aprovar / editar / rejeitar
Publicação e edição de vaga existem.
Estado obrigatório “enriquecimento aprovado antes de F2/F6”; rejeitar redispara F1.B.
Estados/campos na Job (ou agregado), regras que bloqueiam Bloco A sem aprovação, auditoria.

Parecer: Na metodologia, a F1 é o gate de qualidade e governança antes de qualquer extração Big Five ou geração de perguntas. No Rails temos vaga + LLM de sugestão, mas não o pipeline fechado F1.B → F1.C → revisão humana → persistência como fonte de verdade. O caminho mais seguro é começar por F1.B + persistência + API e só depois amarrar F1.C–E e bloqueios para o restante do Bloco A.Quando quiser, fazemos o mesmo formato para F2.

---

F2
Frente
O que temos hoje (ats_api)
O que não temos (vs F2.5 no doc)
O que precisaríamos alterar / criar
Extração LLM (F2.5)
O LLM em JobSuggestionService gera perguntas e pode atribuir ocean_trait por pergunta a partir do contexto da vaga.
Passo dedicado só para extrair o perfil OCEAN do JD: rubric NEO-PI-R, temperature ≈ 0.1, max_tokens ~ 800, saída estruturada por trait com score, evidências (citações literais) e confidence (high / medium / low).
Serviço único (ex. Wsi::JdBigFiveExtractionService), contrato JSON versionado, persistência, testes com stub do LLM.
Artefato persistido na vaga
Nenhum campo agregando o resultado da F2.5 para a Job.
JSON canônico dos 5 traits consumível por F3 / F5 / F9 sem depender das perguntas já geradas.
Migration (jsonb na jobs ou tabela associada) + leitura/escrita + extracted_at / versão do método.
Entrada do LLM
Texto livre da vaga (description, skills, etc.).
Texto preferencialmente limpo pós-F1 (about_role + responsabilidades do enriched_jd aprovado), mais lista de competências comportamentais com trait_big_five quando existir.
Acoplar à F1 quando existir; ou documentar modo “degradado” só com JD atual até F1 existir.
Taxonomia OCEAN
Prompts de geração usam neuroticism em alguns pontos; o doc fala em estabilidade (N invertido) em outros trechos.
Um contrato único entre extração F2.5, perguntas, scoring e relatórios.
Enum estável + regra de mapeamento (ex. N vs “stability”) documentada na API.
Auditabilidade
Evidências do “perfil da vaga” não ficam armazenadas de forma explícita.
Citações literais do JD por trait (requisito citado no doc para rastreabilidade).
Incluir evidence (ou equivalente) no schema persistido e validar no prompt.
Parecer (só Abordagem C): O escopo fica só F2.5: um único motor LLM com rubric, baixa temperatura e saída estruturada persistida na vaga. O gap principal deixa de ser “implementar A e B” e passa a ser (1) serviço + persistência F2.5, (2) alinhamento de entrada com F1 quando houver, (3) normalização OCEAN e evidências para F3 em diante.

---

Segue a Fase 3 no mesmo estilo das anteriores, alinhada ao doc (§3.x, ~887–989) e ao que o ats_api faz hoje — com só Abordagem C na F2: o ranking é ordenar os 5 traits pelo score do LLM (F2.5) e cortar Top-N; a fórmula 0.40×C + 0.35×B + 0.25×A e o boost por senioridade (§3.2) ficam fora do escopo até existirem A/B ou decisão explícita de produto.

F3 — Ranking ponderado de traits
Frente
O que temos hoje (ats_api)
O que não temos (vs metodologia)
O que precisaríamos alterar / criar
Entrada (saída da F2)
Ainda sem perfil Big Five persistido por vaga (F2.5).
Lista dos 5 traits com score (e idealmente evidência/confidence) vinda só do LLM.
Depende da F2.5 persistida; F3 só consome esse JSON.
Ranking determinístico
Nenhum serviço que ordene traits por score e produza rank 1..5.
ranked = sort por score decrescente como no pseudo-código do doc (equivalente a score_final = score_C).
Serviço puro (ex. Wsi::TraitRankingService) + specs com fixtures de scores.
Top-N por senioridade e modo
Job tem seniority (índice + Job::SENIORITY), mas não há mapa senioridade → N traits nem distinção Compact vs Full para Big Five.
Constante tipo SENIORITY_BIGFIVE_TOP_N: quantos traits entram em perguntas (doc cita mapa por nível; default 3 se ausente no exemplo Python).
Tabela/código de config (YAML ou constante) alinhada ao wsi_constants do doc; testes por senioridade.
weight_normalized (pré-F9)
EvaluationAggregateService usa média simples do bloco comportamental, sem pesos por trait ( split_scores_by_competence + average).
Para traits selecionados (Top-N): weight_normalized = score / soma(scores do Top-N) (doc §3.4; uso pleno na F9).
Persistir ranking + pesos na vaga (ou derivar de F2+F3 em runtime) e alterar agregação quando F9 for paritar o doc.
Output estruturado
Nada persistido no formato big_five_ranking + metadados.
JSON com rank, trait, score_final (aqui = score C), opcionalmente scores_by_approach só com ramo C_llm se quiserem audit trail.
Campo jsonb na Job (ou snapshot em Evaluation) + contrato versionado.
Boost por senioridade (§3.2)
Não aplicável no mesmo desenho do doc enquanto só existir C — a própria metodologia v2 diz que esse boost não está implementado na referência por falta de base A/B.
Ajuste fino de scores por nível (ex. +8 em Estabilidade para Senior).
Opcional: implementar só com C com cuidado (doc alerta risco de calibração); ou deixar explícito “fora de escopo” até F2/F3 estarem estáveis.

Parecer (F3)
A F3, no recorte só Abordagem C, é essencialmente determinística sobre números já produzidos pelo LLM na F2.5: ordenar, cortar Top-N conforme senioridade (e, se o produto exigir, modo Compact/Full), e expor rank + scores + pesos normalizados para F5 (quantas perguntas por trait) e F9 (média comportamental ponderada). No Rails isso ainda não existe como pipeline; o que há hoje é agregação sem pesos por trait.Ordem sugerida: implementar F2.5 persistida → F3 (sort + Top-N + persistência) → só então F5 e refino da F9.

---

F4 — Senioridade: definição e calibração
Frente
O que temos hoje (ats_api)
O que não temos (vs metodologia)
O que precisaríamos alterar / criar
Senioridade explícita (recrutador)
Campo jobs.seniority (inteiro) com rótulos em (Júnior, Pleno, Sênior, Especialista, Estágio, Lead, Gerente, Diretor).
Cobertura 1:1 com o enums do doc (ex.: Estagiário, Junior, Pleno, Senior, Lead/Principal, Diretor, VP/C-Level — “Principal” e “VP/C-Level” não existem como níveis próprios).
Mapa explícito índice ATS ↔ nível WSI (ou ampliar enum) para F3/F5/F9 usarem a mesma chave que SENIORITY_BIGFIVE_TOP_N / tabelas do doc.
Inferência multi-sinal (sem LLM)
Não há resolve_seniority_full() equivalente: título, texto do JD, faixa salarial, complexidade de skills com pesos fixos (doc: explicit 0.50, title 0.25, jd 0.25, salary 0.15, skills 0.10).
Sugestão automática + nível de confiança quando o recrutador não preencheu senioridade.
Serviço determinístico + specs (fixtures de job com título/salário/skills); opcional persistir suggested_seniority, seniority_confidence, seniority_source.
Regras por título (§4.2)
Não centralizado no backend como tabela de keywords → nível WSI.
Matriz do doc (Trainee→Estagiário, Jr→Junior, “Analista” sem qualificador→Pleno baixa confiança, etc.).
Implementar como constante + testes; integrar ao resolver.
Confirmação / override humano
Recrutador pode editar seniority no job; não há fluxo “sistema sugeriu X — confirmar?” nem auditoria de mudança motivada por WSI.
Doc: senioridade inferida deve ser confirmada ou ajustada na F1.
UX + API (ex.: seniority_resolved_at, seniority_user_overridden) se o produto exigir rastreio WSI.
Calibração Bloom / Dreyfus esperados (§4.1)
Question tem dreyfus_target e bloom_level por pergunta, em geral vindos do LLM na geração 1.
Tabela única “senioridade → Dreyfus técnico, Bloom esperado, Dreyfus comportamental” como fonte de verdade compartilhada por F4, F5 e avaliação (como no Python wsi_deterministic_scorer).
Constantes ou config versionada + validação/alinhamento das perguntas geradas a esses alvos (ou pós-processamento).
Uso em scoring agregado
aplica SENIORITY_WEIGHTS com chave job.seniority.to_s.downcase — na prática costuma ser "0".."7" (string numérica), caindo no default pleno salvo wsi_scoring customizado por conta.
Chaves semânticas (junior, senior, …) alinhadas ao nível WSI da vaga.
Corrigir mapeamento índice → chave usada em seniority_multiplier (e em futuras F4/F5), para pesos refletirem a senioridade real.

Parecer (F4)
No doc, a F4 é dois movimentos: (1) definir senioridade (explícita ou inferida com confiança e confirmação), (2) calibrar expectativas (Bloom/Dreyfus) que alimentam geração de perguntas e leitura dos resultados. No ats_api já existe escolha manual de senioridade e uso indireto em prompts e agregação, mas falta o resolver determinístico, a matriz canônica §4.1 como contrato único e um mapeamento índice ↔ nível WSI — hoje o agregador pode estar usando sempre o fallback pleno por causa de seniority.to_s.downcase numérico.Ordem sugerida: alinhar mapeamento senioridade + fix seniority_multiplier → tabela §4.1 em código → resolver + confirmação se o produto quiser sugestão automática.

---

F5 — Distribuição de perguntas por senioridade e modo
Frente
O que temos hoje (ats_api)
O que não temos (vs metodologia)
O que precisaríamos alterar / criar
Modos Compact / Full
WSI Compact: 6–8 perguntas; WSI Compact+: 8–10 1. Modo “query”: 1 pergunta.
Compact = 7 e Full = 12 fixos no doc, com tabelas distintas por senioridade (§5.3–5.5).
Definir produto: alinhar nomes/contagens ao doc ou documentar desvio; se Full 12 for obrigatório, novo wsi_type + motor de distribuição.
Razão técnica × comportamental por senioridade
Prompt fixa 70% técnico / 30% comportamental e sugere até 7 competências (5 técnicas + 2 comportamentais) — não varia com senioridade.
Tabelas adaptativas (ex.: Estagiário–Pleno Compact 5T+2B; Lead 3T+4B; VP Compact 2T+5B — §5.4). Full com 9+3 até 7+5 conforme nível (§5.5).
Serviço determinístico que, dado seniority + mode, devolve T, B, Top-N traits; o prompt/gerador consome esse mapa em vez de 70/30 fixo.
Alinhamento com peso de scoring (§5.1, §5.6)
Agregação usa macro_distribution (default 70/30) e SENIORITY_WEIGHTS em — números diferentes dos pesos normalizados do doc (ex.: Senior doc 56.25% / 43.75% técnico/comportamental na §5.6).
Princípio doc: proporção de perguntas ≈ peso no score por senioridade; tabela §5.6 (e elegibilidade 20% quando existir bloco).
Unificar fonte de verdade: constantes compartilhadas entre F5 (contagens) e F9 (pesos); opcionalmente incorporar fatia de elegibilidade quando G1 existir.
Top-N traits (ligação F3 → F5)
O LLM escolhe ocean_trait por pergunta; não há corte explícito “só top-2/3/4/5” a partir do ranking F3.
Doc §5.4–5.5 e §5.7: quantidade de comportamentais e Top-N ligados ao ranking F3.
Após F3 persistida, passar lista de traits selecionados ao gerador; validar pós-LLM que cada pergunta comportamental mapeia a um trait do Top-N.
Seleção de skills técnicas (§5.7)
Skills vêm do contexto da vaga; importance_score / ordem explícita tipo wizard não está acoplada ao gerador como regra determinística.
Ordenar por importance_score; se faltar ranking, ordem do recrutador; se menos skills que T, distribuir múltiplas perguntas por skill com Bloom distinto (§5.7).
Contrato de entrada (skills ranqueadas) + algoritmo de alocação antes do LLM (ou validação depois).
Alocação intra-framework (§5.8)
Não há decomposição determinística Dreyfus / Bloom / CBI tech / CBI behav / BigFive por contagem T e B (tabelas de fórmulas do doc).
generate_all() no Python com exemplos verificados Junior compact, Senior compact, etc.
Portar fórmulas §5.8 para Ruby (ou lib compartilhada) e usar como plano que o LLM preenche pergunta a pergunta, ou gerar slots e depois LLM por slot.
Config por conta
wsi_scoring em sourcing_config altera macro e pesos de senioridade no agregador.
Distribuição F5 canônica por senioridade/modo como default; overrides conscientes.
Estender config tipada (ex.: wsi_question_distribution) se precisarem flexibilidade tenant sem quebrar paridade metodológica.

Parecer (F5)
No doc, a F5 é um motor tabular + fórmulas: contagens T/B, Top-N do F3 e fatias por framework batem com os pesos do score final por senioridade. No ats_api, a distribuição é em grande parte heurística no prompt (70/30, 6–10 perguntas) e não reproduz as tabelas §5.4–5.5 nem a §5.8 — logo, candidatos de Lead/VP podem receber a mesma mistura que Júnior/Pleno, e o agregador usa outra lógica de pesos que a §5.6.Ordem sugerida: consolidar mapeamento senioridade WSI (F4) → implementar QuestionDistributionService (saída: T, B, Top-N, breakdown §5.8) → ajustar JobSuggestionService para consumir esse plano → alinhar EvaluationAggregateService aos pesos §5.6 (ou documentar desvio aceito).

---

F6 — Geração de perguntas por LLM
Frente
O que temos hoje (ats_api)
O que não temos (vs metodologia)
O que precisaríamos alterar / criar
Princípio “sem banco fixo”
Perguntas geradas sob demanda via LLM e persistidas em questions (opcionalmente ao gerar para uma Evaluation).
Mesmo princípio no doc (§6.1).
Manter; reforçar política de não usar biblioteca estática de templates.
Geração por slot (skill / trait)
Uma chamada LLM devolve todas as perguntas em um único JSON (lote).
Referência Python: geração por pergunta (ou por tipo) com temperaturas distintas — técnica 0.7, comportamental ~0.75, Big Five ~0.8 (§6 cabeçalho).
Ou alinhar produto ao lote único documentando desvio, ou orquestrar N chamadas conforme plano F5 (T/B + frameworks).
Calibração Bloom / Dreyfus (§6.2–6.4)
Prompt pede dreyfus_target e bloom_level “baseado na senioridade”; não amarra a tabelas F4 canônicas nem valida pós-geração contra elas.
Mapas explícitos senioridade → Bloom/Dreyfus (técnico e comportamental) e regras de formulação por nível.
Após F4 tabular: passar alvos explícitos por slot + validação (rejeitar/regenerar se fora do intervalo esperado).
F6.5 — Prompt técnico (CBI, fairness, skill rara)
Prompt geral WSI cobre CBI/Bloom/Dreyfus e boas práticas; não reproduz o SYSTEM/USER longo da §6.5 (proibições de rubric na pergunta, [SKILL_APPROXIMATED:], etc.).
Checklist §6.5 (fairness, aberta, não hipotética, skill proprietária).
Prompt(s) dedicados por tipo técnico + tratamento de skill aproximada + metadados (\_skill_approximated).
F6.6 — Comportamental + trait-affinity
LLM escolhe ocean_trait no lote; não há _select_comp_by_trait() a partir do ranking F3 + trait_big_five do enriched_jd (doc §6.6, bridge F1).
Uma pergunta comportamental por trait alvo do Top-N; cenários ativadores por trait; regras de alto risco de viés (A, N↓, E).
Implementar seleção determinística da competência/trait antes da chamada LLM; prompt comportamental alinhado à §6.6.
Validação automática (F6.8 / F6.8.1)
Controller normaliza framework_weights, validation_type_weight, category; não há checagens determinísticas do doc (ex.: 15–80 palavras, verbo no passado, sem “imagine que”, etc.) nem segunda passagem LLM de validação citada no checklist.
Pipeline “validação determinística → opcional LLM validador → regenerar até 3× → needs_manual_review”.
Módulo QuestionValidation + contador de retries + flags na pergunta ou evaluation.
Revisão humana obrigatória (§6.7 / crença #01)
Recrutador pode editar perguntas na UI (fora do escopo detalhado aqui); não há no backend gate explícito reviewed_by_recruiter / bloqueio de uso em triagem sem revisão.
Aprovação explícita antes de “ativar” perguntas para candidatos.
Estados em Evaluation/Question + política ao iniciar triagem (F7).
Metadados de persistência (§6.7 checklist)
Question guarda título, tipos, bloom, dreyfus, ocean_trait, framework, weights, etc.
Metadados extras: reviewed_by_recruiter, needs_manual_review, tentativas de geração, skill associada explícita, flags de aproximação.
Extensão de schema ou jsonb wsi_metadata + serializers.
Integração F5 → F6
Contagem vem do intervalo min/max do tipo WSI no prompt, não do plano T/B/Top-N do doc.
Gerar exatamente o número e o tipo de slots que F5 definiu (incl. alocação intra-framework §5.8).
F5 como pré-requisito: F6 só “preenche” slots planejados.

Parecer (F6)
No doc, a F6 é geração guiada por slots (uma skill / um trait por vez), com prompts e temperaturas específicos, validação automática forte e revisão humana antes de publicar. No ats_api, o fluxo é mais simples e barato: uma chamada LLM em lote com um super-prompt, normalização de campos no controller e sem trait-affinity determinística, sem validação F6.8 explícita e sem trava formal de governança no modelo.Ordem sugerida: estabilizar F5 (plano de slots) → F6.6 (escolha de trait/competência por F3+F1) → prompts F6.5/F6.6 alinhados ao doc → F6.8 + retries → revisão obrigatória se o produto exigir paridade com a metodologia.

---

F7 — Coleta das respostas (fluxo conversacional)
Frente
O que temos hoje (ats_api)
O que não temos (vs metodologia)
O que precisaríamos alterar / criar
Canais (chat / WhatsApp)
Avaliação com chatbot interno ou WhatsApp (Evaluation + chatbot_channel); Answer com source (internal, whatsapp, voice).
Referência Python também cita portal síncrono (LangGraph) e voz (E3) como irmãos do mesmo contrato WSI.
Se a paridade for estrita: alinhar contrato de eventos/mensagens ao state machine do doc; voz já existe como SOURCE_VOICE — validar se cobre o mesmo fluxo F7.
Sequência e ordem
questions.position na avaliação — permite ordem fixa por vaga/avaliação.
Doc: ordem definida na criação, igual para todos os candidatos.
Garantir que UI/agente sempre respeite position e que não haja randomização por sessão.
Fluxo técnico: autodeclaração 1–5 + texto
A autodeclaração usada no score vem sobretudo de comments_response da IA (campo score / aninhado), interpretada em .
Doc §7.1–7.2: passo explícito antes da pergunta técnica — escala 1–5 com rótulos fixos (Nunca usei … Especialista), depois pergunta, depois texto livre; autodeclaração com peso 35% na fórmula técnica do doc (F8).
Modelar dois eventos (ou choices estruturados) por pergunta técnica: valor 1–5 persistido de forma independente do texto; copiar rótulos §7.2; alinhar F8 aos pesos do doc se necessário.
Fluxo comportamental
Mesma conversa: candidato responde em texto; rounds em choices.
Doc: sem autodeclaração — só texto livre.
Em geral já compatível; validar que o agente não exige escala onde competence_type é comportamental.
Perguntas de elegibilidade (binárias)
Não há tipo elegibilidade Sim/Não no modelo Question como no doc (G1).
Bloco de elegibilidade com respostas Sim/Não antes/paralelo ao fluxo principal.
Novo response_type ou flag + fluxo de coleta + uso em F10 G1.
Imutabilidade após envio
Depende do produto (API update em respostas públicas pode existir).
Doc §7.3: edição não permitida após envio.
Regra no controller/policy: bloquear update de description/choices após estado “submetido”.
Timeout / mínimo de palavras
Configurações de screening no job (screening_timeout, etc.) — não necessariamente = “sem timeout por pergunta” do doc.
Doc: sem timeout por pergunta; sem bloqueio por mínimo de palavras (penalização na F8).
Documentar desvio ou alinhar política de timeout ao WSI.
Hash SHA-256 das respostas brutas
Não há campo em Answer / EvaluationCandidate com hash do conjunto de respostas ao fim da triagem (doc §7.1, §7.3, relatório F11).
Integridade e auditoria (LGPD / AI Act no texto do doc).
Ao concluir triagem: canonicalizar payload (ordem, normalização de Unicode/espacos), Digest::SHA256.hexdigest, persistir em evaluation_candidates ou tabela de auditoria.
Orquestração conversacional

- follow-ups no choices; não é LangGraph.
  WSIInterviewGraph no Python como referência de estágios.
  Só necessário se quiser paridade de máquina de estados; senão, manter Rails mas documentar equivalência de estágios.

Parecer (F7)
No doc, a F7 é coleta determinística e auditável: fluxos distintos para técnico (escala + texto), comportamental (só texto), elegibilidade (binária), ordem fixa, sem edição, e hash ao final. No ats_api, a base está boa (web/WhatsApp/voz, position, Answer + rounds), mas a autodeclaração não está garantida como passo de produto isolado com copy §7.2 — ela aparece sobretudo via JSON da IA. Elegibilidade e SHA-256 são os gaps mais claros para paridade WSI e para F10/F11.Ordem sugerida: definir contrato de autodeclaração persistida por pergunta técnica → hash ao completar EvaluationCandidate → perguntas de elegibilidade se G1 for prioridade.

---

F8 — Avaliação das respostas (camadas) 
O doc descreve três camadas de processamento + persistência do score por pergunta 0–10; o título fala em “4 camadas” (na prática: estrutural → extrator → fórmula → materialização do resultado). 

Frente 
O que temos hoje (ats*api) 
O que não temos (vs metodologia) 
O que precisaríamos alterar / criar 
Camada 1 — Determinístico (STAR + ajustes) 
e afins produzem sinais tipo STAR/completude; há penalidades e bônus (score_inflation, generic_response, lack_of_context, etc.) com valores próprios (ex. 1.0, 0.5). 
Tabela §8.2: pesos S 20% / T 20% / A 40% / R 20%; penalidades por faixa de palavras (−2.5 &lt;30, −1.0 30–50), sem 1ª pessoa (−1.5), R ausente (−0.8), paráfrase da pergunta (−2.0), idioma (−1.0), injeção → override; bônus por métrica quantificada, texto longo, múltiplos episódios. 
Ou portar as regras §8.2 para um módulo dedicado, ou documentar desvio aceito; alinhar nomes e gatilhos com F10 (G5/G6) e relatório. 
Camada 2 — LLM só extrator (temp = 0) 
O JSON da IA em comments_response é usado principalmente para score / satisfatoriedade / follow-up no fluxo conversacional; Bloom e Dreyfus “demonstrados” vêm em grande parte de classificadores locais no texto (BloomClassifier, DreyfusScorer, BigFiveAnalyzer). 
Contrato §8.3: LLM não dá nota; retorna star_components, bloom_demonstrated 1–6, dreyfus_demonstrated 1–5, trait_signals*\*, inflation_detected, specificity_score, key_quote, response_authentic, tratamento elegibilidade / injeção / idioma. 
Nova etapa (ou substituição): chamada temperature 0.0, max_tokens ~800, schema fixo; classificadores locais só como fallback ou validação cruzada, conforme produto. 
Camada 3 — Fórmula por tipo de pergunta 
Fórmula atual: base_score = 0.6×autodeclaração + 0.4×contexto; depois 0.6×base + 0.4×framework_score menos penalidades/bônus; escala 0–5 em final_skill_score. 
Doc §1895–1896: técnico 0.35×autodeclaração + 0.40×evidências_técnicas + 0.25×alinhamento Bloom; comportamental 0.35×STAR + 0.40×sinais_trait + 0.25×alinhamento Bloom; score por pergunta 0–10 persistido. 
Serviço de scoring que consuma saída Camada 1 + JSON Camada 2; decidir mapeamento 0–10 ↔ 0–5 no agregado (hoje o candidato usa score = wsi×2 em EvaluationAggregateService). 
Escala Bloom demonstrado 
Classificador local alinhado a níveis do tipo remember/create (5 níveis no prompt de geração). 
Extração com Bloom 1–6 (incl. Avaliar/Criar conforme §8.3). 
Alinhar taxonomia e parser ao doc se a Camada 2 for LLM-first. 
Perguntas de elegibilidade 
Fluxo genérico de resposta; sem question_category: eligibility nem JSON com campos null como no doc. 
Pass/fail na coleta + extrator sem Bloom/Dreyfus. 
Estender modelo/prompt quando F7/F10 de elegibilidade existirem. 
PII, auditoria e injeção 
Não há, no trecho central do Rails citado, máscara obrigatória de PII antes do LLM nem log com hash da resposta em claro conforme checklist §8.3. 
Máscara pré-envio; prompt_injection / response_authentic; rastreio para G2. 
Pipeline de pré-processamento + contadores de reincidência por candidato. 
Separação “extrator vs avaliador” 
A mesma resposta da IA pode conter campos interpretados como avaliação (ex. score) enquanto o backend também recalcula nota com regras determinísticas. 
Princípio WSI: nota final só na Camada 3, a partir de fatos extraídos. 
Contrato explícito com o agente: JSON sem nota final ou ignorar nota se houver duplicação. 

 
Parecer (F8) 
A divergência central é arquitetural: a metodologia separa (1) regras estruturais fixas, (2) LLM apenas extrator com temp 0, (3) fórmula fixa e auditável com pesos diferentes para técnico vs comportamental e 0–10 por pergunta. No ats_api, predomina o modelo híbrido: classificadores locais no texto + autodeclaração vinda do JSON da IA + fórmula 0–5 com pesos 0.6/0.4 que não coincidem com o doc.
Ordem sugerida: congelar contrato JSON da Camada 2 (alinhado a §8.3) → implementar Camada 3 conforme §1895–1896 (ou documentar deltas) → realinhar Camada 1 à §8.2 onde impactar gates e relatório → só então ajustar F9 para a mesma escala. 

---

F9 — Score WSI final: composição e classificação
Frente
O que temos hoje (ats_api)
O que não temos (vs metodologia)
O que precisaríamos alterar / criar
WSI_tecnico
Média simples dos final_skill_score das respostas com competence_type ≠ comportamental (split_scores_by_competence + average).
Doc §9.1: média simples dos scores técnicos no mesmo modelo de escala que a F8 (pergunta 0–10 no doc).
Garantir que final_skill_score esteja na mesma escala que a fórmula F8; senão normalizar antes da média.
WSI_comportamental
Média simples das respostas comportamentais — sem pesos por trait.
Doc §9.1: soma ponderada — cada pergunta i pesa trait_i.score_final / soma(scores dos top-N do JD) (F3); só entram traits que tiveram pergunta.
Persistir ranking F3 na vaga; em cada Question comportamental, ligar ao trait; agregador usa weight_normalized.
Bloco elegibilidade
Não existe WSI_elegibilidade nem fatia 20% no agregador.
Doc §9.1 / §9.3: se houver elegibilidade, 0,8× nos pesos técnico/comportamental + 20% elegibilidade (G1 manda na reprovação).
Por enquanto vamos adiar o bloco de elegibilidade.
WSI final (fórmula)
macro_score = média_téc × wT + média_comp × wB com wT/wB default 70/30 (macro_distribution_weights), depois macro_score \* seniority_multiplier, onde o multiplicador deriva de technical + behavioral em SENIORITY_WEIGHTS com heurística /0,80 — não é a soma ponderada explícita do doc.
Doc §9.3: WSI_final = WSI_tec×peso_tech + WSI_comp×peso_comp [+ WSI_elig×0,20] com SENIORITY_WEIGHTS fixos por chave (estagiario … vp_clevel, §9.2).
Substituir por composição linear explícita; alinhar chaves ao mapa F4; remover ou justificar o seniority_multiplier atual.
Pesos por senioridade (§9.2)
SENIORITY_WEIGHTS no Rails usa junior, pleno, senior, lead, manager com valores diferentes dos do doc (ex.: doc Lead 43,75% / 56,25%; Rails lead 35% / 35% + experience + cultural).
Dict §9.2 (8 níveis) + opcional eligibility 20%.
Portar tabela ou config; mapear Job::SENIORITY → chave WSI; decidir o que fazer com experience / cultural_fit do modelo atual.
Classificação e faixas (§9.5)
CLASSIFICATION_RANGES em 0–5 (Excellent ≥4,5 … Low &lt;2,0).
Doc §9.5: faixas em WSI final 0–10 com 6 rótulos (Excepcional … Regular/Baixo) e coluna “decisão automática”.
Recalcular ranges após escala final unificada; opcionalmente separar rótulo de decisão (isso encosta em F10).
Falha do extrator LLM (§9.4)
Não há política centralizada de fallback no agregador; scoring por resposta é responsabilidade do fluxo F8.
Defaults conservadores + _llm_fallback para auditoria; nunca reprovar só por falha técnica.
Implementar no serviço de extração F8 e propagar flag até analysis_data.
Perfil Big Five observado (§9.6)
Não há candidate_big_five_observed persistido com score_demonstrated / score_required / gap / status por trait.
JSON agregando evidências das respostas comportamentais vs perfil requerido do JD (F2/F3).
Serviço pós-agregação + coluna jsonb em evaluation_candidates (ou snapshot no ai_feedback).
trait_weight por pergunta (nota WSI-8)
Perguntas não carregam trait_weight derivado do F3 (doc: default 1,0 se F3 indisponível).
WSIQuestionBlock.trait_weight na referência Python.
Campo opcional em questions ou extra_params preenchido na geração F6.

Parecer (F9)
O doc define F9 como composição explícita de três blocos possíveis (técnico, comportamental ponderado pelo ranking do JD, elegibilidade), com pesos de senioridade tabulados — sem um “multiplicador” opaco sobre uma média já misturada. O Rails hoje aproxima só a parte de média técnica / média comportamental com pesos macro 70/30 e um ajuste por senioridade que não reproduz §9.2–9.3 e ainda depende de job.seniority numérico como string (risco de fallback errado, como na discussão F4).
Ordem sugerida: alinhar escala F8 → scores por pergunta → implementar WSI_comportamental ponderado (F3) → trocar fórmula do WSI final pela §9.3 com SENIORITY_WEIGHTS do doc → persistir Big Five observado para F10/F11.

---

Segue a Fase 10 no mesmo formato, com base no doc (§10.1–10.6, ~2651–2767) e no que existe hoje em evaluation_candidates, agregação e jobs.

F10 — Gates absolutos e critérios de aprovação
Frente
O que temos hoje (ats_api)
O que não temos (vs metodologia)
O que precisaríamos alterar / criar
Duas camadas (gates → score)
Após as respostas, roda-se e classificação só por faixas de score (wsi_classification). Não há passo explícito “primeiro gates, depois nota”.
Doc §10.1: gates têm precedência total; nota alta não salva se algum gate disparou.
Serviço ScreeningDecisionService (ou equivalente) que ordene checagens: G1–G6 → só então §10.3–10.4.
G1 — Elegibilidade
Sem tipo de pergunta / fluxo de elegibilidade binária (F7) ligado a decisão.
Qualquer obrigatória Não → reprovação por gate (independente do WSI).
Vamos adiar o bloco de Elegibilidade
G2 — Prompt injection
Sem contador persistido de tentativas por candidato/sessão; detecção pode existir só no agente, sem contrato com o Rails.
≥ 2 ocorrências → gate (doc §10.2).
Persistir eventos ou flags em analysis_data / tabela de segurança + regra G2.
G3 — WSI técnico mínimo
Não há comparação WSI_tecnico < 4.0 (em escala 0–10 do doc) após agregação. jobs.minimum_screening_score entra em analytics 1, não como gate WSI.
Limiar fixo sobre bloco técnico (e no Python citado há ainda limiar por resposta — alinhar produto).
Calcular WSI_tecnico como na F9 doc e aplicar G3 antes da decisão por score.
G4 — Skill crítica
Skills na vaga sem flag critical (máx. 2) amarrada a pergunta técnica e limiar score &lt; 3.0 (0–10).
Gate explícito §10.2.
Schema em skill_relationships ou questions + avaliação na F10.
G5 — Engajamento
Não há agregação “≥ 50% respostas com &lt; 30 palavras” como reprovação automática.
Doc §10.2 (coleta não bloqueia, gate sim).
Contagem a partir de answers.description + regra no decisor.
G6 — Inflação sistemática
Penalidade por resposta em (score_inflation); não há gate “≥ 3 perguntas com inflação”.
Padrão sistemático §10.2.
Agregar flags inflation_detected (pós-F8) e aplicar G6.
Critérios §10.3 (faixas WSI Final / Téc / Comp / gap top-1)
Decisão efetiva não implementada como tabela §10.3; classificação atual é Excellent / High / … em escala 0–5 interna.
Limiares em 0–10 no doc para final e sub-blocos + gap top-1 trait 15 / 20 pts.
Unificar escala com F8/F9; persistir gap top-1 a partir do perfil observado (F9.6).
Lógica §10.4 (APROVADO / EM_AVALIAÇÃO / REPROVADO + confiança)
evaluation_candidates tem score, wsi_classification, wsi_level, wsi_summary — sem decision, decision_confidence, gate_triggered, human_review_required.
Pseudocódigo §10.4 e matriz §10.5.
Novos campos ou jsonb wsi_decision + API para recrutador.
Red flags §10.6
pode produzir análise qualitativa; não há conjunto RF-01–RF-08 calculado de forma determinística como no doc.
Lista estruturada para relatório F11 (não reprovam sozinhas).
Função detect_red_flags consumindo analysis_data de todas as respostas.

Parecer (F10)
A F10 é o “tribunal” da metodologia: seis gates objetivos, depois regras de score e gap com estados Aprovado / Em avaliação / Reprovado e confiança. No ats_api, o que existe é sobretudo nota agregada + rótulo de classificação e, à parte, mínimo de score na vaga para métricas — não o motor de gates nem a persistência de gate_triggered / decisão explícita.Dependências: F7 (elegibilidade + texto), F8 (flags inflation, response_authentic, contagem palavras), F9 (WSI_tecnico, WSI_comportamental, WSI_final e perfil observado para gap top-1). Ordem sugerida: implementar cálculo dos blocos e WSI final alinhados ao doc (F9) → serviço de decisão F10 → persistência + RF-01–08 para F11.

---

Segue a Fase 11 no mesmo formato, com base no doc (§11.1–11.2, template ~2792–2967; §11.2.1 gaps; §11.5 perguntas presenciais; referências a endpoints em wsi.py) e no que o ats_api expõe hoje (, evaluation_candidates.ai_feedback).

F11 — Relatório completo do consultor
Frente
O que temos hoje (ats_api)
O que não temos (vs metodologia)
O que precisaríamos alterar / criar
Documento de decisão estruturado (§11.2)
Após a triagem, monta análise com dados determinísticos (build_deterministic_analysis) + texto via LLM (skills, comportamento, recomendação, sumário, etc.) e o fluxo costuma persistir em evaluation_candidates.ai_feedback (via job de notificação).
Template fixo em 9 seções: cabeçalho (vaga + candidato + JD Quality Score, modo Compact/Full), resultado e decisão com checklist G1–G6, visão geral de scores com pesos %, cruzamento técnico (skill × Dreyfus/Bloom esperado vs demonstrado), cruzamento Big Five (rank JD, req, cand., gap), detalhe por pergunta, Seção 7 gaps (template determinístico §11.2.1), radar, auditoria (versão metodologia, modelos LLM, hash SHA-256).
Gerador de relatório (template + preenchimento a partir de F1–F10) ou serialização canônica f11_report_json; não depender só de narrativa LLM para campos de decisão/auditoria.
Alinhamento com F10
ai_feedback pode incluir approval_criteria e recomendação qualitativa; não reproduz obrigatoriamente gates verificados, gate_triggered, nem a matriz §10.5 no formato do relatório.
Seções 2–3 do template com estado explícito pós-F10 + red flags §10.6.
F10 grava decisão estruturada → F11 só renderiza (comparabilidade entre candidatos).
Seção 7 — Gaps (§11.2.1)
Gaps vêm em grande parte do LLM (weaknesses, narrativas), não da tabela de severidade determinística do doc (ALTO/MÉDIO/BAIXO por regras de score/peso/Bloom).
Texto comparável entre candidatos da mesma vaga; máx. 3 fortes / 4 gaps; 2 perguntas CBI ancoradas em gaps_ranked (F11.5).
Motor determinístico de gaps + slot para F11.5 antes do bloco narrativo opcional.
F11.5 — Perguntas para entrevista presencial
Não há serviço dedicado que gere exatamente 2 perguntas CBI a partir dos top 3 gaps (gap_score_delta), com parâmetros do doc (ex.: temp 0.6).
Perguntas calibradas injetadas na Seção 7.
Serviço + persistência em ai_feedback ou no JSON do relatório.
Ranking por vaga / por candidato
Não há endpoints tipo GET .../ranking/{vacancy_id} ou GET .../candidate/.../ranking/... como na referência Python; “ranking” no repo aparece em jobs stats / search, não em WSI por vaga.
Comparação de candidatos na mesma triagem com mesmo relatório estruturado.
Endpoints + queries ordenadas por WSI_final (e desempate documentado) + política de privacidade.
Cache f11_report_json
Cada chamada reconstrói payload e pode reinvocar LLM para a parte qualitativa (custo e variabilidade).
Cache invalidado quando respostas/decisão mudam.
Coluna jsonb + updated_at / versão; invalidação em Answer/EvaluationCandidate update.
Feedback ao candidato (transparência)
Doc §8.5.1: templates determinísticos por competência; há menção a feedback explicável na metodologia. O produto Rails pode ter fluxo paralelo (não mapeado aqui como paridade total).
Garantir que o texto ao candidato não viole as regras EU AI Act citadas (estrutura fixa).
Alinhar canal candidato ao template §8.5.1 se for requisito legal de paridade.
F11.7 — Relatório completo via LLM (LIA)
Hoje o “relatório” é híbrido: blocos estruturados + LLM para narrativa.
Doc prevê um prompt de geração completa para alimentar 3 abas do modal de detalhes (checklist longo no doc).
Opcional: unificar em um contrato JSON único consumido pelo front, com campos obrigatórios validados.

Parecer (F11)
No doc, o F11 é o pacote fechado de decisão e auditoria: mesma estrutura para todos os candidatos, com dados vindos de F1–F10 (incluindo gates, pesos, cruzamentos skill/trait, hash, versões de modelo). No ats_api, o que há é rico para o recrutador (análise IA + agregados), mas não o relatório canônico nem APIs de ranking/cache da implementação de referência — e a Seção 7 deveria ser, na metodologia, majoritariamente determinística para equidade entre candidatos.Dependências: F9 (blocos e perfil observado), F10 (decisão + gates + red flags), F7 (hash), F1 (JD quality no cabeçalho). Ordem sugerida: congelar schema JSON do relatório → preenchimento a partir dos serviços existentes → endpoints + cache → F11.5 → reduzir dependência de LLM para campos “de decisão”.
