-- ============================================================================
-- SEED DEMO — Triagem WSI para a vaga "Diretor(a) Juridico(a) (Chief Legal Officer)"
-- ----------------------------------------------------------------------------
-- Objetivo: popular dados de triagem WSI completos (sessao + perguntas +
--   respostas analisadas + resultado + relatorio + feedback) para dois
--   candidatos da vaga, de modo que o modal "Triagem WSI" (icone BrainCircuit
--   no card do Kanban) abra com conteudo rico para DEMO a clientes:
--     - Bruno Henrique Costa  -> destaque (WSI 9.5/10, "Excepcional", Aprovado)
--     - Ana Lima Ferreira     -> forte 2o lugar (WSI 7.8/10, "Alto", Em Avaliacao)
--
-- IMPORTANTE — este script e DADO DE DEMO, nao codigo de producao. Usa SQL
--   direto (fora do escopo do ADR-001, que restringe SQL inline em services/).
--   E idempotente: pode ser re-executado a vontade (apaga as 2 sessoes demo
--   por UUID fixo, em cascata, e re-insere).
--
-- Contexto (confirmado no banco helium/heliumdb em 2026-06-05):
--   vaga    610705ab-7a98-45e9-999a-5bdb62975989  (company 00000000-0000-4000-a000-000000000001)
--   Bruno   c5f82107-431a-47fe-acb0-b3aa4f16373c  (lia_score 94.8 -> card 95%)
--   Ana     5392a24a-5b03-4a9b-96e0-2e3f43de9eef  (lia_score NULL -> card vazio)
--
-- Escalas WSI: scores 0-10 (numeric(3,2)); weight 0-1; bloom 1-6; dreyfus 1-5;
--   percentile 0-100; classification/decision/framework/etc validados por CHECK.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- 0) Limpeza idempotente (cascata: sessions -> questions/response_analyses/results
--    -> reports/feedbacks). UUID fixos garantem que so removemos a demo.
-- ----------------------------------------------------------------------------
DELETE FROM wsi_sessions WHERE id IN (
  'c5f8b000-0000-4000-a000-000000000001',  -- Bruno
  '5392a000-0000-4000-a000-000000000001'   -- Ana
);

-- ----------------------------------------------------------------------------
-- 1) Polimento do candidato Ana para a DEMO (nome/cargo estavam malformados)
--    + lia_score para o card de triagem deixar de ficar vazio (78%).
-- ----------------------------------------------------------------------------
UPDATE candidates
   SET name = 'Ana Lima Ferreira',
       current_title = 'Gerente Juridica',
       lia_score = 78
 WHERE id = '5392a24a-5b03-4a9b-96e0-2e3f43de9eef';

-- ============================================================================
-- BRUNO HENRIQUE COSTA — WSI 9.5 / Excepcional / Aprovado
-- ============================================================================

INSERT INTO wsi_sessions
  (id, candidate_id, job_vacancy_id, screening_type, mode, status,
   question_set_version, question_set_id, started_at, completed_at, score)
VALUES
  ('c5f8b000-0000-4000-a000-000000000001',
   'c5f82107-431a-47fe-acb0-b3aa4f16373c',
   '610705ab-7a98-45e9-999a-5bdb62975989',
   'chat', 'compact', 'completed',
   1, NULL,
   CURRENT_TIMESTAMP - INTERVAL '2 days' - INTERVAL '17 minutes',
   CURRENT_TIMESTAMP - INTERVAL '2 days',
   9.5);

INSERT INTO wsi_results
  (id, session_id, candidate_id, job_vacancy_id,
   technical_wsi, behavioral_wsi, overall_wsi, classification, percentile,
   created_at)
VALUES
  ('c5f8b000-0000-4000-a000-0000000000a1',
   'c5f8b000-0000-4000-a000-000000000001',
   'c5f82107-431a-47fe-acb0-b3aa4f16373c',
   '610705ab-7a98-45e9-999a-5bdb62975989',
   9.6, 9.4, 9.5, 'excepcional', 96,
   CURRENT_TIMESTAMP - INTERVAL '2 days');

-- Perguntas (CHECK: framework IN CBI/Bloom/Dreyfus/BigFive;
--   question_type IN autodeclaration/contextual/microcase/situational; weight 0-1)
INSERT INTO wsi_questions
  (id, session_id, competency, framework, question_type, question_text, weight, expected_signals, sequence_order)
VALUES
  ('c5f8b000-0000-4000-a000-000000000011','c5f8b000-0000-4000-a000-000000000001',
   'Governanca Corporativa e Compliance','CBI','situational',
   'Descreva uma situacao em que voce estruturou ou reformulou um programa de compliance corporativo. Qual era o contexto, como conduziu e quais resultados alcancou?',
   1.00, '["estruturacao de programa","metricas de risco","resultado mensuravel","aderencia regulatoria"]'::jsonb, 1),

  ('c5f8b000-0000-4000-a000-000000000012','c5f8b000-0000-4000-a000-000000000001',
   'Gestao de Contencioso Estrategico','CBI','situational',
   'Conte sobre o contencioso de maior impacto que voce liderou. Como definiu a estrategia juridica e qual foi o desfecho?',
   1.00, '["definicao de estrategia","analise de risco-retorno","desfecho","exposicao financeira"]'::jsonb, 2),

  ('c5f8b000-0000-4000-a000-000000000013','c5f8b000-0000-4000-a000-000000000001',
   'Negociacao de Contratos de Alto Impacto','CBI','contextual',
   'De um exemplo de negociacao contratual complexa (M&A, parceria estrategica ou contrato de grande valor) que voce conduziu. Quais riscos identificou e como protegeu a companhia?',
   0.90, '["identificacao de riscos","clausulas de protecao","valor negociado","resultado"]'::jsonb, 3),

  ('c5f8b000-0000-4000-a000-000000000014','c5f8b000-0000-4000-a000-000000000001',
   'Lideranca e Gestao da Area Juridica','CBI','situational',
   'Como voce estruturou e desenvolveu sua equipe juridica? Descreva uma situacao de reestruturacao ou desenvolvimento de time.',
   0.95, '["desenvolvimento de pessoas","estrutura de time","indicadores de produtividade","retencao"]'::jsonb, 4),

  ('c5f8b000-0000-4000-a000-000000000015','c5f8b000-0000-4000-a000-000000000001',
   'Visao de Negocio e Gestao de Riscos','Bloom','microcase',
   'A diretoria quer lancar um produto inovador em zona regulatoria cinzenta. Como voce equilibra a viabilizacao do negocio com a mitigacao do risco juridico?',
   0.85, '["pensamento de negocio","apetite a risco","plano de mitigacao","decisao estruturada"]'::jsonb, 5);

-- Respostas analisadas (CHECK: bloom 1-6; dreyfus 1-5; scores 0-10)
INSERT INTO wsi_response_analyses
  (id, session_id, question_id, candidate_id, job_vacancy_id, competency, response_text,
   autodeclaration_score, context_score, bloom_level, dreyfus_level,
   evidences, red_flags, consistency_penalty, final_score, justification, response_hash)
VALUES
  ('c5f8b000-0000-4000-a000-000000000021','c5f8b000-0000-4000-a000-000000000001','c5f8b000-0000-4000-a000-000000000011',
   'c5f82107-431a-47fe-acb0-b3aa4f16373c','610705ab-7a98-45e9-999a-5bdb62975989',
   'Governanca Corporativa e Compliance',
   'Quando assumi como Head Juridico de uma fintech em expansao, a empresa nao tinha programa de compliance estruturado e enfrentava risco regulatorio crescente junto ao Banco Central. Estruturei o programa em 90 dias: construi a matriz de riscos por area, implementei codigo de conduta, canal de denuncias independente, politica antsuborno e adequacao completa a LGPD, treinando mais de 400 colaboradores. Passamos pela auditoria do regulador sem nenhum apontamento e reduzimos os incidentes reportados em 60 por cento ao longo do primeiro ano.',
   9.4, 9.6, 6, 5,
   '["Programa estruturado em 90 dias","Auditoria do regulador sem apontamentos","Reducao de 60% em incidentes","Treinamento de mais de 400 colaboradores"]'::jsonb,
   '[]'::jsonb, 0, 9.7,
   'Resposta STAR completa, com contexto regulatorio especifico, acao detalhada e resultados mensuraveis. Demonstra dominio de especialista na estruturacao de programas de compliance de ponta a ponta.',
   md5('bruno-juridico-ra1')),

  ('c5f8b000-0000-4000-a000-000000000022','c5f8b000-0000-4000-a000-000000000001','c5f8b000-0000-4000-a000-000000000012',
   'c5f82107-431a-47fe-acb0-b3aa4f16373c','610705ab-7a98-45e9-999a-5bdb62975989',
   'Gestao de Contencioso Estrategico',
   'Liderei a defesa de uma acao tributaria de aproximadamente 80 milhoes de reais que ameacava o fluxo de caixa da companhia. Em vez de litigar de forma reativa, montei uma tese combinando jurisprudencia recente do STJ com um parecer economico independente, e em paralelo avaliei a transacao tributaria como alternativa. Conduzi a negociacao com a Procuradoria e fechamos um acordo que reduziu a exposicao em 70 por cento, com previsibilidade de caixa e sem impacto reputacional.',
   9.3, 9.5, 6, 5,
   '["Exposicao de 80 milhoes endereçada","Reducao de 70% na exposicao","Tese juridico-economica combinada","Acordo com previsibilidade de caixa"]'::jsonb,
   '[]'::jsonb, 0, 9.5,
   'Pensamento estrategico de alto nivel: equilibra risco-retorno, considera alternativas (litigio x transacao) e entrega resultado financeiro concreto. Nivel de especialista.',
   md5('bruno-juridico-ra2')),

  ('c5f8b000-0000-4000-a000-000000000023','c5f8b000-0000-4000-a000-000000000001','c5f8b000-0000-4000-a000-000000000013',
   'c5f82107-431a-47fe-acb0-b3aa4f16373c','610705ab-7a98-45e9-999a-5bdb62975989',
   'Negociacao de Contratos de Alto Impacto',
   'Conduzi o juridico na aquisicao de uma concorrente avaliada em 250 milhoes. Estruturei a due diligence em tres frentes (trabalhista, tributaria e contratos), identifiquei um passivo trabalhista oculto e um contrato de fornecimento com clausula de change of control que poderia ser rescindido. Negociei um ajuste de preco, uma conta escrow e clausulas de indenizacao especificas, alem de obter o waiver do fornecedor antes do fechamento. A operacao fechou no prazo e sem disputas pos-aquisicao.',
   9.2, 9.6, 5, 5,
   '["Due diligence em 3 frentes","Passivo oculto identificado","Escrow e clausulas de indenizacao","Waiver de change of control obtido"]'::jsonb,
   '[]'::jsonb, 0, 9.6,
   'Demonstra visao 360 de risco em M&A e capacidade de traduzir riscos em mecanismos contratuais de protecao. Resultado protegeu a companhia e viabilizou o negocio.',
   md5('bruno-juridico-ra3')),

  ('c5f8b000-0000-4000-a000-000000000024','c5f8b000-0000-4000-a000-000000000001','c5f8b000-0000-4000-a000-000000000014',
   'c5f82107-431a-47fe-acb0-b3aa4f16373c','610705ab-7a98-45e9-999a-5bdb62975989',
   'Lideranca e Gestao da Area Juridica',
   'Assumi uma area juridica de oito pessoas que operava de forma reativa e sem indicadores. Redesenhei a estrutura em squads por tema (societario, contratos e contencioso), implementei OKRs e um SLA de atendimento as areas de negocio, e criei um programa de mentoria interna. Em um ano reduzi o tempo medio de resposta de 12 para 3 dias, promovi duas pessoas a coordenacao e a area passou a ser percebida como parceira de negocio, com NPS interno acima de 85.',
   9.4, 9.3, 5, 5,
   '["Reestruturacao em squads","SLA reduzido de 12 para 3 dias","Duas promocoes internas","NPS interno acima de 85"]'::jsonb,
   '[]'::jsonb, 0, 9.4,
   'Lideranca madura, orientada a pessoas e a indicadores. Transformou a area de centro de custo reativo em parceira estrategica de negocio.',
   md5('bruno-juridico-ra4')),

  ('c5f8b000-0000-4000-a000-000000000025','c5f8b000-0000-4000-a000-000000000001','c5f8b000-0000-4000-a000-000000000015',
   'c5f82107-431a-47fe-acb0-b3aa4f16373c','610705ab-7a98-45e9-999a-5bdb62975989',
   'Visao de Negocio e Gestao de Riscos',
   'Eu nao trato zona cinzenta como bloqueio nem como sinal verde. Mapeio o apetite a risco com a diretoria, classifico o risco por probabilidade e impacto, e desenho um caminho de viabilizacao por etapas: consulta ou sandbox regulatorio quando existir, piloto controlado com volume limitado, e clausulas de saida. Documento a decisao e os pressupostos para rastreabilidade. Assim o negocio avanca com risco consciente e mitigado, e nao com risco ignorado.',
   9.3, 9.5, 6, 5,
   '["Apetite a risco alinhado com diretoria","Uso de sandbox regulatorio","Piloto controlado por etapas","Decisao documentada e rastreavel"]'::jsonb,
   '[]'::jsonb, 0, 9.5,
   'Equilibra viabilizacao de negocio e mitigacao de risco com metodo claro e estruturado. Pensamento de nivel diretor, com governanca da propria decisao.',
   md5('bruno-juridico-ra5'));

-- Relatorio estruturado (jsonb conforme shapes consumidos pelo modal)
INSERT INTO wsi_reports
  (id, wsi_result_id, candidate_id, executive_summary,
   technical_analysis, behavioral_analysis, cultural_fit, recommendation)
VALUES
  ('c5f8b000-0000-4000-a000-0000000000b1',
   'c5f8b000-0000-4000-a000-0000000000a1',
   'c5f82107-431a-47fe-acb0-b3aa4f16373c',
   'Bruno Henrique Costa apresentou desempenho excepcional na triagem para Diretor Juridico, com WSI geral de 9.5/10 (percentil 96). Demonstrou dominio de especialista em governanca, compliance e gestao de contencioso estrategico, sempre sustentado por resultados mensuraveis e por uma lideranca consolidada e orientada a negocio. Recomendacao forte de avanco para a etapa final.',
   '{"pontos_fortes":["Estruturacao de programas de compliance de ponta a ponta com aderencia regulatoria comprovada","Estrategia de contencioso orientada a risco-retorno, com resultados financeiros concretos","Visao 360 de risco em operacoes de M&A, traduzindo riscos em protecoes contratuais","Lideranca por indicadores que transforma a area juridica em parceira de negocio"],"gaps":[{"texto":"Experiencia internacional / cross-border ainda concentrada no mercado nacional","severidade":"baixa"}],"evidencias":["Auditoria de regulador sem apontamentos","Reducao de 70% em exposicao tributaria de 80 milhoes","SLA juridico reduzido de 12 para 3 dias"]}'::jsonb,
   '{"openness":{"score":4.5,"descricao":"Aberto a novas abordagens regulatorias e a inovacao com risco consciente","is_critical":false,"expected_pct":70,"dreyfus_esperado":4},"conscientiousness":{"score":4.8,"descricao":"Altissima disciplina, rigor metodologico e governanca das proprias decisoes","is_critical":true,"expected_pct":85,"dreyfus_esperado":5},"extraversion":{"score":4.2,"descricao":"Comunicacao clara e influente com diretoria e areas de negocio","is_critical":false,"expected_pct":65,"dreyfus_esperado":4},"agreeableness":{"score":4.3,"descricao":"Colaborativo, constroi consenso sem abrir mao de posicoes tecnicas","is_critical":false,"expected_pct":70,"dreyfus_esperado":4},"neuroticism":{"score":4.4,"descricao":"Mantem a calma sob pressao em cenarios de alta exposicao e crise","is_critical":true,"expected_pct":80,"dreyfus_esperado":4}}'::jsonb,
   '{"alinhamento":"alto","score":9.2,"descricao":"Perfil aderente a uma cultura de alta responsabilidade, transparencia e parceria com o negocio."}'::jsonb,
   '{"decisao":"Avancar para entrevista final com a lideranca","justificativa":"Candidato excepcional, com evidencias consistentes de senioridade de diretor em todas as competencias avaliadas e fit cultural elevado.","proximos_passos":["Entrevista final com CEO e board","Validacao de pretensao salarial e disponibilidade","Checagem de referencias de lideranca"]}'::jsonb);

-- Feedback para o candidato (CHECK: decision IN aprovado/aguardando/nao_aprovado)
INSERT INTO wsi_feedbacks
  (id, wsi_result_id, candidate_id, decision, main_message,
   technical_strengths, development_opportunities, behavioral_strengths,
   next_steps, personalized_tip, development_plan, recommended_resources)
VALUES
  ('c5f8b000-0000-4000-a000-0000000000c1',
   'c5f8b000-0000-4000-a000-0000000000a1',
   'c5f82107-431a-47fe-acb0-b3aa4f16373c',
   'aprovado',
   'Parabens, Bruno! Sua triagem para a posicao de Diretor Juridico foi excepcional. Suas respostas demonstraram senioridade consistente em governanca, contencioso estrategico e lideranca, sempre com resultados concretos.',
   '["Estruturacao de programas de compliance com aderencia regulatoria comprovada","Estrategia de contencioso orientada a risco-retorno","Protecao contratual sofisticada em operacoes de M&A"]'::jsonb,
   '["Ampliar exposicao a operacoes cross-border e regulacao internacional"]'::jsonb,
   '["Lideranca madura e orientada a indicadores","Comunicacao influente com a alta gestao","Equilibrio emocional em cenarios de crise"]'::jsonb,
   'Convidaremos voce para a entrevista final com a lideranca nos proximos dias.',
   'Na entrevista final, traga 2 ou 3 exemplos de decisoes em zona regulatoria cinzenta - e um diferencial forte do seu perfil.',
   '{"foco":"Exposicao internacional","horizonte":"6-12 meses"}'::jsonb,
   '["Programa de regulacao internacional / cross-border","Imersao em operacoes societarias multi-jurisdicao"]'::jsonb);

-- ============================================================================
-- ANA LIMA FERREIRA — WSI 7.8 / Alto / Em Avaliacao (forte 2o lugar)
-- ============================================================================

INSERT INTO wsi_sessions
  (id, candidate_id, job_vacancy_id, screening_type, mode, status,
   question_set_version, question_set_id, started_at, completed_at, score)
VALUES
  ('5392a000-0000-4000-a000-000000000001',
   '5392a24a-5b03-4a9b-96e0-2e3f43de9eef',
   '610705ab-7a98-45e9-999a-5bdb62975989',
   'chat', 'compact', 'completed',
   1, NULL,
   CURRENT_TIMESTAMP - INTERVAL '1 day' - INTERVAL '14 minutes',
   CURRENT_TIMESTAMP - INTERVAL '1 day',
   7.8);

INSERT INTO wsi_results
  (id, session_id, candidate_id, job_vacancy_id,
   technical_wsi, behavioral_wsi, overall_wsi, classification, percentile,
   created_at)
VALUES
  ('5392a000-0000-4000-a000-0000000000a1',
   '5392a000-0000-4000-a000-000000000001',
   '5392a24a-5b03-4a9b-96e0-2e3f43de9eef',
   '610705ab-7a98-45e9-999a-5bdb62975989',
   7.5, 8.0, 7.8, 'alto', 72,
   CURRENT_TIMESTAMP - INTERVAL '1 day');

INSERT INTO wsi_questions
  (id, session_id, competency, framework, question_type, question_text, weight, expected_signals, sequence_order)
VALUES
  ('5392a000-0000-4000-a000-000000000011','5392a000-0000-4000-a000-000000000001',
   'Governanca Corporativa e Compliance','CBI','situational',
   'Descreva uma situacao em que voce estruturou ou reformulou um programa de compliance corporativo. Qual era o contexto, como conduziu e quais resultados alcancou?',
   1.00, '["estruturacao de programa","metricas de risco","resultado mensuravel","aderencia regulatoria"]'::jsonb, 1),

  ('5392a000-0000-4000-a000-000000000012','5392a000-0000-4000-a000-000000000001',
   'Gestao de Contencioso Estrategico','CBI','situational',
   'Conte sobre o contencioso de maior impacto que voce liderou. Como definiu a estrategia juridica e qual foi o desfecho?',
   1.00, '["definicao de estrategia","analise de risco-retorno","desfecho","exposicao financeira"]'::jsonb, 2),

  ('5392a000-0000-4000-a000-000000000013','5392a000-0000-4000-a000-000000000001',
   'Negociacao de Contratos de Alto Impacto','CBI','contextual',
   'De um exemplo de negociacao contratual complexa (M&A, parceria estrategica ou contrato de grande valor) que voce conduziu. Quais riscos identificou e como protegeu a companhia?',
   0.90, '["identificacao de riscos","clausulas de protecao","valor negociado","resultado"]'::jsonb, 3),

  ('5392a000-0000-4000-a000-000000000014','5392a000-0000-4000-a000-000000000001',
   'Lideranca e Gestao da Area Juridica','CBI','situational',
   'Como voce estruturou e desenvolveu sua equipe juridica? Descreva uma situacao de reestruturacao ou desenvolvimento de time.',
   0.95, '["desenvolvimento de pessoas","estrutura de time","indicadores de produtividade","retencao"]'::jsonb, 4),

  ('5392a000-0000-4000-a000-000000000015','5392a000-0000-4000-a000-000000000001',
   'Visao de Negocio e Gestao de Riscos','Bloom','microcase',
   'A diretoria quer lancar um produto inovador em zona regulatoria cinzenta. Como voce equilibra a viabilizacao do negocio com a mitigacao do risco juridico?',
   0.85, '["pensamento de negocio","apetite a risco","plano de mitigacao","decisao estruturada"]'::jsonb, 5);

INSERT INTO wsi_response_analyses
  (id, session_id, question_id, candidate_id, job_vacancy_id, competency, response_text,
   autodeclaration_score, context_score, bloom_level, dreyfus_level,
   evidences, red_flags, consistency_penalty, final_score, justification, response_hash)
VALUES
  ('5392a000-0000-4000-a000-000000000021','5392a000-0000-4000-a000-000000000001','5392a000-0000-4000-a000-000000000011',
   '5392a24a-5b03-4a9b-96e0-2e3f43de9eef','610705ab-7a98-45e9-999a-5bdb62975989',
   'Governanca Corporativa e Compliance',
   'Na empresa em que atuo, participei da revisao do programa de compliance. Atualizei o codigo de conduta, ajudei a implantar o canal de denuncias e conduzi treinamentos de LGPD para as areas. O programa ficou mais maduro e tivemos boa adesao das equipes, embora a medicao de indicadores de efetividade ainda esteja em construcao.',
   8.0, 7.6, 4, 4,
   '["Revisao do codigo de conduta","Implantacao de canal de denuncias","Treinamentos de LGPD"]'::jsonb,
   '["Resultado descrito de forma qualitativa, sem metricas de efetividade"]'::jsonb, 0.3, 7.8,
   'Boa experiencia pratica em compliance e execucao consistente. Gap em demonstrar resultado por indicadores quantitativos - ponto a aprofundar na entrevista.',
   md5('ana-juridico-ra1')),

  ('5392a000-0000-4000-a000-000000000022','5392a000-0000-4000-a000-000000000001','5392a000-0000-4000-a000-000000000012',
   '5392a24a-5b03-4a9b-96e0-2e3f43de9eef','610705ab-7a98-45e9-999a-5bdb62975989',
   'Gestao de Contencioso Estrategico',
   'Acompanhei uma carteira de contencioso civel e trabalhista relevante e fui responsavel por priorizar os casos de maior risco. Em um caso trabalhista importante, optei por acordo apos analisar a jurisprudencia e o custo de litigar. Reduzimos a contingencia, mas reconheco que a decisao foi mais reativa do que parte de uma estrategia macro de portfolio.',
   7.6, 7.2, 4, 3,
   '["Priorizacao por risco","Acordo trabalhista com reducao de contingencia"]'::jsonb,
   '["Abordagem mais reativa do que estrategica no nivel de portfolio"]'::jsonb, 0.4, 7.3,
   'Demonstra solidez tecnica e bom julgamento caso a caso. Para o nivel de diretor, falta evidencia de estrategia de contencioso no nivel de portfolio.',
   md5('ana-juridico-ra2')),

  ('5392a000-0000-4000-a000-000000000023','5392a000-0000-4000-a000-000000000001','5392a000-0000-4000-a000-000000000013',
   '5392a24a-5b03-4a9b-96e0-2e3f43de9eef','610705ab-7a98-45e9-999a-5bdb62975989',
   'Negociacao de Contratos de Alto Impacto',
   'Conduzi a revisao e negociacao de contratos comerciais relevantes, incluindo um contrato de fornecimento estrategico. Identifiquei riscos de reajuste e de rescisao e negociei clausulas de protecao e SLA. Nao tive ainda a oportunidade de liderar uma operacao de M&A de ponta a ponta, mas participei do suporte juridico em uma due diligence.',
   8.2, 7.8, 5, 4,
   '["Negociacao de contrato de fornecimento estrategico","Clausulas de protecao e SLA","Suporte em due diligence"]'::jsonb,
   '[]'::jsonb, 0, 8.0,
   'Forte em negociacao contratual comercial. Experiencia em M&A ainda como suporte, nao como lideranca da operacao - natural para o proximo passo de carreira.',
   md5('ana-juridico-ra3')),

  ('5392a000-0000-4000-a000-000000000024','5392a000-0000-4000-a000-000000000001','5392a000-0000-4000-a000-000000000014',
   '5392a24a-5b03-4a9b-96e0-2e3f43de9eef','610705ab-7a98-45e9-999a-5bdb62975989',
   'Lideranca e Gestao da Area Juridica',
   'Coordeno hoje uma equipe de tres advogados. Organizei a distribuicao de demandas por especialidade, criei rituais semanais de alinhamento e acompanho prazos de forma estruturada. A equipe ganhou previsibilidade e a satisfacao das areas internas melhorou. Lideranca de times maiores e algo que busco desenvolver nesta proxima etapa.',
   8.0, 8.2, 4, 4,
   '["Coordenacao de equipe de 3 advogados","Rituais de alinhamento semanais","Melhora na satisfacao das areas internas"]'::jsonb,
   '[]'::jsonb, 0, 8.1,
   'Boa base de lideranca e organizacao de time. Escala de gestao (times maiores e multi-tema) ainda em desenvolvimento para o nivel de diretor.',
   md5('ana-juridico-ra4')),

  ('5392a000-0000-4000-a000-000000000025','5392a000-0000-4000-a000-000000000001','5392a000-0000-4000-a000-000000000015',
   '5392a24a-5b03-4a9b-96e0-2e3f43de9eef','610705ab-7a98-45e9-999a-5bdb62975989',
   'Visao de Negocio e Gestao de Riscos',
   'Eu busco entender o objetivo de negocio antes de dar uma resposta juridica. Em uma zona cinzenta, levantaria os precedentes, avaliaria o risco e proporia um caminho com mitigacoes, como comecar com um escopo reduzido. Acredito que o juridico deve viabilizar e nao apenas barrar, ainda que eu tenda a ser conservadora quando o risco regulatorio e alto.',
   7.8, 7.4, 5, 4,
   '["Orientacao a objetivo de negocio","Proposta de escopo reduzido como mitigacao","Avaliacao de precedentes"]'::jsonb,
   '["Perfil mais conservador pode exigir calibragem em ambientes de alta inovacao"]'::jsonb, 0.2, 7.6,
   'Visao de negocio presente e bem orientada. Tende ao conservadorismo em risco regulatorio alto - adequado para muitos contextos, a calibrar conforme o apetite a risco da companhia.',
   md5('ana-juridico-ra5'));

INSERT INTO wsi_reports
  (id, wsi_result_id, candidate_id, executive_summary,
   technical_analysis, behavioral_analysis, cultural_fit, recommendation)
VALUES
  ('5392a000-0000-4000-a000-0000000000b1',
   '5392a000-0000-4000-a000-0000000000a1',
   '5392a24a-5b03-4a9b-96e0-2e3f43de9eef',
   'Ana Lima Ferreira teve um desempenho solido na triagem para Diretor Juridico, com WSI geral de 7.8/10 (percentil 72). Apresenta base tecnica consistente em compliance, contratos e gestao de equipe, com bom julgamento e fit comportamental elevado. Os principais pontos a aprofundar sao a estrategia de contencioso no nivel de portfolio e a lideranca de times maiores - naturais para o salto de senioridade. Recomenda-se avancar com avaliacao na entrevista.',
   '{"pontos_fortes":["Execucao consistente em programas de compliance e LGPD","Negociacao contratual comercial solida com clausulas de protecao","Organizacao de equipe e melhora de previsibilidade de entrega"],"gaps":[{"texto":"Estrategia de contencioso ainda mais reativa do que no nivel de portfolio","severidade":"media"},{"texto":"Lideranca de M&A como protagonista (atuou como suporte)","severidade":"media"},{"texto":"Resultados frequentemente descritos sem metricas quantitativas","severidade":"baixa"}],"evidencias":["Acordo trabalhista com reducao de contingencia","Negociacao de contrato de fornecimento estrategico","Coordenacao de equipe de 3 advogados"]}'::jsonb,
   '{"openness":{"score":4.0,"descricao":"Aberta a aprender, com leve tendencia conservadora em risco regulatorio alto","is_critical":false,"expected_pct":70,"dreyfus_esperado":4},"conscientiousness":{"score":4.3,"descricao":"Organizada, metodica e confiavel na execucao","is_critical":true,"expected_pct":85,"dreyfus_esperado":5},"extraversion":{"score":3.6,"descricao":"Comunicacao clara, ainda desenvolvendo presenca executiva junto a board","is_critical":false,"expected_pct":65,"dreyfus_esperado":4},"agreeableness":{"score":4.4,"descricao":"Muito colaborativa e bem avaliada pelas areas internas","is_critical":false,"expected_pct":70,"dreyfus_esperado":4},"neuroticism":{"score":4.0,"descricao":"Boa estabilidade emocional, lida bem com prazos e pressao do dia a dia","is_critical":true,"expected_pct":80,"dreyfus_esperado":4}}'::jsonb,
   '{"alinhamento":"alto","score":8.3,"descricao":"Perfil colaborativo e responsavel, com bom encaixe cultural e espaco claro de crescimento."}'::jsonb,
   '{"decisao":"Avancar com avaliacao na entrevista","justificativa":"Candidata solida e com fit cultural forte; gaps sao de escala/senioridade e devem ser explorados na entrevista para confirmar prontidao para o nivel de diretor.","proximos_passos":["Entrevista tecnica focada em estrategia de contencioso e M&A","Explorar prontidao para liderar times maiores","Validar pretensao e disponibilidade"]}'::jsonb);

INSERT INTO wsi_feedbacks
  (id, wsi_result_id, candidate_id, decision, main_message,
   technical_strengths, development_opportunities, behavioral_strengths,
   next_steps, personalized_tip, development_plan, recommended_resources)
VALUES
  ('5392a000-0000-4000-a000-0000000000c1',
   '5392a000-0000-4000-a000-0000000000a1',
   '5392a24a-5b03-4a9b-96e0-2e3f43de9eef',
   'aguardando',
   'Ana, obrigado pela sua participacao na triagem para Diretor Juridico. Voce demonstrou uma base tecnica solida e um perfil muito colaborativo. Estamos avaliando os perfis e retornaremos com o proximo passo do processo.',
   '["Execucao consistente em compliance e LGPD","Negociacao contratual comercial solida","Organizacao e gestao de equipe com previsibilidade"]'::jsonb,
   '["Desenvolver estrategia de contencioso no nivel de portfolio","Liderar uma operacao de M&A de ponta a ponta","Quantificar resultados com metricas e indicadores"]'::jsonb,
   '["Perfil muito colaborativo e bem avaliado pelas areas","Organizacao e confiabilidade na execucao","Boa estabilidade emocional sob pressao"]'::jsonb,
   'Aguardando decisao do recrutador para a etapa de entrevista.',
   'Na entrevista, traga numeros e indicadores dos seus resultados - isso fortalece muito a percepcao de senioridade.',
   '{"foco":"Estrategia de contencioso e lideranca de escala","horizonte":"12 meses"}'::jsonb,
   '["Formacao em gestao estrategica de contencioso","Mentoria em lideranca de areas juridicas de maior porte"]'::jsonb);

COMMIT;

-- ----------------------------------------------------------------------------
-- Verificacao
-- ----------------------------------------------------------------------------
\echo '=== RESUMO DA SEED ==='
SELECT c.name,
       r.overall_wsi, r.technical_wsi, r.behavioral_wsi, r.classification, r.percentile,
       (SELECT count(*) FROM wsi_response_analyses ra WHERE ra.session_id = r.session_id) AS respostas,
       f.decision
  FROM wsi_results r
  JOIN candidates c ON c.id = r.candidate_id
  LEFT JOIN wsi_feedbacks f ON f.wsi_result_id = r.id
 WHERE r.job_vacancy_id = '610705ab-7a98-45e9-999a-5bdb62975989'
 ORDER BY r.overall_wsi DESC;
