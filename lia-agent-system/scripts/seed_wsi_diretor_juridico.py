#!/usr/bin/env python3
"""
Seed WSI/Triagem data for Diretor Juridico vacancy.
Creates screening data for 3 candidates to enable the WSI modal.

Idempotent: uses fixed UUIDs so re-running is safe.

Run: cd /home/runner/workspace/lia-agent-system && python3 scripts/seed_wsi_diretor_juridico.py
"""
import asyncio
import hashlib
import json
import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, "/home/runner/workspace/lia-agent-system")
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

VACANCY_ID = "610705ab-7a98-45e9-999a-5bdb62975989"
COMPANY_ID = "00000000-0000-4000-a000-000000000001"
KAREN_ID = "14e03edf-5c20-52f3-af25-3cf4b2c6c820"
DEBORA_ID = "2b6a41c5-c625-50cf-814f-479b3d5d44d7"
FELIPE_ID = "2490d882-9d1d-5564-adf1-14cc6c6d2cf8"

# Fixed UUIDs for idempotent re-runs
KAREN_SESSION_ID = "a1000001-0000-4000-0000-000000000001"
FELIPE_SESSION_ID = "a1000001-0000-4000-0000-000000000002"
KAREN_RESULT_ID = "b2000001-0000-4000-0000-000000000001"
FELIPE_RESULT_ID = "b2000001-0000-4000-0000-000000000002"
KAREN_TRIAGEM_ID = "c3000001-0000-4000-0000-000000000001"
DEBORA_TRIAGEM_ID = "c3000001-0000-4000-0000-000000000002"
FELIPE_TRIAGEM_ID = "c3000001-0000-4000-0000-000000000003"

# Fixed question UUIDs per session (5 questions each)
KAREN_Q_IDS = [f"d400000{i}-0000-4000-0000-000000000001" for i in range(1, 6)]
FELIPE_Q_IDS = [f"d400000{i}-0000-4000-0000-000000000002" for i in range(1, 6)]

ELIGIBILITY_QUESTIONS = [
    {
        "id": "eq_001",
        "question": "Voce possui OAB ativa e em dia com anuidades?",
        "is_eliminatory": True,
        "expected_answer": "yes",
    },
    {
        "id": "eq_002",
        "question": "Voce tem disponibilidade para trabalho presencial em Sao Paulo (min. 3x/semana)?",
        "is_eliminatory": True,
        "expected_answer": "yes",
    },
    {
        "id": "eq_003",
        "question": "Voce possui ingles fluente para conduzir reunioes e negociacoes internacionais?",
        "is_eliminatory": True,
        "expected_answer": "yes",
    },
]

WSI_QUESTIONS = [
    # weight must be 0.0–1.0 (constraint); question_type must be one of:
    # autodeclaration | contextual | microcase | situational
    {
        "competency": "Governanca Corporativa",
        "framework": "CBI",
        "question_type": "situational",
        "question_text": "Descreva uma situacao em que voce estruturou ou reformou a governanca juridica de uma empresa. Quais foram os principais desafios e resultados?",
        "weight": 1.0,
        "expected_signals": ["estrutura de comites", "politicas internas", "compliance", "board"],
        "scoring_criteria": {"min_bloom": 4, "required_signals": 2, "context_weight": 0.4},
        "sequence_order": 1,
    },
    {
        "competency": "Gestao de Riscos Juridicos",
        "framework": "CBI",
        "question_type": "situational",  # 'behavioral' not valid; use 'situational'
        "question_text": "Conte sobre um momento em que identificou um risco juridico critico antes que se tornasse um passivo significativo. Como agiu?",
        "weight": 1.0,
        "expected_signals": ["identificacao proativa", "mitigacao", "comunicacao ao board", "follow-up"],
        "scoring_criteria": {"min_bloom": 4, "required_signals": 2, "context_weight": 0.4},
        "sequence_order": 2,
    },
    {
        "competency": "Lideranca e Influencia",
        "framework": "BigFive",
        "question_type": "contextual",
        "question_text": "Como voce conduz a area juridica para ser parceira estrategica do negocio, e nao apenas um centro de custo?",
        "weight": 0.9,
        "expected_signals": ["alinhamento estrategico", "KPIs", "parceria com C-level"],
        "scoring_criteria": {"min_bloom": 3, "required_signals": 2, "context_weight": 0.3},
        "sequence_order": 3,
    },
    {
        "competency": "Negociacao e Contratos",
        "framework": "CBI",
        "question_type": "contextual",
        "question_text": "Descreva a negociacao contratual mais complexa que liderou. Qual foi sua estrategia e resultado?",
        "weight": 1.0,
        "expected_signals": ["estrategia de negociacao", "valor gerado", "risco mitigado"],
        "scoring_criteria": {"min_bloom": 4, "required_signals": 2, "context_weight": 0.4},
        "sequence_order": 4,
    },
    {
        "competency": "Conformidade Regulatoria",
        "framework": "CBI",
        "question_type": "contextual",  # 'behavioral' not valid; use 'contextual'
        "question_text": "Como voce garante que a empresa se mantém em conformidade com novas regulamentacoes (ex: LGPD)?",
        "weight": 0.9,
        "expected_signals": ["monitoramento regulatorio", "treinamentos", "politicas", "auditorias"],
        "scoring_criteria": {"min_bloom": 3, "required_signals": 2, "context_weight": 0.3},
        "sequence_order": 5,
    },
]

KAREN_RESPONSES = [
    {
        "text": "Na minha ultima empresa, reestruturei o comite de governanca, criando tres subcomites especializados: contratos, compliance e litigios. Implementamos dashboards de indicadores juridicos apresentados mensalmente ao board. Em 18 meses reduzimos o passivo contingente em 34%.",
        "autodecl": 8.0, "ctx": 8.5, "bloom": 5, "dreyfus": 4, "final": 8.2,
        "evidences": ["Reestruturacao de comite com subcomites", "Dashboards ao board", "Reducao 34% passivo contingente"],
        "flags": [],
        "justification": "Candidata demonstra dominio senior em governanca com evidencias quantitativas solidas.",
    },
    {
        "text": "Identificamos via analise contratual que um fornecedor chave tinha clausula de change-of-control que poderia ser ativada pela M&A em andamento. Apresentei analise ao CEO com tres cenarios. Renegociamos antecipadamente evitando multa estimada em R$ 8M.",
        "autodecl": 7.5, "ctx": 8.0, "bloom": 5, "dreyfus": 4, "final": 7.8,
        "evidences": ["Identificacao proativa em M&A", "Analise de cenarios ao CEO", "Evitou multa R$8M"],
        "flags": [],
        "justification": "Excelente demonstracao de gestao de risco proativa com impacto financeiro mensuravel.",
    },
    {
        "text": "Criei um programa Juridico como Parceiro com SLAs de resposta por tipo de demanda, reunioes mensais com cada VP de negocio e participacao no comite de produto desde o inception. Nossa area passou de ser vista como bloqueio para enabler estrategico.",
        "autodecl": 7.5, "ctx": 7.8, "bloom": 4, "dreyfus": 4, "final": 7.6,
        "evidences": ["SLAs definidos", "Reunioes mensais com VPs", "Participacao no comite de produto"],
        "flags": [],
        "justification": "Demonstra maturidade em posicionamento estrategico da area juridica.",
    },
    {
        "text": "Conduzi a negociacao de contrato de licenciamento de tecnologia com parceiro europeu avaliado em 12M euros. Utilizei estrategia de ancoragem com benchmarks de mercado. Reduzimos royalties em 18% vs proposta inicial.",
        "autodecl": 8.5, "ctx": 8.0, "bloom": 5, "dreyfus": 5, "final": 8.3,
        "evidences": ["Negociacao de contrato EU 12M", "Benchmarks de mercado", "Reducao 18% royalties"],
        "flags": [],
        "justification": "Alta competencia em negociacao com impacto mensuravel.",
    },
    {
        "text": "Temos processo de regulatory scanning mensal mapeando publicacoes do DOU, CVM e Banco Central. Quando a LGPD entrou em vigor, coordenei o programa de adequacao em 8 meses, treinamos 200+ colaboradores e implementamos processos de DPIA.",
        "autodecl": 7.0, "ctx": 7.5, "bloom": 4, "dreyfus": 4, "final": 7.3,
        "evidences": ["Regulatory scanning sistematico", "Adequacao LGPD 8 meses", "200+ colaboradores treinados"],
        "flags": [],
        "justification": "Bom dominio em compliance regulatorio com processo estruturado.",
    },
]

FELIPE_RESPONSES = [
    {
        "text": "Fui responsavel pela reestruturacao completa da governanca juridica no IPO da empresa. Criamos estrutura de 4 comites com charters formais, implementamos politica de conflitos de interesse aprovada pelo conselho e estabelecemos canal de etica independente. Apos o IPO, fomos reconhecidos pela ISS com nota maxima em governanca.",
        "autodecl": 9.5, "ctx": 9.0, "bloom": 6, "dreyfus": 5, "final": 9.3,
        "evidences": ["Estrutura pre-IPO 4 comites", "Politica de conflitos pelo conselho", "Nota maxima ISS"],
        "flags": [],
        "justification": "Expertise excepcional em governanca com experiencia em operacoes de mercado de capitais.",
    },
    {
        "text": "Durante due diligence de aquisicao, identifiquei passivo ambiental oculto em imovel industrial nao refletido nos balancetes. Estruturei clausula de escrow com R$ 45M por 5 anos, obtive laudos tecnicos e negociei reducao de R$ 30M no preco de aquisicao. Passivo efetivo foi de R$ 12M.",
        "autodecl": 9.0, "ctx": 9.5, "bloom": 6, "dreyfus": 5, "final": 9.2,
        "evidences": ["Passivo ambiental oculto em M&A", "Escrow R$45M", "Reducao R$30M no preco"],
        "flags": [],
        "justification": "Analise de risco excepcional com impacto financeiro muito significativo.",
    },
    {
        "text": "Participei como membro votante do comite executivo por 3 anos, sendo o unico advogado nessa posicao. Desenvolvi metodo de legal lens para decisoes estrategicas: toda iniciativa maior passa por analise juridica na fase de planejamento, nao de execucao. Reduziu custos de adequacao em 60%.",
        "autodecl": 9.0, "ctx": 8.5, "bloom": 5, "dreyfus": 5, "final": 8.8,
        "evidences": ["Membro votante do comite executivo", "Metodo legal lens", "Reducao 60% custos de adequacao"],
        "flags": [],
        "justification": "Posicionamento estrategico excepcional da area juridica no nivel C-suite.",
    },
    {
        "text": "Liderei negociacao do maior contrato da historia da empresa: R$ 380M por 7 anos. Desenvolvemos estrategia com 3 BATNAs mapeados, utilizamos mediacao tecnica em pontos controversos e incluimos mecanismos de rebalanceamento automatico por inflacao. Estrutura adotada como template corporativo.",
        "autodecl": 9.5, "ctx": 9.0, "bloom": 6, "dreyfus": 5, "final": 9.3,
        "evidences": ["Contrato R$380M 7 anos", "3 BATNAs mapeados", "Adotado como template"],
        "flags": [],
        "justification": "Capacidade negocial excepcional com resultado de impacto estrategico duradouro.",
    },
    {
        "text": "Implementei programa de regulatory intelligence com monitoramento automatizado de 47 orgaos regulatorios. Criamos matriz de materialidade por impacto/probabilidade. Somos auditados por 6 reguladores e mantemos historico de zero notificacoes nos ultimos 4 anos.",
        "autodecl": 8.5, "ctx": 9.0, "bloom": 5, "dreyfus": 5, "final": 8.7,
        "evidences": ["Monitoramento 47 orgaos regulatorios", "Matriz de materialidade", "Zero notificacoes 4 anos"],
        "flags": [],
        "justification": "Gestao de compliance em nivel excepcional.",
    },
]


def _response_hash(session_id: str, question_id: str, response_text: str) -> str:
    """Generate deterministic hash for wsi_response_analyses.response_hash."""
    payload = f"{session_id}:{question_id}:{response_text[:100]}"
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


async def cleanup_existing(db):
    """Remove existing seed data by fixed IDs (idempotent)."""
    session_ids = [KAREN_SESSION_ID, FELIPE_SESSION_ID]
    triagem_ids = [KAREN_TRIAGEM_ID, DEBORA_TRIAGEM_ID, FELIPE_TRIAGEM_ID]

    # Order matters: child tables first
    await db.execute(text("DELETE FROM wsi_feedbacks WHERE wsi_result_id IN (:r1, :r2)"), {"r1": KAREN_RESULT_ID, "r2": FELIPE_RESULT_ID})
    await db.execute(text("DELETE FROM wsi_reports WHERE wsi_result_id IN (:r1, :r2)"), {"r1": KAREN_RESULT_ID, "r2": FELIPE_RESULT_ID})
    await db.execute(text("DELETE FROM wsi_results WHERE id IN (:r1, :r2)"), {"r1": KAREN_RESULT_ID, "r2": FELIPE_RESULT_ID})
    for sid in session_ids:
        await db.execute(text("DELETE FROM wsi_response_analyses WHERE session_id = :s"), {"s": sid})
        await db.execute(text("DELETE FROM wsi_questions WHERE session_id = :s"), {"s": sid})
    await db.execute(text("DELETE FROM wsi_sessions WHERE id IN (:s1, :s2)"), {"s1": KAREN_SESSION_ID, "s2": FELIPE_SESSION_ID})
    for tid in triagem_ids:
        await db.execute(text("DELETE FROM triagem_messages WHERE session_id = :t"), {"t": tid})
    await db.execute(text("DELETE FROM triagem_sessions WHERE id IN (:t1, :t2, :t3)"), {"t1": KAREN_TRIAGEM_ID, "t2": DEBORA_TRIAGEM_ID, "t3": FELIPE_TRIAGEM_ID})
    await db.commit()
    print("  Cleanup OK")


async def seed_triagem_karen(db):
    """Karen Monteiro: passed all eligibility, proceeding to WSI (completed)."""
    base_time = datetime.utcnow() - timedelta(days=3)
    meta = {
        "eligibility": {
            "questions": ELIGIBILITY_QUESTIONS,
            "phase": "complete",
            "index": 3,
        }
    }
    token = "seed-karen-" + KAREN_TRIAGEM_ID[-8:]
    await db.execute(
        text("""
            INSERT INTO triagem_sessions
              (id, token, candidate_id, candidate_name, candidate_email,
               job_id, job_title, company_id, company_name,
               status, current_block, total_blocks,
               wsi_final_score, recommendation,
               expires_at, started_at, completed_at,
               metadata_json)
            VALUES
              (:id, :token, :cid, :cname, :cemail,
               :jid, :jtitle, :coid, :coname,
               'completed', 5, 5,
               7.8, 'APROVADO',
               :exp, :start, :end,
               :meta)
        """),
        {
            "id": KAREN_TRIAGEM_ID,
            "token": token,
            "cid": KAREN_ID,
            "cname": "Karen Monteiro",
            "cemail": "karen.monteiro@example.com",
            "jid": VACANCY_ID,
            "jtitle": "Diretor(a) Juridico(a) (Chief Legal Officer)",
            "coid": COMPANY_ID,
            "coname": "WeDOTalent Demo",
            "exp": base_time + timedelta(days=7),
            "start": base_time,
            "end": base_time + timedelta(minutes=28),
            "meta": json.dumps(meta),
        },
    )
    # Eligibility answers from Karen
    answers = [
        "Sim, minha OAB esta ativa ha mais de 10 anos, com anuidades em dia.",
        "Sim, tenho total disponibilidade para trabalho presencial em Sao Paulo.",
        "Sim, trabalho em ingles diariamente ha 6 anos em reunioes com times internacionais.",
    ]
    for i, answer in enumerate(answers):
        await db.execute(
            text("""
                INSERT INTO triagem_messages (id, session_id, sender, content, message_type, wsi_block, created_at)
                VALUES (:id, :sid, 'candidate', :content, 'text', 999, :ts)
            """),
            {
                "id": str(uuid.uuid4()),
                "sid": KAREN_TRIAGEM_ID,
                "content": answer,
                "ts": base_time + timedelta(minutes=(i + 1) * 3),
            },
        )
    await db.commit()
    print("  Karen triagem: OK (status=completed, wsi_final_score=7.8)")


async def seed_triagem_debora(db):
    """Debora Freitas: eliminated at eligibility q3 (ingles)."""
    base_time = datetime.utcnow() - timedelta(days=5)
    meta = {
        "eligibility": {
            "questions": ELIGIBILITY_QUESTIONS,
            "phase": "talent_pool",
            "index": 2,
            "eliminated_reason": "Candidata nao atendeu ao criterio de ingles fluente.",
        }
    }
    token = "seed-debora-" + DEBORA_TRIAGEM_ID[-8:]
    await db.execute(
        text("""
            INSERT INTO triagem_sessions
              (id, token, candidate_id, candidate_name, candidate_email,
               job_id, job_title, company_id, company_name,
               status, current_block, total_blocks,
               wsi_final_score, recommendation,
               expires_at, started_at, completed_at,
               metadata_json)
            VALUES
              (:id, :token, :cid, :cname, :cemail,
               :jid, :jtitle, :coid, :coname,
               'talent_pool', 2, 5,
               NULL, 'NAO_ELEGIVEL',
               :exp, :start, :end,
               :meta)
        """),
        {
            "id": DEBORA_TRIAGEM_ID,
            "token": token,
            "cid": DEBORA_ID,
            "cname": "Debora Freitas",
            "cemail": "debora.freitas@example.com",
            "jid": VACANCY_ID,
            "jtitle": "Diretor(a) Juridico(a) (Chief Legal Officer)",
            "coid": COMPANY_ID,
            "coname": "WeDOTalent Demo",
            "exp": base_time + timedelta(days=7),
            "start": base_time,
            "end": base_time + timedelta(minutes=4),
            "meta": json.dumps(meta),
        },
    )
    answers = [
        "Sim, possuo OAB ativa ha 8 anos.",
        "Sim, tenho disponibilidade para trabalho presencial em Sao Paulo.",
        "Tenho ingles intermediario, consigo me comunicar mas nao me considero fluente.",
    ]
    for i, answer in enumerate(answers):
        await db.execute(
            text("""
                INSERT INTO triagem_messages (id, session_id, sender, content, message_type, wsi_block, created_at)
                VALUES (:id, :sid, 'candidate', :content, 'text', 999, :ts)
            """),
            {
                "id": str(uuid.uuid4()),
                "sid": DEBORA_TRIAGEM_ID,
                "content": answer,
                "ts": base_time + timedelta(minutes=(i + 1)),
            },
        )
    await db.commit()
    print("  Debora triagem: OK (status=talent_pool, eliminated at eligibility q3)")


async def seed_triagem_felipe(db):
    """Felipe Almeida: passed all eligibility, WSI completed (separate wsi_session)."""
    base_time = datetime.utcnow() - timedelta(days=10)
    meta = {
        "eligibility": {
            "questions": ELIGIBILITY_QUESTIONS,
            "phase": "complete",
            "index": 3,
        }
    }
    token = "seed-felipe-" + FELIPE_TRIAGEM_ID[-8:]
    await db.execute(
        text("""
            INSERT INTO triagem_sessions
              (id, token, candidate_id, candidate_name, candidate_email,
               job_id, job_title, company_id, company_name,
               status, current_block, total_blocks,
               wsi_final_score, recommendation,
               expires_at, started_at, completed_at,
               metadata_json)
            VALUES
              (:id, :token, :cid, :cname, :cemail,
               :jid, :jtitle, :coid, :coname,
               'completed', 5, 5,
               9.1, 'ALTAMENTE_RECOMENDADO',
               :exp, :start, :end,
               :meta)
        """),
        {
            "id": FELIPE_TRIAGEM_ID,
            "token": token,
            "cid": FELIPE_ID,
            "cname": "Felipe Almeida",
            "cemail": "felipe.almeida@example.com",
            "jid": VACANCY_ID,
            "jtitle": "Diretor(a) Juridico(a) (Chief Legal Officer)",
            "coid": COMPANY_ID,
            "coname": "WeDOTalent Demo",
            "exp": base_time + timedelta(days=7),
            "start": base_time,
            "end": base_time + timedelta(minutes=41),
            "meta": json.dumps(meta),
        },
    )
    answers = [
        "Sim, sou membro ativo da OAB ha 15 anos.",
        "Sim, trabalho presencialmente em Sao Paulo.",
        "Sim, ingles fluente — conduzo reunioes internacionais semanalmente.",
    ]
    for i, answer in enumerate(answers):
        await db.execute(
            text("""
                INSERT INTO triagem_messages (id, session_id, sender, content, message_type, wsi_block, created_at)
                VALUES (:id, :sid, 'candidate', :content, 'text', 999, :ts)
            """),
            {
                "id": str(uuid.uuid4()),
                "sid": FELIPE_TRIAGEM_ID,
                "content": answer,
                "ts": base_time + timedelta(minutes=(i + 1) * 2),
            },
        )
    await db.commit()
    print("  Felipe triagem: OK (status=completed, wsi_final_score=9.1)")


async def seed_wsi_karen(db):
    """Karen Monteiro: WSI session, 5 questions, 5 analyses, 1 result."""
    base_time = datetime.utcnow() - timedelta(days=3, minutes=-5)

    await db.execute(
        text("""
            INSERT INTO wsi_sessions
              (id, candidate_id, job_vacancy_id, screening_type, mode, status,
               started_at, completed_at, score)
            VALUES
              (:id, :cid, :jid, 'chat', 'compact', 'completed',
               :start, :end, 7.8)
        """),
        {
            "id": KAREN_SESSION_ID,
            "cid": KAREN_ID,
            "jid": VACANCY_ID,
            "start": base_time,
            "end": base_time + timedelta(minutes=28),
        },
    )

    for i, (qid, q, resp) in enumerate(zip(KAREN_Q_IDS, WSI_QUESTIONS, KAREN_RESPONSES)):
        await db.execute(
            text("""
                INSERT INTO wsi_questions
                  (id, session_id, competency, framework, question_type,
                   question_text, weight, expected_signals, scoring_criteria, sequence_order)
                VALUES
                  (:id, :sid, :comp, :fw, :qt, :txt, :weight, :signals, :criteria, :seq)
            """),
            {
                "id": qid,
                "sid": KAREN_SESSION_ID,
                "comp": q["competency"],
                "fw": q["framework"],
                "qt": q["question_type"],
                "txt": q["question_text"],
                "weight": q["weight"],
                "signals": json.dumps(q["expected_signals"]),
                "criteria": json.dumps(q["scoring_criteria"]),
                "seq": q["sequence_order"],
            },
        )
        rhash = _response_hash(KAREN_SESSION_ID, qid, resp["text"])
        await db.execute(
            text("""
                INSERT INTO wsi_response_analyses
                  (id, session_id, question_id, candidate_id, job_vacancy_id,
                   competency, response_text, response_hash,
                   autodeclaration_score, context_score, bloom_level, dreyfus_level,
                   final_score, justification, evidences, red_flags, consistency_penalty)
                VALUES
                  (:id, :sid, :qid, :cid, :jid,
                   :comp, :text, :hash,
                   :auto, :ctx, :bloom, :drey,
                   :final, :just, :ev, :rf, 0.0)
            """),
            {
                "id": str(uuid.uuid4()),
                "sid": KAREN_SESSION_ID,
                "qid": qid,
                "cid": KAREN_ID,
                "jid": VACANCY_ID,
                "comp": q["competency"],
                "text": resp["text"],
                "hash": rhash,
                "auto": resp["autodecl"],
                "ctx": resp["ctx"],
                "bloom": resp["bloom"],
                "drey": resp["dreyfus"],
                "final": resp["final"],
                "just": resp["justification"],
                "ev": json.dumps(resp["evidences"]),
                "rf": json.dumps(resp["flags"]),
            },
        )

    await db.execute(
        text("""
            INSERT INTO wsi_results
              (id, session_id, candidate_id, job_vacancy_id,
               technical_wsi, behavioral_wsi, overall_wsi, classification, percentile)
            VALUES
              (:id, :sid, :cid, :jid, 7.95, 7.60, 7.80, 'alto', 76)
        """),
        {
            "id": KAREN_RESULT_ID,
            "sid": KAREN_SESSION_ID,
            "cid": KAREN_ID,
            "jid": VACANCY_ID,
        },
    )
    await db.commit()
    print("  Karen WSI: OK (score=7.8, classification=alto, percentile=76)")


async def seed_wsi_felipe(db):
    """Felipe Almeida: WSI session, 5 questions, 5 analyses, 1 result."""
    base_time = datetime.utcnow() - timedelta(days=10, minutes=-5)

    await db.execute(
        text("""
            INSERT INTO wsi_sessions
              (id, candidate_id, job_vacancy_id, screening_type, mode, status,
               started_at, completed_at, score)
            VALUES
              (:id, :cid, :jid, 'chat', 'compact_plus', 'completed',
               :start, :end, 9.1)
        """),
        {
            "id": FELIPE_SESSION_ID,
            "cid": FELIPE_ID,
            "jid": VACANCY_ID,
            "start": base_time,
            "end": base_time + timedelta(minutes=41),
        },
    )

    for i, (qid, q, resp) in enumerate(zip(FELIPE_Q_IDS, WSI_QUESTIONS, FELIPE_RESPONSES)):
        await db.execute(
            text("""
                INSERT INTO wsi_questions
                  (id, session_id, competency, framework, question_type,
                   question_text, weight, expected_signals, scoring_criteria, sequence_order)
                VALUES
                  (:id, :sid, :comp, :fw, :qt, :txt, :weight, :signals, :criteria, :seq)
            """),
            {
                "id": qid,
                "sid": FELIPE_SESSION_ID,
                "comp": q["competency"],
                "fw": q["framework"],
                "qt": q["question_type"],
                "txt": q["question_text"],
                "weight": q["weight"],
                "signals": json.dumps(q["expected_signals"]),
                "criteria": json.dumps(q["scoring_criteria"]),
                "seq": q["sequence_order"],
            },
        )
        rhash = _response_hash(FELIPE_SESSION_ID, qid, resp["text"])
        await db.execute(
            text("""
                INSERT INTO wsi_response_analyses
                  (id, session_id, question_id, candidate_id, job_vacancy_id,
                   competency, response_text, response_hash,
                   autodeclaration_score, context_score, bloom_level, dreyfus_level,
                   final_score, justification, evidences, red_flags, consistency_penalty)
                VALUES
                  (:id, :sid, :qid, :cid, :jid,
                   :comp, :text, :hash,
                   :auto, :ctx, :bloom, :drey,
                   :final, :just, :ev, :rf, 0.0)
            """),
            {
                "id": str(uuid.uuid4()),
                "sid": FELIPE_SESSION_ID,
                "qid": qid,
                "cid": FELIPE_ID,
                "jid": VACANCY_ID,
                "comp": q["competency"],
                "text": resp["text"],
                "hash": rhash,
                "auto": resp["autodecl"],
                "ctx": resp["ctx"],
                "bloom": resp["bloom"],
                "drey": resp["dreyfus"],
                "final": resp["final"],
                "just": resp["justification"],
                "ev": json.dumps(resp["evidences"]),
                "rf": json.dumps(resp["flags"]),
            },
        )

    await db.execute(
        text("""
            INSERT INTO wsi_results
              (id, session_id, candidate_id, job_vacancy_id,
               technical_wsi, behavioral_wsi, overall_wsi, classification, percentile)
            VALUES
              (:id, :sid, :cid, :jid, 9.26, 8.92, 9.10, 'excepcional', 97)
        """),
        {
            "id": FELIPE_RESULT_ID,
            "sid": FELIPE_SESSION_ID,
            "cid": FELIPE_ID,
            "jid": VACANCY_ID,
        },
    )
    await db.commit()
    print("  Felipe WSI: OK (score=9.1, classification=excepcional, percentile=97)")


async def seed_eligibility_questions_on_vacancy(db):
    """Add eligibility questions to the vacancy if not already present."""
    r = await db.execute(
        text("SELECT eligibility_questions FROM job_vacancies WHERE id = :id"),
        {"id": VACANCY_ID},
    )
    row = r.fetchone()
    existing = row[0] if row else None
    if existing and isinstance(existing, list) and len(existing) > 0:
        print(f"  Vacancy already has {len(existing)} eligibility questions — skipping update")
        return
    await db.execute(
        text("UPDATE job_vacancies SET eligibility_questions = :q WHERE id = :id"),
        {"q": json.dumps(ELIGIBILITY_QUESTIONS), "id": VACANCY_ID},
    )
    await db.commit()
    print(f"  Vacancy eligibility questions: {len(ELIGIBILITY_QUESTIONS)} inserted")


async def verify_seed(db):
    """Print row counts for all seeded tables."""
    r = await db.execute(
        text("SELECT count(*) FROM triagem_sessions WHERE id IN (:t1,:t2,:t3)"),
        {"t1": KAREN_TRIAGEM_ID, "t2": DEBORA_TRIAGEM_ID, "t3": FELIPE_TRIAGEM_ID},
    )
    print(f"  triagem_sessions seeded: {r.scalar()}/3")

    r2 = await db.execute(
        text("SELECT count(*) FROM triagem_messages WHERE session_id IN (:t1,:t2,:t3)"),
        {"t1": KAREN_TRIAGEM_ID, "t2": DEBORA_TRIAGEM_ID, "t3": FELIPE_TRIAGEM_ID},
    )
    print(f"  triagem_messages seeded: {r2.scalar()} (expected 9)")

    r3 = await db.execute(
        text("SELECT count(*) FROM wsi_sessions WHERE id IN (:s1,:s2)"),
        {"s1": KAREN_SESSION_ID, "s2": FELIPE_SESSION_ID},
    )
    print(f"  wsi_sessions seeded: {r3.scalar()}/2")

    r4 = await db.execute(
        text("SELECT count(*) FROM wsi_questions WHERE session_id IN (:s1,:s2)"),
        {"s1": KAREN_SESSION_ID, "s2": FELIPE_SESSION_ID},
    )
    print(f"  wsi_questions seeded: {r4.scalar()} (expected 10)")

    r5 = await db.execute(
        text("SELECT count(*) FROM wsi_response_analyses WHERE session_id IN (:s1,:s2)"),
        {"s1": KAREN_SESSION_ID, "s2": FELIPE_SESSION_ID},
    )
    print(f"  wsi_response_analyses seeded: {r5.scalar()} (expected 10)")

    r6 = await db.execute(
        text("SELECT count(*) FROM wsi_results WHERE id IN (:r1,:r2)"),
        {"r1": KAREN_RESULT_ID, "r2": FELIPE_RESULT_ID},
    )
    print(f"  wsi_results seeded: {r6.scalar()}/2")

    # Quick score check
    r7 = await db.execute(
        text("SELECT candidate_id, overall_wsi, classification, percentile FROM wsi_results WHERE id IN (:r1,:r2) ORDER BY overall_wsi DESC"),
        {"r1": KAREN_RESULT_ID, "r2": FELIPE_RESULT_ID},
    )
    print("  WSI results:")
    for row in r7.fetchall():
        cname = "Felipe" if str(row[0]) == FELIPE_ID else "Karen"
        print(f"    {cname}: overall={row[1]}, class={row[2]}, pct={row[3]}")


async def main():
    print("Seeding WSI/Triagem data for Diretor Juridico (vacancy 610705ab)...")
    async with AsyncSessionLocal() as db:
        r = await db.execute(
            text("SELECT count(*) FROM candidates WHERE id IN (:k,:d,:f)"),
            {"k": KAREN_ID, "d": DEBORA_ID, "f": FELIPE_ID},
        )
        count = r.scalar()
        if count != 3:
            print(f"ERROR: Expected 3 candidates, found {count}. Aborting.")
            return
        print(f"  Candidates confirmed: {count}/3")

        r2 = await db.execute(
            text("SELECT id FROM job_vacancies WHERE id = :id"), {"id": VACANCY_ID}
        )
        if not r2.fetchone():
            print("ERROR: Vacancy not found. Aborting.")
            return
        print(f"  Vacancy confirmed: {VACANCY_ID}")

        print("Cleaning up existing seed data...")
        await cleanup_existing(db)

        print("Seeding eligibility questions on vacancy...")
        await seed_eligibility_questions_on_vacancy(db)

        print("Seeding triagem sessions...")
        await seed_triagem_karen(db)
        await seed_triagem_debora(db)
        await seed_triagem_felipe(db)

        print("Seeding WSI sessions (Karen + Felipe)...")
        await seed_wsi_karen(db)
        await seed_wsi_felipe(db)

        print("Verifying seed results...")
        await verify_seed(db)

    print("\nSeed complete.")
    print("  Karen Monteiro  : triagem completed + WSI 7.8/10 (alto, percentile 76)")
    print("  Debora Freitas  : triagem talent_pool — eliminated at eligibility q3")
    print("  Felipe Almeida  : triagem completed + WSI 9.1/10 (excepcional, percentile 97)")


if __name__ == "__main__":
    asyncio.run(main())
