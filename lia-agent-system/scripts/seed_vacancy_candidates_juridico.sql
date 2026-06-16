-- ============================================================================
-- SEED DEMO — links candidato↔vaga (vacancy_candidates) p/ Diretor Jurídico
-- ----------------------------------------------------------------------------
-- Necessário após o fix P0-1: o board passa a ler vacancy_candidates (não mais
-- a lista global). A vaga jurídico tinha 0 links → board ficaria vazio. Este
-- seed vincula ~21 candidatos demo (incl. Bruno + Ana, que têm triagem WSI).
-- Placement no board segue candidate.status (global) — o link só escopa QUEM
-- aparece, então cada candidato permanece na coluna em que já estava.
-- stage/status aqui são p/ a agregação do funil (P1-2). Idempotente.
-- vaga 610705ab-...989 | company 00000000-0000-4000-a000-000000000001
-- ============================================================================
BEGIN;

DELETE FROM vacancy_candidates
 WHERE vacancy_id = '610705ab-7a98-45e9-999a-5bdb62975989'
   AND source = 'seed_demo_juridico';

INSERT INTO vacancy_candidates
  (id, vacancy_id, candidate_id, company_id, source, stage, status, lia_score, created_at, updated_at, stage_entered_at)
SELECT
  gen_random_uuid(),
  '610705ab-7a98-45e9-999a-5bdb62975989',
  c.id,
  '00000000-0000-4000-a000-000000000001',
  'seed_demo_juridico',
  CASE
    WHEN c.status IN ('reprovado','rejected') THEN 'rejected'
    WHEN c.status IN ('aprovado','hired') THEN 'hired'
    WHEN c.status IN ('entrevista','interview') THEN 'interview_hr'
    WHEN c.status IN ('triagem','screening','em_triagem','approved_screening') THEN 'screening'
    ELSE 'sourcing'
  END,
  CASE
    WHEN c.status IN ('reprovado','rejected') THEN 'rejected'
    WHEN c.status IN ('aprovado','hired') THEN 'hired'
    WHEN c.status = 'approved_screening' THEN 'approved'
    WHEN c.status IN ('triagem','screening') THEN 'screening'
    ELSE 'active'
  END,
  c.lia_score,
  now(), now(), now()
FROM candidates c
WHERE c.id IN (
  'c5f82107-431a-47fe-acb0-b3aa4f16373c',  -- Bruno (WSI 9.5)
  '5392a24a-5b03-4a9b-96e0-2e3f43de9eef',  -- Ana Lima Ferreira (WSI 7.8)
  '6aaca77e-c74c-4b2b-b122-d7294dc274dc',
  '1bb0811f-4ae4-4d18-9538-704cee192aad',
  'd538fef9-91a7-4fc9-8a49-fb2d2d23f0dd',
  '70212dd6-f1a0-470a-a0fc-49158826f59f',
  '8f8e3c93-d8fa-4ab1-aa39-b605348e12cb',
  'cc4966df-2ef5-4ffc-be0a-82ec6461de8c',
  '2b5d70df-e679-4286-af11-f705f506105f',
  '9f4fe7a1-f5a7-470c-b2f3-5a79f3e0a7da',
  '79625620-84a2-49c6-9f1b-b6e10c906283',
  'a422d5d1-2ced-4333-817f-2a2200f8add8',
  '3c44c282-b26f-4525-9dfd-62d1edb75b7f',
  '47b4c932-e96a-5f83-b64d-55ab3497f10c',
  '047ce4d8-012a-5263-a871-3f83a3a7d3b3',
  '34ed1866-0642-5a9c-bd08-f1700e9b6df9',
  '14edb766-241e-5acd-b473-36de6b9258b7',
  'a9ce77ac-d1f9-519d-8890-91dd6aa238ec',
  '5d291184-99ca-57f1-9ec2-74f4c712f1b5',
  'a1a465fe-d325-4a63-a032-b3d4b1788aa0',
  '5eac13e7-a6a2-41f4-bd33-16d76a5a9e5c'
)
ON CONFLICT (vacancy_id, candidate_id) DO NOTHING;

COMMIT;

\echo === resumo links juridico ===
SELECT vc.stage, vc.status, count(*)
FROM vacancy_candidates vc
WHERE vc.vacancy_id = '610705ab-7a98-45e9-999a-5bdb62975989'
GROUP BY 1,2 ORDER BY 3 DESC;
