"""
Seed Diretor Jurídico — Popula a vaga 610705ab com 12 candidatos ricos para demo.

Candidatos distribuídos em TODOS os estágios do kanban (exceto hired/placement).
Cada candidato tem: CV completo, educação, experiência, WSI, triagem, entrevistas.

Usage:
    python scripts/seed_diretor_juridico.py --seed   # insere dados
    python scripts/seed_diretor_juridico.py --clean  # remove dados deste seed

Idempotente: usa UUIDs determinísticos via uuid5.
"""
import asyncio
import argparse
import hashlib
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from lia_config.database import AsyncSessionLocal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ─── IDs Canônicos ──────────────────────────────────────────────────────────
COMPANY_ID = "00000000-0000-4000-a000-000000000001"
VACANCY_ID = "610705ab-7a98-45e9-999a-5bdb62975989"
VACANCY_TITLE = "Diretor(a) Jurídico(a) (Chief Legal Officer)"
SEED_TAG = "seed_diretor_juridico"

SEED_NS = uuid.UUID("b1b1b1b1-0000-4000-a000-610705ab7a98")

# IDs dos estágios da Demo Company (recruitment_stages where company_id = COMPANY_ID)
STAGE_IDS = {
    "sourcing":            "b85770d1-ef84-5622-aa76-7dddd432677f",
    "screening":           "08feb99a-588d-5e88-8b9f-47b191af6c13",
    "long_list":           "2d79e3a8-7ec9-549f-a1be-4b494079e31c",
    "short_list":          "a3bab07e-47cb-5dd4-8960-46e465339d21",
    "interview_hr":        "079249c8-a2fd-545c-8a1d-0ec483365839",
    "technical_test":      "859cc76b-fd3c-5b36-bddb-4351fa7d7ec7",
    "interview_technical": "585f497b-4a03-5715-9f45-19b11e050b00",
    "interview_manager":   "7036e4be-35e5-5080-8a2a-ef6c61b77816",
    "offer":               "5afe8376-a375-5034-a498-6457c809446e",
    "hired":               "e3054b9d-ad6c-5886-9e2b-ec2050ff295a",
    "rejected":            "0856af6e-1b2f-562b-b747-885787ccca83",
}

def _sid(label: str) -> str:
    return str(uuid.uuid5(SEED_NS, label))

def _dt(days_ago: float) -> datetime:
    return datetime.utcnow() - timedelta(days=days_ago)

def _dt_str(days_ago: float) -> str:
    return _dt(days_ago).isoformat()

NOW = datetime.utcnow()


# ─── Candidatos (12 perfis jurídicos realistas) ─────────────────────────────
# stage, status, lia_score, wsi_done, has_interview, profile_level
CANDIDATES = [
    # ── OFFER (1) — proposta em negociação ──────────────────────────
    {
        "key": "patricia_drummond",
        "name": "Patricia Drummond Tavares",
        "email": "patricia.drummond@email.com.br",
        "phone": "+55 11 99321-4578",
        "location_city": "São Paulo", "location_state": "SP",
        "current_title": "Sócia – Direito Corporativo & M&A",
        "current_company": "Drummond Tavares Advogados",
        "seniority_level": "executive", "years_of_experience": 22,
        "headline": "CLO | M&A | Governança Corporativa | 22 anos estruturando departamentos jurídicos",
        "self_introduction": (
            "Advogada com 22 anos de experiência, sendo 12 como sócia em M&A e Direito Corporativo. "
            "Liderou a estruturação do departamento jurídico da Votorantim Energia (2018-2022), "
            "gerenciando equipe de 14 advogados e orçamento de R$ 8M. "
            "Expertise em fusões, aquisições, joint ventures e governança para companhias abertas. "
            "MBA pela Wharton (EUA) e LLM pela University of London."
        ),
        "technical_skills": ["M&A", "Governança Corporativa", "Direito Societário", "Securities Law", "Due Diligence",
                              "Contratos Complexos", "Arbitragem Comercial", "CVM", "B3", "LGPD"],
        "soft_skills": ["Liderança estratégica", "Negociação", "Visão de negócios", "Gestão de equipes", "Comunicação executiva"],
        "languages": [{"language": "Português", "level": "Nativo"}, {"language": "Inglês", "level": "Fluente"}, {"language": "Espanhol", "level": "Avançado"}],
        "certifications": ["OAB-SP 189.XXX", "CPA-20 (Ancord)", "Fellow – Institute of Directors (IoD-UK)"],
        "current_salary": 85000.0, "salary_currency": "BRL",
        "desired_salary_min": 90000.0, "desired_salary_max": 110000.0,
        "linkedin_url": "https://linkedin.com/in/patriciadrummondtavares",
        "work_model_preference": "hybrid", "contract_type_preference": "CLT",
        "willing_to_relocate": False, "is_remote": False, "is_open_to_work": True,
        "stage": "offer", "status": "offer", "lia_score": 94.5,
        "wsi_done": True, "has_interview": True, "profile_level": "excelente",
        "education": [
            {"institution": "Universidade de São Paulo (USP)", "degree": "Bacharelado em Direito",
             "field": "Direito", "city": "São Paulo", "state": "SP", "start": "1997-02", "end": "2001-12"},
            {"institution": "Wharton School – University of Pennsylvania", "degree": "MBA",
             "field": "Finanças e Direito Corporativo", "city": "Philadelphia", "state": "PA", "start": "2006-09", "end": "2008-06"},
            {"institution": "University of London", "degree": "LLM (Mestre em Direito)",
             "field": "International Corporate Law", "city": "Londres", "state": "", "start": "2009-01", "end": "2009-12"},
        ],
        "experiences": [
            {"company": "Drummond Tavares Advogados", "title": "Sócia – M&A & Direito Corporativo",
             "start": "2022-03", "end": None, "is_current": True,
             "description": "Fundação e gestão de boutique especializada em M&A mid-market. 12 transações concluídas (R$ 340M total)."},
            {"company": "Votorantim Energia", "title": "Diretora Jurídica (CLO)",
             "start": "2018-01", "end": "2022-02", "is_current": False,
             "description": "Liderou equipe de 14 advogados. Reestruturou área jurídica pós-fusão. Supervisionou 3 IPOs e 7 M&As."},
            {"company": "Machado Meyer Advogados", "title": "Advogada Sênior – M&A",
             "start": "2012-06", "end": "2017-12", "is_current": False,
             "description": "M&A e mercado de capitais. 45+ transações. Clientes: Vale, Itaúsa, BRF, Embraer."},
            {"company": "Pinheiro Neto Advogados", "title": "Advogada Associada",
             "start": "2002-03", "end": "2012-05", "is_current": False,
             "description": "Entrada como trainee. Evolução para sênior em Direito Societário e Contratos Complexos."},
        ],
    },

    # ── INTERVIEW_MANAGER (1) — entrevista com gestor ────────────────
    {
        "key": "eduardo_britto",
        "name": "Eduardo Carvalho Britto",
        "email": "eduardo.britto@protonmail.com",
        "phone": "+55 11 98765-4321",
        "location_city": "São Paulo", "location_state": "SP",
        "current_title": "Vice-Presidente Jurídico",
        "current_company": "Itaú Unibanco",
        "seniority_level": "executive", "years_of_experience": 20,
        "headline": "VP Jurídico | Tributário | Regulatório Bancário | Gestão de riscos legais em larga escala",
        "self_introduction": (
            "20 anos em grandes instituições financeiras. Atualmente VP Jurídico no Itaú, "
            "responsável por equipe de 28 advogados e gestão de passivo tributário de R$ 4,2 bilhões. "
            "Especialista em Direito Tributário, Regulatório Bancário (Bacen/CMN) e LGPD. "
            "Pós-graduação em Direito Tributário pela PUC-SP e MBA pela FGV-SP."
        ),
        "technical_skills": ["Direito Tributário", "Regulatório Bancário", "BACEN", "CMN", "LGPD",
                              "Planejamento Tributário", "Contencioso Tributário", "Gestão de Passivos",
                              "Compliance Bancário", "Parecer Jurídico"],
        "soft_skills": ["Liderança", "Gestão de times grandes", "Negociação com reguladores", "Comunicação executiva"],
        "languages": [{"language": "Português", "level": "Nativo"}, {"language": "Inglês", "level": "Avançado"}],
        "certifications": ["OAB-SP 156.XXX", "Pós-Tributário PUC-SP", "MBA FGV-SP"],
        "current_salary": 78000.0, "salary_currency": "BRL",
        "desired_salary_min": 82000.0, "desired_salary_max": 100000.0,
        "linkedin_url": "https://linkedin.com/in/eduardocarvalhobritto",
        "work_model_preference": "hybrid", "contract_type_preference": "CLT",
        "willing_to_relocate": False, "is_remote": False, "is_open_to_work": False,
        "stage": "interview_manager", "status": "approved", "lia_score": 88.0,
        "wsi_done": True, "has_interview": True, "profile_level": "excelente",
        "education": [
            {"institution": "Pontifícia Universidade Católica de São Paulo (PUC-SP)",
             "degree": "Bacharelado em Direito", "field": "Direito",
             "city": "São Paulo", "state": "SP", "start": "1998-02", "end": "2002-12"},
            {"institution": "PUC-SP", "degree": "Pós-graduação",
             "field": "Direito Tributário", "city": "São Paulo", "state": "SP", "start": "2004-02", "end": "2005-12"},
            {"institution": "FGV São Paulo", "degree": "MBA",
             "field": "Gestão Empresarial", "city": "São Paulo", "state": "SP", "start": "2010-03", "end": "2011-12"},
        ],
        "experiences": [
            {"company": "Itaú Unibanco", "title": "Vice-Presidente Jurídico",
             "start": "2019-05", "end": None, "is_current": True,
             "description": "Liderança de 28 advogados. Gestão de passivo tributário R$ 4,2B. Interface Bacen/CMN."},
            {"company": "Bradesco Seguros", "title": "Diretor Jurídico",
             "start": "2014-01", "end": "2019-04", "is_current": False,
             "description": "Implementação compliance LGPD antecipada. Reestruturação contencioso."},
            {"company": "KPMG Advogados", "title": "Sênior Manager – Tax & Legal",
             "start": "2007-03", "end": "2013-12", "is_current": False,
             "description": "Auditoria tributária e consultoria. Clientes do setor financeiro."},
            {"company": "Machado Associados", "title": "Advogado Tributarista",
             "start": "2003-02", "end": "2007-02", "is_current": False,
             "description": "Planejamento tributário e contencioso administrativo."},
        ],
    },

    # ── INTERVIEW_HR (1) — entrevista RH realizada ───────────────────
    {
        "key": "fernanda_leal",
        "name": "Fernanda Leal Santos",
        "email": "fernanda.leal.santos@gmail.com",
        "phone": "+55 21 99876-5432",
        "location_city": "Rio de Janeiro", "location_state": "RJ",
        "current_title": "Gerente Sênior Jurídico – M&A & Transações",
        "current_company": "Vale S.A.",
        "seniority_level": "senior", "years_of_experience": 15,
        "headline": "M&A | Due Diligence | Direito Internacional | 15 anos em empresas globais",
        "self_introduction": (
            "Advogada corporativa com 15 anos em M&A e transações internacionais. "
            "Na Vale desde 2016, responsável por due diligence e estruturação de desinvestimentos. "
            "Participou de 12 transações internacionais (US$ 2,4B no total). "
            "LLM pela Universidade de Cambridge, fluente em inglês e francês."
        ),
        "technical_skills": ["M&A Internacional", "Due Diligence", "Contratos Internacionais",
                              "Direito Societário", "Desinvestimentos", "Joint Ventures",
                              "Securities US/BR", "ESG Legal", "Arbitragem Internacional"],
        "soft_skills": ["Pensamento estratégico", "Trabalho em equipe cross-cultural", "Gestão de projetos complexos"],
        "languages": [{"language": "Português", "level": "Nativo"}, {"language": "Inglês", "level": "Fluente"}, {"language": "Francês", "level": "Avançado"}],
        "certifications": ["OAB-RJ 198.XXX", "LLM Cambridge", "ISO 37001 Compliance Officer"],
        "current_salary": 55000.0, "salary_currency": "BRL",
        "desired_salary_min": 65000.0, "desired_salary_max": 85000.0,
        "linkedin_url": "https://linkedin.com/in/fernandaleal-santos",
        "work_model_preference": "hybrid", "contract_type_preference": "CLT",
        "willing_to_relocate": True, "is_remote": False, "is_open_to_work": True,
        "stage": "interview_hr", "status": "approved", "lia_score": 82.5,
        "wsi_done": True, "has_interview": True, "profile_level": "alto",
        "education": [
            {"institution": "Universidade Federal do Rio de Janeiro (UFRJ)",
             "degree": "Bacharelado em Direito", "field": "Direito",
             "city": "Rio de Janeiro", "state": "RJ", "start": "2004-02", "end": "2008-12"},
            {"institution": "University of Cambridge", "degree": "LLM",
             "field": "Corporate and Commercial Law", "city": "Cambridge", "state": "", "start": "2011-10", "end": "2012-09"},
        ],
        "experiences": [
            {"company": "Vale S.A.", "title": "Gerente Sênior Jurídico – M&A",
             "start": "2016-02", "end": None, "is_current": True,
             "description": "Due diligence e estruturação de 12 transações internacionais (US$ 2,4B). Gestão de equipe de 6 advogados."},
            {"company": "Embraer", "title": "Advogada Sênior – Contratos Internacionais",
             "start": "2012-10", "end": "2016-01", "is_current": False,
             "description": "Contratos com clientes de defesa e aviação civil. Direito aéreo internacional."},
            {"company": "Linklaters (Londres)", "title": "Advogada Associada – M&A",
             "start": "2009-01", "end": "2012-09", "is_current": False,
             "description": "M&A em transações envolvendo empresas brasileiras no mercado europeu."},
        ],
    },

    # ── SHORT_LIST (2) — selecionados para entrevista ─────────────────
    {
        "key": "rafael_monteiro",
        "name": "Rafael Monteiro Costa",
        "email": "rafael.monteiro.costa@outlook.com",
        "phone": "+55 11 97654-3210",
        "location_city": "São Paulo", "location_state": "SP",
        "current_title": "Diretor de Compliance e Regulatório",
        "current_company": "Bradesco Seguros",
        "seniority_level": "director", "years_of_experience": 17,
        "headline": "Compliance | Regulatório | Seguros | SUSEP | Prevenção a Lavagem",
        "self_introduction": (
            "17 anos em compliance e regulatório no setor de seguros. "
            "Responsável por adequação LGPD, PLD-FT e SUSEP. "
            "Experiente em gestão de crise regulatória e relacionamento com reguladores."
        ),
        "technical_skills": ["Compliance", "Regulatório Seguros", "SUSEP", "PLD-FT", "LGPD",
                              "Gestão de Riscos", "Controles Internos", "Auditoria Regulatória"],
        "soft_skills": ["Liderança", "Ética", "Comunicação com reguladores", "Gestão de crise"],
        "languages": [{"language": "Português", "level": "Nativo"}, {"language": "Inglês", "level": "Intermediário"}],
        "certifications": ["OAB-SP 201.XXX", "CFE (Certified Fraud Examiner)", "CAMS (Anti-Money Laundering)"],
        "current_salary": 52000.0, "salary_currency": "BRL",
        "desired_salary_min": 60000.0, "desired_salary_max": 80000.0,
        "linkedin_url": "https://linkedin.com/in/rafaelmonteirocosta",
        "work_model_preference": "presential", "contract_type_preference": "CLT",
        "willing_to_relocate": False, "is_remote": False, "is_open_to_work": True,
        "stage": "short_list", "status": "approved", "lia_score": 79.0,
        "wsi_done": True, "has_interview": False, "profile_level": "alto",
        "education": [
            {"institution": "Universidade Presbiteriana Mackenzie", "degree": "Bacharelado em Direito",
             "field": "Direito", "city": "São Paulo", "state": "SP", "start": "2002-02", "end": "2006-12"},
            {"institution": "FGV-SP", "degree": "Pós-graduação",
             "field": "Direito Regulatório e Compliance", "city": "São Paulo", "state": "SP", "start": "2008-02", "end": "2009-12"},
        ],
        "experiences": [
            {"company": "Bradesco Seguros", "title": "Diretor de Compliance e Regulatório",
             "start": "2018-03", "end": None, "is_current": True,
             "description": "Liderança de equipe de 9. Gestão LGPD, PLD-FT, SUSEP. Sem multas regulatórias em 6 anos."},
            {"company": "Mapfre Seguros", "title": "Gerente de Compliance",
             "start": "2014-01", "end": "2018-02", "is_current": False,
             "description": "Implementação do programa compliance grupo. Auditoria interna."},
            {"company": "KPMG", "title": "Auditor Sênior – Riscos e Compliance",
             "start": "2008-06", "end": "2013-12", "is_current": False,
             "description": "Auditoria de compliance e gestão de riscos para clientes financeiros."},
        ],
    },
    {
        "key": "beatriz_rocha",
        "name": "Beatriz Rocha Alves",
        "email": "beatriz.rocha.alves@gmail.com",
        "phone": "+55 11 96543-2109",
        "location_city": "São Paulo", "location_state": "SP",
        "current_title": "Gerente Jurídico – Direito Internacional e Contratos",
        "current_company": "Embraer S.A.",
        "seniority_level": "senior", "years_of_experience": 14,
        "headline": "Contratos Internacionais | Aviação | Exportação | Disputas Internacionais",
        "self_introduction": (
            "14 anos na Embraer com foco em contratos internacionais, exportação e disputas. "
            "Experiência com clientes governamentais de 22 países. "
            "Especialista em arbitragem ICC e contratos de defesa."
        ),
        "technical_skills": ["Contratos Internacionais", "Direito Aeronáutico", "Exportação/Importação",
                              "Arbitragem ICC", "Direito da Defesa", "ITAR Compliance", "Trade Compliance"],
        "soft_skills": ["Negociação internacional", "Visão global", "Gestão de contratos complexos"],
        "languages": [{"language": "Português", "level": "Nativo"}, {"language": "Inglês", "level": "Fluente"}, {"language": "Espanhol", "level": "Avançado"}],
        "certifications": ["OAB-SP 217.XXX", "LL.M Comercial Internacional USP"],
        "current_salary": 45000.0, "salary_currency": "BRL",
        "desired_salary_min": 58000.0, "desired_salary_max": 75000.0,
        "linkedin_url": "https://linkedin.com/in/beatrizrochaalves",
        "work_model_preference": "hybrid", "contract_type_preference": "CLT",
        "willing_to_relocate": True, "is_remote": False, "is_open_to_work": True,
        "stage": "short_list", "status": "approved", "lia_score": 76.5,
        "wsi_done": True, "has_interview": False, "profile_level": "alto",
        "education": [
            {"institution": "Universidade Estadual de Campinas (Unicamp)",
             "degree": "Bacharelado em Direito", "field": "Direito",
             "city": "Campinas", "state": "SP", "start": "2004-02", "end": "2008-12"},
            {"institution": "USP – Largo São Francisco",
             "degree": "LL.M", "field": "Direito Comercial Internacional",
             "city": "São Paulo", "state": "SP", "start": "2010-03", "end": "2011-12"},
        ],
        "experiences": [
            {"company": "Embraer S.A.", "title": "Gerente Jurídico – Direito Internacional",
             "start": "2013-04", "end": None, "is_current": True,
             "description": "Contratos com 22 países. Gestão de 4 advogados. Disputas ICC."},
            {"company": "Tozzini Freire Advogados", "title": "Advogada – Direito Internacional",
             "start": "2009-02", "end": "2013-03", "is_current": False,
             "description": "Contratos internacionais, CISG, arbitragem."},
        ],
    },

    # ── LONG_LIST (2) — aprovados na triagem ─────────────────────────
    {
        "key": "gustavo_novaes",
        "name": "Gustavo Novaes Lima",
        "email": "gustavo.novaes.lima@hotmail.com",
        "phone": "+55 21 95432-1098",
        "location_city": "Rio de Janeiro", "location_state": "RJ",
        "current_title": "Gerente Jurídico – Trabalhista e Sindical",
        "current_company": "Ambev S.A.",
        "seniority_level": "senior", "years_of_experience": 13,
        "headline": "Direito Trabalhista | Sindical | Gestão de Passivos | Grandes Empresas",
        "self_introduction": (
            "13 anos em grandes empresas (Ambev, Petrobras) com foco em direito trabalhista. "
            "Gerencia carteira com +18.000 ações. Reduziu passivo trabalhista em 32% em 3 anos."
        ),
        "technical_skills": ["Direito Trabalhista", "Contencioso Trabalhista", "Sindicato",
                              "Negociação Coletiva", "Passivo Trabalhista", "CLT",
                              "Reforma Trabalhista", "TST", "TRT"],
        "soft_skills": ["Negociação sindical", "Gestão de equipes", "Foco em resultados", "Análise de risco"],
        "languages": [{"language": "Português", "level": "Nativo"}, {"language": "Inglês", "level": "Básico"}],
        "certifications": ["OAB-RJ 178.XXX", "Pós-Direito Trabalhista PUC-Rio"],
        "current_salary": 38000.0, "salary_currency": "BRL",
        "desired_salary_min": 50000.0, "desired_salary_max": 65000.0,
        "linkedin_url": "https://linkedin.com/in/gustavonovaeslima",
        "work_model_preference": "hybrid", "contract_type_preference": "CLT",
        "willing_to_relocate": False, "is_remote": False, "is_open_to_work": True,
        "stage": "long_list", "status": "approved", "lia_score": 71.0,
        "wsi_done": True, "has_interview": False, "profile_level": "medio",
        "education": [
            {"institution": "PUC-Rio", "degree": "Bacharelado em Direito",
             "field": "Direito", "city": "Rio de Janeiro", "state": "RJ", "start": "2006-02", "end": "2010-12"},
            {"institution": "PUC-Rio", "degree": "Pós-graduação",
             "field": "Direito do Trabalho", "city": "Rio de Janeiro", "state": "RJ", "start": "2012-02", "end": "2013-12"},
        ],
        "experiences": [
            {"company": "Ambev S.A.", "title": "Gerente Jurídico – Trabalhista",
             "start": "2017-06", "end": None, "is_current": True,
             "description": "Carteira de 18.000 ações. Equipe de 8 advogados. Redução passivo -32%."},
            {"company": "Petrobras", "title": "Advogado Sênior – Trabalhista",
             "start": "2012-02", "end": "2017-05", "is_current": False,
             "description": "Gestão de ações coletivas e negociação com sindicatos."},
            {"company": "Goulart Penteado Advogados", "title": "Advogado Trabalhista",
             "start": "2010-06", "end": "2012-01", "is_current": False,
             "description": "Contencioso trabalhista para empresas de médio porte."},
        ],
    },
    {
        "key": "camila_azevedo",
        "name": "Camila Azevedo Pinto",
        "email": "camila.azevedo.pinto@uol.com.br",
        "phone": "+55 61 94321-0987",
        "location_city": "Brasília", "location_state": "DF",
        "current_title": "Advogada – Regulatório e Agências",
        "current_company": "Petrobras",
        "seniority_level": "senior", "years_of_experience": 11,
        "headline": "Direito Regulatório | ANP | ANEEL | ANATEL | Setor de Energia",
        "self_introduction": (
            "11 anos em direito regulatório com foco em agências (ANP, ANEEL, ANATEL). "
            "Atuou em processos administrativos de grande porte no setor de petróleo e energia. "
            "Experiência em Brasília com acesso a reguladores e visão de política regulatória."
        ),
        "technical_skills": ["Direito Regulatório", "ANP", "ANEEL", "ANATEL", "Petróleo e Gás",
                              "Processos Administrativos", "Consultas Públicas", "Licenciamento"],
        "soft_skills": ["Relacionamento institucional", "Análise regulatória", "Redação jurídica"],
        "languages": [{"language": "Português", "level": "Nativo"}, {"language": "Inglês", "level": "Intermediário"}],
        "certifications": ["OAB-DF 23.XXX", "Pós-Regulação INSPER"],
        "current_salary": 28000.0, "salary_currency": "BRL",
        "desired_salary_min": 40000.0, "desired_salary_max": 60000.0,
        "linkedin_url": "https://linkedin.com/in/camilaazevedopinto",
        "work_model_preference": "remote", "contract_type_preference": "CLT",
        "willing_to_relocate": True, "is_remote": True, "is_open_to_work": True,
        "stage": "long_list", "status": "approved", "lia_score": 67.5,
        "wsi_done": True, "has_interview": False, "profile_level": "medio",
        "education": [
            {"institution": "Universidade de Brasília (UnB)",
             "degree": "Bacharelado em Direito", "field": "Direito",
             "city": "Brasília", "state": "DF", "start": "2008-02", "end": "2012-12"},
            {"institution": "INSPER", "degree": "Pós-graduação",
             "field": "Regulação e Direito Econômico", "city": "São Paulo", "state": "SP", "start": "2015-02", "end": "2016-12"},
        ],
        "experiences": [
            {"company": "Petrobras", "title": "Advogada Sênior – Regulatório",
             "start": "2018-04", "end": None, "is_current": True,
             "description": "Processos administrativos ANP. Licenciamento ambiental e exploratório."},
            {"company": "Tozzini Freire", "title": "Advogada – Regulatório",
             "start": "2014-02", "end": "2018-03", "is_current": False,
             "description": "Consultoria regulatória para clientes de energia e telecom."},
            {"company": "Advocacia Geral da União (AGU)", "title": "Advogada da União",
             "start": "2012-08", "end": "2014-01", "is_current": False,
             "description": "Defesa da União em processos administrativos e judiciais."},
        ],
    },

    # ── SCREENING (3) — em triagem/análise ───────────────────────────
    {
        "key": "marcelo_duarte",
        "name": "Marcelo Duarte Gomes",
        "email": "marcelo.duarte.gomes@terra.com.br",
        "phone": "+55 11 93210-9876",
        "location_city": "São Paulo", "location_state": "SP",
        "current_title": "Coordenador Jurídico – Contratos e Comercial",
        "current_company": "TIM Brasil",
        "seniority_level": "senior", "years_of_experience": 9,
        "headline": "Contratos Comerciais | Telecom | Gestão de Fornecedores | CLT e PJ",
        "self_introduction": (
            "9 anos em jurídico corporativo com foco em contratos e gestão de fornecedores. "
            "TIM há 5 anos, gerenciando mais de 400 contratos simultâneos. "
            "Interesse em evolução para gerência/direção em empresa de médio porte."
        ),
        "technical_skills": ["Contratos Comerciais", "Gestão de Fornecedores", "SLA/OLA",
                              "Direito Telecomunicações", "ANATEL", "Terceirização", "NDA"],
        "soft_skills": ["Organização", "Atenção a detalhes", "Gestão de demandas", "Proatividade"],
        "languages": [{"language": "Português", "level": "Nativo"}, {"language": "Inglês", "level": "Básico"}],
        "certifications": ["OAB-SP 233.XXX"],
        "current_salary": 18000.0, "salary_currency": "BRL",
        "desired_salary_min": 28000.0, "desired_salary_max": 40000.0,
        "linkedin_url": "https://linkedin.com/in/marceloduartegomes",
        "work_model_preference": "hybrid", "contract_type_preference": "CLT",
        "willing_to_relocate": False, "is_remote": False, "is_open_to_work": True,
        "stage": "screening", "status": "screening", "lia_score": 55.0,
        "wsi_done": False, "has_interview": False, "profile_level": "medio",
        "education": [
            {"institution": "Universidade Anhembi Morumbi", "degree": "Bacharelado em Direito",
             "field": "Direito", "city": "São Paulo", "state": "SP", "start": "2010-02", "end": "2014-12"},
        ],
        "experiences": [
            {"company": "TIM Brasil", "title": "Coordenador Jurídico – Contratos",
             "start": "2019-06", "end": None, "is_current": True,
             "description": "Gestão de 400+ contratos. Revisão de SLAs e cláusulas de multa."},
            {"company": "Claro Brasil", "title": "Analista Jurídico",
             "start": "2016-01", "end": "2019-05", "is_current": False,
             "description": "Análise de contratos comerciais e suporte ao setor de compras."},
        ],
    },
    {
        "key": "ana_falcao",
        "name": "Ana Cristina Falcão Mendes",
        "email": "ana.falcao.mendes@gmail.com",
        "phone": "+55 31 92109-8765",
        "location_city": "Belo Horizonte", "location_state": "MG",
        "current_title": "Gerente Jurídico",
        "current_company": "Usiminas",
        "seniority_level": "manager", "years_of_experience": 12,
        "headline": "Gerente Jurídico | Mineração | Ambiental | Licenciamento",
        "self_introduction": (
            "12 anos em jurídico na indústria de mineração e siderurgia. "
            "Foco em licenciamento ambiental, mineração e relações fundiárias. "
            "Busca posição executiva em empresa de grande porte com desafios de expansão."
        ),
        "technical_skills": ["Direito Ambiental", "Licenciamento Ambiental", "Mineração",
                              "Direito Fundiário", "DNPM/ANM", "IBAMA", "AIA"],
        "soft_skills": ["Liderança", "Gestão de projetos", "Negociação com órgãos públicos"],
        "languages": [{"language": "Português", "level": "Nativo"}, {"language": "Inglês", "level": "Intermediário"}],
        "certifications": ["OAB-MG 98.XXX", "Pós-Direito Ambiental UFMG"],
        "current_salary": 22000.0, "salary_currency": "BRL",
        "desired_salary_min": 35000.0, "desired_salary_max": 55000.0,
        "linkedin_url": "https://linkedin.com/in/anacristina-falcao",
        "work_model_preference": "presential", "contract_type_preference": "CLT",
        "willing_to_relocate": True, "is_remote": False, "is_open_to_work": True,
        "stage": "screening", "status": "screening", "lia_score": 58.5,
        "wsi_done": False, "has_interview": False, "profile_level": "medio",
        "education": [
            {"institution": "PUC Minas", "degree": "Bacharelado em Direito",
             "field": "Direito", "city": "Belo Horizonte", "state": "MG", "start": "2006-02", "end": "2010-12"},
            {"institution": "UFMG", "degree": "Pós-graduação",
             "field": "Direito Ambiental", "city": "Belo Horizonte", "state": "MG", "start": "2012-03", "end": "2013-12"},
        ],
        "experiences": [
            {"company": "Usiminas", "title": "Gerente Jurídico",
             "start": "2019-02", "end": None, "is_current": True,
             "description": "Gestão do jurídico de mineração. Licenciamentos IBAMA/IEF. Equipe de 5 advogados."},
            {"company": "Vale S.A.", "title": "Advogada Sênior – Ambiental",
             "start": "2014-03", "end": "2019-01", "is_current": False,
             "description": "Processos de licenciamento ambiental complexos. EIA/RIMA."},
            {"company": "Advocacia Ambiental MG", "title": "Advogada",
             "start": "2011-01", "end": "2014-02", "is_current": False,
             "description": "Contencioso ambiental e consultoria para empresas de mineração."},
        ],
    },
    {
        "key": "roberto_neves",
        "name": "Roberto Henrique Neves Barros",
        "email": "roberto.neves.barros@yahoo.com.br",
        "phone": "+55 11 91098-7654",
        "location_city": "São Paulo", "location_state": "SP",
        "current_title": "Advogado Pleno – Corporativo e Societário",
        "current_company": "Souza Cescon Barrieu & Flesch Advogados",
        "seniority_level": "pleno", "years_of_experience": 7,
        "headline": "Societário | Contratos | M&A Entry-Level | Escritório Top-Tier",
        "self_introduction": (
            "7 anos em escritório top-tier de SP com foco em direito societário e M&A. "
            "Assistiu em 8 transações. Busca primeiro cargo in-house em empresa de grande porte."
        ),
        "technical_skills": ["Direito Societário", "Contratos", "M&A", "Due Diligence",
                              "Reorganizações Societárias", "Atos Societários", "JUCESP"],
        "soft_skills": ["Rigor técnico", "Responsabilidade", "Aprendizagem rápida", "Trabalho sob pressão"],
        "languages": [{"language": "Português", "level": "Nativo"}, {"language": "Inglês", "level": "Avançado"}],
        "certifications": ["OAB-SP 248.XXX"],
        "current_salary": 14000.0, "salary_currency": "BRL",
        "desired_salary_min": 22000.0, "desired_salary_max": 35000.0,
        "linkedin_url": "https://linkedin.com/in/roberto-neves-barros",
        "work_model_preference": "hybrid", "contract_type_preference": "CLT",
        "willing_to_relocate": False, "is_remote": False, "is_open_to_work": True,
        "stage": "screening", "status": "screening", "lia_score": 48.0,
        "wsi_done": False, "has_interview": False, "profile_level": "regular",
        "education": [
            {"institution": "Universidade de São Paulo (USP)",
             "degree": "Bacharelado em Direito", "field": "Direito",
             "city": "São Paulo", "state": "SP", "start": "2012-02", "end": "2016-12"},
        ],
        "experiences": [
            {"company": "Souza Cescon Barrieu & Flesch", "title": "Advogado Pleno",
             "start": "2019-01", "end": None, "is_current": True,
             "description": "Societário e M&A. Assistência em 8 transações."},
            {"company": "Mattos Filho Advogados", "title": "Advogado Trainee/Júnior",
             "start": "2016-08", "end": "2018-12", "is_current": False,
             "description": "Contratos e atos societários."},
        ],
    },

    # ── SOURCING (2) — identificados/contatados ───────────────────────
    {
        "key": "lucia_figueiredo",
        "name": "Lucia Figueiredo Almeida",
        "email": "lucia.figueiredo@protonmail.com",
        "phone": "+55 11 90987-6543",
        "location_city": "São Paulo", "location_state": "SP",
        "current_title": "General Counsel",
        "current_company": "Totvs S.A.",
        "seniority_level": "executive", "years_of_experience": 18,
        "headline": "General Counsel | Tecnologia | Contratos SaaS | Propriedade Intelectual",
        "self_introduction": (
            "18 anos em tech companies. General Counsel na Totvs há 4 anos, "
            "liderando jurídico de empresa com +12.000 clientes e receita de R$ 4B. "
            "Expertise em contratos SaaS, PI, privacidade e compliance global."
        ),
        "technical_skills": ["Contratos SaaS", "Propriedade Intelectual", "LGPD", "GDPR",
                              "Open Source", "Licenciamento de Software", "Tech Compliance"],
        "soft_skills": ["Visão de negócios", "Parceria com produto e engenharia", "Liderança"],
        "languages": [{"language": "Português", "level": "Nativo"}, {"language": "Inglês", "level": "Fluente"}],
        "certifications": ["OAB-SP 167.XXX", "Pós-PI USP", "IAPP CIPP/E"],
        "current_salary": 68000.0, "salary_currency": "BRL",
        "desired_salary_min": 72000.0, "desired_salary_max": 90000.0,
        "linkedin_url": "https://linkedin.com/in/luciafigueiredo-gc",
        "work_model_preference": "hybrid", "contract_type_preference": "CLT",
        "willing_to_relocate": False, "is_remote": False, "is_open_to_work": False,
        "stage": "sourcing", "status": "sourced", "lia_score": 87.5,
        "wsi_done": False, "has_interview": False, "profile_level": "excelente",
        "education": [
            {"institution": "Universidade de São Paulo (USP)",
             "degree": "Bacharelado em Direito", "field": "Direito",
             "city": "São Paulo", "state": "SP", "start": "1999-02", "end": "2003-12"},
            {"institution": "USP – Largo São Francisco",
             "degree": "Pós-graduação", "field": "Propriedade Intelectual",
             "city": "São Paulo", "state": "SP", "start": "2006-02", "end": "2007-12"},
        ],
        "experiences": [
            {"company": "Totvs S.A.", "title": "General Counsel",
             "start": "2020-06", "end": None, "is_current": True,
             "description": "CLO da maior tech company da América Latina. 16 advogados. Compliance global."},
            {"company": "CI&T", "title": "Diretora Jurídica",
             "start": "2016-01", "end": "2020-05", "is_current": False,
             "description": "Jurídico de empresa global de TI. 12 países. Contratos SaaS."},
            {"company": "Stefanini", "title": "Gerente Jurídico",
             "start": "2011-03", "end": "2015-12", "is_current": False,
             "description": "Contratos de outsourcing e serviços de TI."},
            {"company": "Pinheiro Neto Advogados", "title": "Advogada – Tecnologia",
             "start": "2004-01", "end": "2011-02", "is_current": False,
             "description": "M&A tech e propriedade intelectual."},
        ],
    },
    {
        "key": "paulo_saldanha",
        "name": "Paulo Henrique Saldanha Cruz",
        "email": "paulo.saldanha.cruz@gmail.com",
        "phone": "+55 11 89876-5432",
        "location_city": "São Paulo", "location_state": "SP",
        "current_title": "Diretor de Assuntos Jurídicos",
        "current_company": "Magazine Luiza",
        "seniority_level": "director", "years_of_experience": 16,
        "headline": "Direito do Consumidor | Varejo | Marketplace | ESG Jurídico",
        "self_introduction": (
            "16 anos em varejo com foco em direito do consumidor, marketplace e ESG. "
            "Liderança de 11 advogados no Magazine Luiza. "
            "Experiência em grande volume de litigância e inovação jurídica via LegalTech."
        ),
        "technical_skills": ["Direito do Consumidor", "Marketplace Digital", "ESG Jurídico",
                              "LGPD", "E-commerce", "Relações Consumeristas", "PROCON", "CDC"],
        "soft_skills": ["Inovação jurídica", "Gestão de alto volume", "Liderança", "Tech-friendly"],
        "languages": [{"language": "Português", "level": "Nativo"}, {"language": "Inglês", "level": "Intermediário"}],
        "certifications": ["OAB-SP 178.XXX", "MBA FGV-SP Direito Empresarial"],
        "current_salary": 42000.0, "salary_currency": "BRL",
        "desired_salary_min": 55000.0, "desired_salary_max": 72000.0,
        "linkedin_url": "https://linkedin.com/in/paulo-saldanha-cruz",
        "work_model_preference": "hybrid", "contract_type_preference": "CLT",
        "willing_to_relocate": False, "is_remote": False, "is_open_to_work": False,
        "stage": "sourcing", "status": "sourced", "lia_score": 73.0,
        "wsi_done": False, "has_interview": False, "profile_level": "alto",
        "education": [
            {"institution": "Universidade São Judas Tadeu", "degree": "Bacharelado em Direito",
             "field": "Direito", "city": "São Paulo", "state": "SP", "start": "2002-02", "end": "2006-12"},
            {"institution": "FGV-SP", "degree": "MBA",
             "field": "Direito Empresarial", "city": "São Paulo", "state": "SP", "start": "2010-02", "end": "2011-12"},
        ],
        "experiences": [
            {"company": "Magazine Luiza", "title": "Diretor de Assuntos Jurídicos",
             "start": "2017-08", "end": None, "is_current": True,
             "description": "11 advogados. 45.000 ações/ano. Programa LegalTech interno."},
            {"company": "Casas Bahia / Via Varejo", "title": "Gerente Jurídico Sênior",
             "start": "2013-02", "end": "2017-07", "is_current": False,
             "description": "Gestão de contencioso consumerista de alto volume."},
            {"company": "Riachuelo", "title": "Advogado Sênior",
             "start": "2009-03", "end": "2013-01", "is_current": False,
             "description": "Relações de consumo e gestão de fornecedores."},
        ],
    },
]

# ─── WSI: Competências jurídicas ───────────────────────────────────────────
WSI_COMPETENCIES = [
    "Estratégia Jurídica e Liderança",
    "Gestão de Riscos e Compliance",
    "M&A e Transações Complexas",
    "Gestão de Equipe Jurídica",
    "Relacionamento com Reguladores",
    "LGPD e Proteção de Dados",
]

WSI_QUESTIONS_BY_COMPETENCY = {
    "Estratégia Jurídica e Liderança": "Descreva como você estruturou ou reestruturou uma função jurídica em uma empresa. Quais foram os principais desafios e como você os superou?",
    "Gestão de Riscos e Compliance": "Conte sobre uma situação em que sua atuação jurídica foi fundamental para prevenir ou mitigar um risco significativo para a empresa. Qual era o risco e como você atuou?",
    "M&A e Transações Complexas": "Descreva sua experiência com fusões, aquisições ou transações societárias de grande porte. Qual foi seu papel e quais desafios jurídicos específicos você enfrentou?",
    "Gestão de Equipe Jurídica": "Como você gerencia e desenvolve uma equipe jurídica? Descreva um momento em que precisou liderar a equipe em uma situação de alta pressão ou crise.",
    "Relacionamento com Reguladores": "Conte sobre uma situação em que você teve que interagir diretamente com órgãos reguladores ou autoridades. Como foi sua abordagem e qual foi o resultado?",
    "LGPD e Proteção de Dados": "Qual sua experiência com implementação de programas de LGPD/GDPR e proteção de dados em uma organização? Descreva os principais desafios e como você os endereçou.",
}

# Respostas por nível de qualidade (adaptadas ao contexto jurídico)
WSI_RESPONSES = {
    "excelente": {
        "Estratégia Jurídica e Liderança": {
            "response": (
                "Na Votorantim Energia, após a fusão de 3 unidades, herdei um jurídico fragmentado: 14 advogados em silos "
                "sem visão de negócio, R$ 12M em contencioso passivo sem gestão ativa. Reestruturei em 4 pilares: "
                "(1) Centro de Competência por área (M&A, trabalhista, ambiental, regulatório); "
                "(2) Legal Business Partners para cada unidade de negócio; "
                "(3) Dashboard executivo de riscos em tempo real; "
                "(4) Outside counsel panel com KPIs. Em 18 meses: redução de 38% no passivo contingente, "
                "NPS interno passou de 3.1 para 4.6, e cortamos gastos externos em R$ 2,1M/ano."
            ),
            "auto_score": 4.8, "ctx_score": 4.9, "bloom": 5, "dreyfus": 5, "final": 4.85,
            "evidences": ["Reestruturação multidimensional com resultados mensuráveis", "Dashboard de riscos — inovação em gestão", "Redução de custos e passivos documentada"],
        },
        "Gestão de Riscos e Compliance": {
            "response": (
                "Em 2020, durante uma auditoria interna, identifiquei que contratos com 3 fornecedores estratégicos "
                "tinham cláusulas de confidencialidade inadequadas para novos requisitos da LGPD — risco de multa de até R$ 50M. "
                "Criei um war room jurídico em 72h, priorizei os 3 contratos por exposição, negociei aditivos emergenciais "
                "com todos em 21 dias. Documentei o processo como framework de risco contratual que virou política corporativa. "
                "Resultado: zero exposição regulatória, framework adotado em outras 2 subsidiárias."
            ),
            "auto_score": 4.7, "ctx_score": 4.8, "bloom": 5, "dreyfus": 5, "final": 4.75,
            "evidences": ["Identificação proativa de risco", "Resposta estruturada em prazo crítico", "Legado sistêmico: framework adotado em grupo"],
        },
        "M&A e Transações Complexas": {
            "response": (
                "Liderei o lado jurídico da aquisição da Energética Potiguar (R$ 780M) com closing em 6 meses. "
                "Due diligence revelou 14 contingências trabalhistas não divulgadas e 3 licenças ambientais vencidas — "
                "negociei redutor de preço de R$ 48M e um escrow de 5 anos para contingências. "
                "Coordenei equipe de 11 advogados internos + 2 escritórios externos. "
                "O deal estabeleceu o modelo de due diligence que a companhia usa até hoje."
            ),
            "auto_score": 4.6, "ctx_score": 4.7, "bloom": 5, "dreyfus": 5, "final": 4.65,
            "evidences": ["Liderança de equipe multidisciplinar em M&A complexo", "Proteção de R$ 48M no deal", "Legado: modelo de due diligence corporativo"],
        },
        "Gestão de Equipe Jurídica": {
            "response": (
                "Quando assumi a Votorantim Energia, 4 dos 14 advogados tinham pedido demissão em 2 meses — cultura de 'jurídico como carimbador'. "
                "Implementei weekly 1:1s, plano de carreira formal, e programa de mentoria interna. "
                "Em 12 meses: zero turnover, 2 promoções internas, e o time foi votado como melhor área de suporte no engajamento interno. "
                "Em crise: quando recebemos um PAD da CVM em prazo de 5 dias úteis, organizei war room com papéis definidos, "
                "entregas intermediárias a cada 12h e entregamos resposta técnica completa em prazo, sem defeitos."
            ),
            "auto_score": 4.5, "ctx_score": 4.6, "bloom": 5, "dreyfus": 4, "final": 4.55,
            "evidences": ["Reversão de turnover com dados", "Gestão de crise com metodologia"], },
        "Relacionamento com Reguladores": {
            "response": (
                "Em negociação de Term Sheet com a CVM para adequação de disclosure de companhia aberta, "
                "conduzimos 6 reuniões formais ao longo de 4 meses. Minha abordagem: total transparência técnica, "
                "apresentação proativa dos riscos identificados antes de perguntados, e proposta de cronograma de adequação "
                "com marcos mensuráveis. Resultado: CVM aceitou plano de adequação de 18 meses sem multa, "
                "reconhecendo boa-fé. O case virou referência citada em duas orientações da autarquia."
            ),
            "auto_score": 4.4, "ctx_score": 4.5, "bloom": 4, "dreyfus": 5, "final": 4.45,
            "evidences": ["Transparência como estratégia — resultado favorável sem multa", "Case citado em orientações CVM"],
        },
        "LGPD e Proteção de Dados": {
            "response": (
                "Lideré a implementação do programa LGPD da Votorantim Energia (18 meses, R$ 1,8M de investimento). "
                "Mapeei 240 processos de tratamento de dados, classifiquei por risco, eliminei 38% desnecessários. "
                "Implantei DPO interno, treinei 1.200 colaboradores, e criei Privacy by Design nos novos contratos. "
                "Resultado: auditoria independente classificou programa como 'mature' — top 15% do setor. "
                "ANPD nos contactou para apresentar o programa como case em workshop do setor energético."
            ),
            "auto_score": 4.6, "ctx_score": 4.7, "bloom": 5, "dreyfus": 5, "final": 4.65,
            "evidences": ["Mapeamento quantitativo (240 processos)", "Reconhecimento ANPD", "Impacto mensurável em redução de dados"],
        },
    },
    "alto": {
        "Estratégia Jurídica e Liderança": {
            "response": (
                "No Itaú, reestruturei a área de tributário que estava dividida entre contencioso e planejamento sem integração. "
                "Criei um comitê semanal conjunto e repositório unificado de teses tributárias. "
                "Em 18 meses, o aproveitamento de créditos tributários aumentou 22% e eliminamos redundâncias em 40 teses simultâneas."
            ),
            "auto_score": 4.0, "ctx_score": 4.1, "bloom": 4, "dreyfus": 4, "final": 4.05,
            "evidences": ["Integração de times", "Resultado financeiro mensurável"],
        },
        "Gestão de Riscos e Compliance": {
            "response": (
                "Identificamos risco de responsabilização no regime de PLD-FT em 3 contratos com distribuidores. "
                "Revisamos todos os contratos da carteira em 30 dias, priorizando por volume. "
                "Aditivos assinados em prazo, sem necessidade de comunicação ao Bacen."
            ),
            "auto_score": 3.9, "ctx_score": 4.0, "bloom": 4, "dreyfus": 4, "final": 3.95,
            "evidences": ["Gestão de risco regulatório em prazo", "Priorização por volume"],
        },
        "M&A e Transações Complexas": {
            "response": (
                "Participei da aquisição de uma seguradora regional (R$ 180M). Fiz parte da equipe de due diligence, "
                "foquei em passivos trabalhistas e regulatórios. Identifiquei contingência de R$ 12M e recomendei escrow. "
                "Transação concluída com sucesso no prazo."
            ),
            "auto_score": 3.8, "ctx_score": 3.9, "bloom": 4, "dreyfus": 3, "final": 3.85,
            "evidences": ["Participação em M&A real", "Identificação de contingência"],
        },
        "Gestão de Equipe Jurídica": {
            "response": (
                "Gestiono equipe de 28 advogados. Implementei revisão de desempenho semestral e plano de desenvolvimento "
                "individual. Em crise de autuação tributária, coordenei equipe de 6 pessoas em rotação de plantão jurídico "
                "por 15 dias. Resultado: defesa apresentada no prazo com todos os argumentos."
            ),
            "auto_score": 3.8, "ctx_score": 4.0, "bloom": 4, "dreyfus": 4, "final": 3.90,
            "evidences": ["Gestão formal de desempenho", "Coordenação em crise"],
        },
        "Relacionamento com Reguladores": {
            "response": (
                "Conduzimos reunião técnica com Bacen sobre nova circular de capital regulatório. "
                "Preparei a argumentação técnica e me reuní com 3 técnicos. "
                "Conseguimos prazo adicional de 6 meses para adequação. Experiência positiva com autoridade reguladora."
            ),
            "auto_score": 3.7, "ctx_score": 3.8, "bloom": 3, "dreyfus": 4, "final": 3.75,
            "evidences": ["Interação direta com regulador", "Resultado concreto (prazo)"],
        },
        "LGPD e Proteção de Dados": {
            "response": (
                "Lideré adaptação dos contratos bancários para LGPD: 1.200 minutas revisadas, "
                "linguagem de consentimento padronizada. Treinamento de 800 funcionários. "
                "Implementamos DPO externo e Privacy Policy renovada. Dentro do prazo legal."
            ),
            "auto_score": 4.0, "ctx_score": 4.1, "bloom": 4, "dreyfus": 4, "final": 4.05,
            "evidences": ["Escala significativa", "Múltiplos produtos LGPD implementados"],
        },
    },
    "medio": {
        "Estratégia Jurídica e Liderança": {
            "response": (
                "Propus a revisão do processo de aprovação de contratos para reduzir o SLA de 10 para 5 dias. "
                "Criamos um checklist digital e roteamento automático por tipo e valor. Conseguimos reduzir para 6 dias."
            ),
            "auto_score": 3.0, "ctx_score": 2.9, "bloom": 3, "dreyfus": 2, "final": 2.95,
            "evidences": ["Iniciativa de melhoria de processo", "Resultado parcial"],
        },
        "Gestão de Riscos e Compliance": {
            "response": (
                "Quando identificamos risco de autuação por descumprimento de norma da ANATEL, "
                "preparamos defesa administrativa com suporte de advogados especializados externos. "
                "A multa foi reduzida em 30%."
            ),
            "auto_score": 2.8, "ctx_score": 2.9, "bloom": 3, "dreyfus": 2, "final": 2.85,
            "evidences": ["Resposta a risco existente (não preventiva)", "Resultado positivo"],
        },
        "M&A e Transações Complexas": {
            "response": (
                "Não tive envolvimento direto em M&A. Em contratos de grande porte (acima de R$ 50M), "
                "acompanhei o processo de negociação e revisão de cláusulas."
            ),
            "auto_score": 2.0, "ctx_score": 1.8, "bloom": 2, "dreyfus": 1, "final": 1.90,
            "evidences": ["Ausência de experiência em M&A"],
        },
        "Gestão de Equipe Jurídica": {
            "response": (
                "Coordeno 4 analistas e 1 estagiário. Faço revisão semanal de tarefas e distribuo processos conforme carga. "
                "Ainda estou desenvolvendo habilidades de liderança formal."
            ),
            "auto_score": 3.1, "ctx_score": 3.0, "bloom": 3, "dreyfus": 2, "final": 3.05,
            "evidences": ["Gestão de pequena equipe", "Autoconhecimento de lacunas"],
        },
        "Relacionamento com Reguladores": {
            "response": (
                "Acompanhei reuniões com ANATEL e preparei materiais de suporte. "
                "Não conduzi reunião como responsável principal ainda."
            ),
            "auto_score": 2.5, "ctx_score": 2.4, "bloom": 2, "dreyfus": 2, "final": 2.45,
            "evidences": ["Participação secundária"],
        },
        "LGPD e Proteção de Dados": {
            "response": (
                "Participei da implementação de LGPD como membro da equipe. "
                "Revisei contratos de fornecedores e adaptei cláusulas de dados. "
                "O programa foi liderado por um consultor externo."
            ),
            "auto_score": 3.0, "ctx_score": 2.8, "bloom": 3, "dreyfus": 2, "final": 2.90,
            "evidences": ["Participação em implementação LGPD"],
        },
    },
    "regular": {
        "Estratégia Jurídica e Liderança": {
            "response": (
                "Ainda não tive oportunidade de liderar uma reestruturação de área jurídica. "
                "Minha experiência é como executante das estratégias definidas pelos sócios ou diretores."
            ),
            "auto_score": 1.8, "ctx_score": 1.5, "bloom": 1, "dreyfus": 1, "final": 1.65,
            "evidences": ["Sem experiência em liderança estratégica"],
        },
        "Gestão de Riscos e Compliance": {
            "response": (
                "Quando aparece um risco, encaminho para o sócio responsável com um memorando de análise. "
                "Ainda não tomei decisão de exposição sozinho."
            ),
            "auto_score": 2.0, "ctx_score": 1.8, "bloom": 2, "dreyfus": 1, "final": 1.90,
            "evidences": ["Papel de suporte, sem decisão autônoma"],
        },
        "M&A e Transações Complexas": {
            "response": (
                "Participei de due diligences preparando listas de documentos e organizando data rooms. "
                "A análise jurídica e negociação era feita pelos sócios."
            ),
            "auto_score": 2.2, "ctx_score": 2.0, "bloom": 2, "dreyfus": 1, "final": 2.10,
            "evidences": ["Suporte operacional em M&A"],
        },
        "Gestão de Equipe Jurídica": {
            "response": (
                "Ainda não tive oportunidade de liderar uma equipe. "
                "Trabalho com colegas em projetos específicos."
            ),
            "auto_score": 1.5, "ctx_score": 1.3, "bloom": 1, "dreyfus": 1, "final": 1.40,
            "evidences": ["Sem experiência de liderança"],
        },
        "Relacionamento com Reguladores": {
            "response": (
                "Não tive contato direto com reguladores. "
                "Preparo documentos que são enviados pelos sócios."
            ),
            "auto_score": 1.8, "ctx_score": 1.6, "bloom": 1, "dreyfus": 1, "final": 1.70,
            "evidences": ["Sem experiência com reguladores"],
        },
        "LGPD e Proteção de Dados": {
            "response": (
                "Fiz um curso online de LGPD e conheço os conceitos básicos. "
                "Na prática, incluo as cláusulas padrão de proteção de dados nos contratos que reviso."
            ),
            "auto_score": 2.2, "ctx_score": 2.0, "bloom": 2, "dreyfus": 1, "final": 2.10,
            "evidences": ["Conhecimento teórico básico", "Aplicação mecânica de cláusulas"],
        },
    },
}

# ─── Helpers para scores WSI ────────────────────────────────────────────────
WSI_SCORES = {
    "excelente": {"overall": 4.65, "technical": 4.70, "behavioral": 4.55,
                  "classification": "excelente", "percentile": 93, "decision": "aprovado"},
    "alto": {"overall": 3.92, "technical": 3.88, "behavioral": 4.00,
             "classification": "alto", "percentile": 78, "decision": "aprovado"},
    "medio": {"overall": 2.85, "technical": 2.65, "behavioral": 3.10,
              "classification": "medio", "percentile": 48, "decision": "aguardando"},
    "regular": {"overall": 1.82, "technical": 1.75, "behavioral": 1.92,
                "classification": "regular", "percentile": 22, "decision": "reprovado"},
}

# ─── Funções auxiliares ─────────────────────────────────────────────────────

def _wsi_report(level: str, name: str) -> dict:
    if level == "excelente":
        return {
            "executive_summary": (
                f"{name} é uma das candidatas mais completas avaliadas para este processo. "
                "Demonstra visão estratégica excepcional, liderança comprovada e profunda experiência técnica em Direito Corporativo e M&A. "
                "Altamente recomendada para o cargo de Diretor(a) Jurídico(a)."
            ),
            "technical_analysis": {
                "pontos_fortes": ["Estratégia jurídica com impacto mensurável", "Liderança em M&A de grande porte",
                                  "Expertise em compliance e LGPD", "Gestão de equipes jurídicas complexas"],
                "gaps": ["Pode aprofundar experiência em startups/scale-ups"],
                "evidencias": ["Reestruturação jurídica com redução de passivo 38%", "M&A liderado de R$ 780M", "Programa LGPD reconhecido pela ANPD"]
            },
            "behavioral_analysis": {
                "colaboracao": {"score": 4.4, "descricao": "Excelente parceria com board e C-level"},
                "inovacao": {"score": 4.6, "descricao": "Pioneira em Legal Ops e jurídico data-driven"},
                "organizacao": {"score": 4.7, "descricao": "Processos estruturados e métricas claras"},
                "resiliencia": {"score": 4.5, "descricao": "Histórico comprovado em crises regulatórias"}
            },
            "cultural_fit": {"score": 4.5, "valores_alinhados": ["Excelência", "Inovação", "Liderança", "Ética"], "atencoes": []},
            "recommendation": {
                "decisao": "Fortemente Recomendado",
                "justificativa": "Perfil excepcional com histórico de criação de valor tangível.",
                "proximos_passos": ["Entrevista com CEO/Conselho", "Apresentar proposta competitiva", "Referências profissionais"]
            }
        }
    elif level == "alto":
        return {
            "executive_summary": (
                f"{name} é um(a) candidato(a) sólido(a) com experiência relevante e boa técnica jurídica. "
                "Demonstra capacidade de liderança e resultados consistentes. Recomendado(a) para avançar no processo."
            ),
            "technical_analysis": {
                "pontos_fortes": ["Experiência sólida em área de especialização", "Liderança funcional comprovada", "Resultados mensuráveis"],
                "gaps": ["Escopo de atuação ainda restrito a uma especialização", "Sem experiência como CLO de empresa listada"],
                "evidencias": ["Gestão de equipes de 6-28 advogados", "Resultados concretos em redução de passivos/riscos"]
            },
            "behavioral_analysis": {
                "colaboracao": {"score": 3.8, "descricao": "Trabalha bem com stakeholders internos"},
                "inovacao": {"score": 3.7, "descricao": "Iniciativas de melhoria focadas na especialização"},
                "organizacao": {"score": 4.0, "descricao": "Processos bem estruturados na sua área"},
                "resiliencia": {"score": 3.9, "descricao": "Boa performance sob pressão"}
            },
            "cultural_fit": {"score": 3.8, "valores_alinhados": ["Excelência técnica", "Resultados", "Ética"], "atencoes": ["Verificar fit com complexidade estratégica do cargo"]},
            "recommendation": {
                "decisao": "Recomendado",
                "justificativa": "Perfil sólido com potencial para o cargo. Avançar para entrevistas.",
                "proximos_passos": ["Entrevista técnica aprofundada", "Avaliar fit cultural com a liderança"]
            }
        }
    else:
        return {
            "executive_summary": (
                f"{name} possui experiência funcional relevante mas apresenta lacunas para o escopo executivo da posição. "
                "Perfil mais adequado a posições de gerência sênior do que à diretoria."
            ),
            "technical_analysis": {
                "pontos_fortes": ["Conhecimento técnico na especialização", "Proatividade"],
                "gaps": ["Escopo executivo limitado", "Sem experiência como CLO", "Pouca experiência em M&A"],
                "evidencias": []
            },
            "behavioral_analysis": {
                "colaboracao": {"score": 3.0, "descricao": "Trabalho colaborativo em equipes menores"},
                "inovacao": {"score": 2.8, "descricao": "Melhorias incrementais, sem ruptura"},
                "organizacao": {"score": 3.2, "descricao": "Organização adequada para o nível atual"},
                "resiliencia": {"score": 3.0, "descricao": "Competência para lidar com pressões operacionais"}
            },
            "cultural_fit": {"score": 3.0, "valores_alinhados": ["Ética", "Comprometimento"], "atencoes": ["Lacuna em liderança executiva"]},
            "recommendation": {
                "decisao": "Em Avaliação",
                "justificativa": "Perfil requer mais análise para o escopo da vaga.",
                "proximos_passos": ["Aguardar conclusão da triagem antes de avanço"]
            }
        }


def _triagem_msgs(level: str, name: str, vacancy_title: str) -> list:
    """Chat de triagem adaptado para Diretor Jurídico."""
    msgs_by_level = {
        "excelente": [
            ("lia", f"Olá, {name}! Sou a LIA, assistente de recrutamento da WeDo Talent. Obrigada por participar da triagem para a vaga de {vacancy_title}. Vamos conversar sobre sua trajetória jurídica?"),
            ("candidate", "Olá! Com muito prazer. Estou animada com essa oportunidade."),
            ("lia", "Excelente! Para começar: você pode me descrever sua experiência liderando departamentos jurídicos e qual foi o maior desafio que você superou nessa função?"),
            ("candidate", "Claro. Na Votorantim Energia, após a fusão de 3 unidades, precisei reestruturar um jurídico fragmentado com 14 advogados em silos. O maior desafio foi mudar a cultura de 'jurídico como carimbador' para parceiro de negócios. Implementei o modelo de Legal Business Partner e em 18 meses o NPS interno subiu de 3.1 para 4.6."),
            ("lia", "Impressionante! E em relação a M&A e transações complexas, qual foi a transação mais desafiadora que você liderou?"),
            ("candidate", "Sem dúvida a aquisição da Energética Potiguar por R$ 780M. A due diligence revelou 14 contingências trabalhistas não divulgadas e 3 licenças ambientais vencidas. Negociei um redutor de preço de R$ 48M e um escrow de 5 anos. O mais desafiador foi manter o timing do deal sem prejudicar a proteção jurídica da compradora."),
            ("lia", "E como você lida com programas de compliance e LGPD em larga escala?"),
            ("candidate", "Lideré a implementação do programa LGPD da Votorantim Energia em 18 meses, com investimento de R$ 1,8M. Mapeei 240 processos, eliminei 38% desnecessários, implementei DPO interno e treinei 1.200 colaboradores. O resultado foi reconhecido pela ANPD como case do setor energético."),
            ("lia", f"Muito obrigada, {name}! Suas respostas foram extraordinárias. A equipe de recrutamento entrará em contato com os próximos passos. Alguma pergunta sobre a posição?"),
            ("candidate", "Gostaria de entender melhor a estrutura da equipe jurídica atual e o escopo de atuação com o board. Mas posso deixar para a próxima etapa. Muito obrigada pela oportunidade!"),
        ],
        "alto": [
            ("lia", f"Olá, {name}! Sou a LIA. Obrigada por participar da triagem para {vacancy_title}. Vamos conversar?"),
            ("candidate", "Olá! Claro, com prazer."),
            ("lia", "Pode me falar sobre sua experiência liderando equipes jurídicas e seus principais resultados?"),
            ("candidate", "Atualmente gerencio 28 advogados no Itaú, com responsabilidade sobre um passivo tributário de R$ 4,2 bilhões. Reestruturei a área criando integração entre contencioso e planejamento tributário, o que aumentou em 22% o aproveitamento de créditos."),
            ("lia", "E em compliance e regulatório, qual sua experiência com órgãos reguladores?"),
            ("candidate", "Tenho interface regular com Bacen e CMN. Em uma negociação recente sobre nova circular de capital regulatório, conduzi 3 reuniões técnicas e conseguimos prazo adicional de 6 meses para adequação — sem multa ou autuação."),
            ("lia", "Como você abordaria a implementação de LGPD em uma empresa que ainda não tem programa estruturado?"),
            ("candidate", "No Bradesco, lideré a adaptação de 1.200 minutas de contratos bancários para LGPD, padronizei linguagem de consentimento e implementamos DPO externo. Treinei 800 funcionários. O processo levou 14 meses para cobertura completa."),
            ("lia", f"Ótimas respostas, {name}! A equipe entrará em contato. Alguma dúvida?"),
            ("candidate", "Não, obrigado. Aguardo o retorno."),
        ],
        "medio": [
            ("lia", f"Olá, {name}! Sou a LIA. Obrigada por participar da triagem para {vacancy_title}."),
            ("candidate", "Olá! Pode começar."),
            ("lia", "Fale sobre sua experiência com gestão de equipes jurídicas."),
            ("candidate", "Atualmente coordeno 4 analistas e um estagiário na revisão e aprovação de contratos. Organizo as atividades semanalmente conforme demanda."),
            ("lia", "E em M&A ou transações complexas, qual sua experiência?"),
            ("candidate", "Não tive envolvimento direto em M&A. Em contratos de grande porte, acompanho a negociação e reviso cláusulas específicas da minha área."),
            ("lia", "Como você lida com LGPD na sua função atual?"),
            ("candidate", "Participei da implementação como membro da equipe, revisando contratos de fornecedores. O programa foi coordenado por um consultor externo."),
            ("lia", f"Obrigada, {name}! A equipe analisará seu perfil. Alguma dúvida?"),
            ("candidate", "Não, obrigado."),
        ],
        "regular": [
            ("lia", f"Olá, {name}! Sou a LIA. Vamos conversar sobre a vaga de {vacancy_title}?"),
            ("candidate", "Oi, pode falar."),
            ("lia", "Fale sobre sua trajetória e o que te motivou a se candidatar a uma posição de direção jurídica."),
            ("candidate", "Estou há 7 anos em escritório e quero minha primeira experiência in-house. Gostaria de crescer para uma posição de liderança."),
            ("lia", "Qual é sua experiência com M&A e transações corporativas?"),
            ("candidate", "Participei de due diligences preparando data rooms e listas de documentos. A análise principal era feita pelos sócios."),
            ("lia", "E com relação a compliance e LGPD?"),
            ("candidate", "Fiz um curso online de LGPD. Na prática, incluo as cláusulas padrão nos contratos que reviso."),
            ("lia", f"Obrigada, {name}! A equipe analisará seu perfil."),
            ("candidate", "Obrigado."),
        ],
    }
    result = []
    msgs = msgs_by_level.get(level, msgs_by_level["medio"])
    for i, (sender, content) in enumerate(msgs):
        result.append({
            "id": _sid(f"tmsg_{name}_{i}"),
            "sender": sender,
            "content": content.replace("{name}", name).replace("{vacancy}", vacancy_title),
            "message_type": "text",
            "wsi_block": (i // 2) + 1,
            "wsi_question_id": None,
            "score": None,
            "created_at": _dt(14 - i * 0.01),
        })
    return result


# ─── Seed Principal ──────────────────────────────────────────────────────────
async def seed(db):
    logger.info(f"Seeding {len(CANDIDATES)} candidatos para vaga {VACANCY_ID}...")

    for c in CANDIDATES:
        cid = _sid(c["key"])
        vcid = _sid(f"vc_{c['key']}")
        logger.info(f"  → {c['name']} ({c['stage']})")

        # ── 1. Candidate ──────────────────────────────────────────────────
        await db.execute(text("""
            INSERT INTO candidates (
                id, company_id, name, email, phone,
                location_city, location_state, location_country,
                current_title, current_company, seniority_level, years_of_experience,
                headline, self_introduction,
                technical_skills, soft_skills, languages, certifications,
                current_salary, salary_currency, desired_salary_min, desired_salary_max,
                linkedin_url, work_model_preference, contract_type_preference,
                willing_to_relocate, is_remote, is_open_to_work,
                source, status, is_active,
                created_at, updated_at
            ) VALUES (
                :id, :company_id, :name, :email, :phone,
                :location_city, :location_state, 'Brasil',
                :current_title, :current_company, :seniority_level, :years_of_experience,
                :headline, :self_introduction,
                :technical_skills, :soft_skills, CAST(:languages AS json), :certifications,
                :current_salary, :salary_currency, :desired_salary_min, :desired_salary_max,
                :linkedin_url, :work_model_preference, :contract_type_preference,
                :willing_to_relocate, :is_remote, :is_open_to_work,
                :source, 'active', true,
                :created_at, :updated_at
            )
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                email = EXCLUDED.email,
                updated_at = EXCLUDED.updated_at
        """), {
            "id": cid,
            "company_id": COMPANY_ID,
            "name": c["name"],
            "email": c["email"],
            "phone": c["phone"],
            "location_city": c["location_city"],
            "location_state": c["location_state"],
            "current_title": c["current_title"],
            "current_company": c["current_company"],
            "seniority_level": c["seniority_level"],
            "years_of_experience": c["years_of_experience"],
            "headline": c["headline"],
            "self_introduction": c["self_introduction"],
            "technical_skills": c["technical_skills"],
            "soft_skills": c["soft_skills"],
            "languages": json.dumps(c["languages"]),
            "certifications": c.get("certifications", []),
            "current_salary": c.get("current_salary"),
            "salary_currency": c.get("salary_currency", "BRL"),
            "desired_salary_min": c.get("desired_salary_min"),
            "desired_salary_max": c.get("desired_salary_max"),
            "linkedin_url": c.get("linkedin_url"),
            "work_model_preference": c.get("work_model_preference"),
            "contract_type_preference": c.get("contract_type_preference"),
            "willing_to_relocate": c.get("willing_to_relocate", False),
            "is_remote": c.get("is_remote", False),
            "is_open_to_work": c.get("is_open_to_work", True),
            "source": SEED_TAG,
            "created_at": _dt(30),
            "updated_at": _dt(1),
        })

        # ── 2. Experiences ────────────────────────────────────────────────
        for i, exp in enumerate(c.get("experiences", [])):
            exp_id = _sid(f"exp_{c['key']}_{i}")
            await db.execute(text("""
                INSERT INTO candidate_experiences (
                    id, candidate_id, company_name, title,
                    start_date, end_date, is_current,
                    location, industries, sequence_order, created_at, updated_at
                ) VALUES (
                    :id, :candidate_id, :company_name, :title,
                    :start_date, :end_date, :is_current,
                    :location, :industries, :seq, :created_at, :updated_at
                ) ON CONFLICT (id) DO NOTHING
            """), {
                "id": exp_id,
                "candidate_id": cid,
                "company_name": exp["company"],
                "title": exp["title"],
                "start_date": exp["start"],
                "end_date": exp.get("end"),
                "is_current": exp.get("is_current", False),
                "location": f"{c['location_city']}, {c['location_state']}",
                "industries": ["Jurídico"],
                "seq": i,
                "created_at": _dt(30),
                "updated_at": _dt(1),
            })

        # ── 3. Education ──────────────────────────────────────────────────
        for i, edu in enumerate(c.get("education", [])):
            edu_id = _sid(f"edu_{c['key']}_{i}")
            await db.execute(text("""
                INSERT INTO candidate_education (
                    id, candidate_id, institution, degree, field_of_study,
                    start_date, end_date, is_completed,
                    institution_city, institution_state, institution_country,
                    sequence_order, created_at, updated_at
                ) VALUES (
                    :id, :candidate_id, :institution, :degree, :field,
                    :start, :end, true,
                    :city, :state, 'Brasil',
                    :seq, :created_at, :updated_at
                ) ON CONFLICT (id) DO NOTHING
            """), {
                "id": edu_id,
                "candidate_id": cid,
                "institution": edu["institution"],
                "degree": edu["degree"],
                "field": edu["field"],
                "start": edu["start"],
                "end": edu.get("end"),
                "city": edu.get("city", c["location_city"]),
                "state": edu.get("state", c["location_state"]),
                "seq": i,
                "created_at": _dt(30),
                "updated_at": _dt(1),
            })

        # ── 4. Vacancy Candidate ──────────────────────────────────────────
        days_in_stage = {"offer": 3, "interview_manager": 8, "interview_hr": 12,
                         "short_list": 18, "long_list": 24, "screening": 10, "sourcing": 5}
        stage_entered = _dt(days_in_stage.get(c["stage"], 7))

        await db.execute(text("""
            INSERT INTO vacancy_candidates (
                id, vacancy_id, candidate_id, company_id,
                status, stage, lia_score, match_percentage,
                source, origin, stage_entered_at,
                created_at, updated_at
            ) VALUES (
                :id, :vacancy_id, :candidate_id, :company_id,
                :status, :stage, :lia_score, :match_pct,
                :source, 'seed', :stage_entered_at,
                :created_at, :updated_at
            )
            ON CONFLICT (id) DO UPDATE SET
                status = EXCLUDED.status,
                stage = EXCLUDED.stage,
                lia_score = EXCLUDED.lia_score,
                updated_at = EXCLUDED.updated_at
        """), {
            "id": vcid,
            "vacancy_id": VACANCY_ID,
            "candidate_id": cid,
            "company_id": COMPANY_ID,
            "status": c["status"],
            "stage": c["stage"],
            "lia_score": c["lia_score"],
            "match_pct": c["lia_score"],
            "source": SEED_TAG,
            "stage_entered_at": stage_entered,
            "created_at": _dt(30),
            "updated_at": _dt(1),
        })

        # ── 5. Stage History ──────────────────────────────────────────────
        history_id = _sid(f"hist_{c['key']}_initial")
        to_stage_id = STAGE_IDS.get(c["stage"], STAGE_IDS["sourcing"])
        await db.execute(text("""
            INSERT INTO candidate_stage_history (
                id, vacancy_candidate_id, vacancy_id, candidate_id, company_id,
                from_stage_id, from_stage_name,
                to_stage_id, to_stage_name,
                transition_type, triggered_by,
                created_at
            ) VALUES (
                :id, :vcid, :vacancy_id, :candidate_id, :company_id,
                NULL, NULL,
                :to_stage_id, :stage,
                'auto', 'seed',
                :created_at
            ) ON CONFLICT (id) DO NOTHING
        """), {
            "id": history_id,
            "vcid": vcid,
            "vacancy_id": VACANCY_ID,
            "candidate_id": cid,
            "company_id": COMPANY_ID,
            "to_stage_id": to_stage_id,
            "stage": c["stage"],
            "created_at": stage_entered,
        })

        # ── 6. Activity Feed ──────────────────────────────────────────────
        act_id = _sid(f"act_added_{c['key']}")
        await db.execute(text("""
            INSERT INTO activity_feed (
                id, activity_type, actor_id, actor_name, actor_type,
                target_id, target_name, target_type,
                title, description,
                priority, category, is_visible, visible_to,
                company_id, created_at
            ) VALUES (
                :id, 'candidate_added', 'system', 'LIA Recruiter', 'system',
                :candidate_id, :name, 'candidate',
                :title, :desc,
                'normal', 'recruiting', true, '[]'::json,
                :company_id, :created_at
            ) ON CONFLICT (id) DO NOTHING
        """), {
            "id": act_id,
            "candidate_id": cid,
            "name": c["name"],
            "title": f"Candidato adicionado: {c['name']}",
            "desc": f"{c['name']} foi adicionado(a) à vaga de {VACANCY_TITLE} — estágio: {c['stage']}",
            "company_id": COMPANY_ID,
            "created_at": _dt(30),
        })

        # ── 7. WSI (apenas para candidatos que passaram da triagem) ──────
        if c["wsi_done"]:
            level = c["profile_level"]
            wsi_session_id = _sid(f"wsi_sess_{c['key']}")
            wsi_result_id = _sid(f"wsi_result_{c['key']}")
            scores = WSI_SCORES[level]

            # WSI Session
            await db.execute(text("""
                INSERT INTO wsi_sessions (
                    id, candidate_id, job_vacancy_id,
                    screening_type, mode, status,
                    question_set_version, started_at, completed_at,
                    created_at, updated_at, score
                ) VALUES (
                    :id, :candidate_id, :job_vacancy_id,
                    'chat', 'compact_plus', 'completed',
                    1, :started_at, :completed_at,
                    :created_at, :updated_at, :score
                ) ON CONFLICT (id) DO NOTHING
            """), {
                "id": wsi_session_id,
                "candidate_id": cid,
                "job_vacancy_id": VACANCY_ID,
                "started_at": _dt(16),
                "completed_at": _dt(15),
                "created_at": _dt(15),
                "updated_at": _dt(15),
                "score": scores["overall"] * 2,  # normalized 0-10
            })

            # WSI Questions + Response Analyses
            for j, comp in enumerate(WSI_COMPETENCIES):
                q_id = _sid(f"wsi_q_{c['key']}_{j}")
                resp_id = _sid(f"wsi_resp_{c['key']}_{j}")
                resp_data = WSI_RESPONSES.get(level, WSI_RESPONSES["medio"]).get(comp, {})
                q_text = WSI_QUESTIONS_BY_COMPETENCY[comp]

                await db.execute(text("""
                    INSERT INTO wsi_questions (
                        id, session_id, competency, framework,
                        question_type, question_text, weight,
                        expected_signals, scoring_criteria, sequence_order, created_at
                    ) VALUES (
                        :id, :session_id, :competency, 'CBI',
                        'contextual', :question_text, 1.0,
                        :expected_signals, :scoring_criteria, :seq, :created_at
                    ) ON CONFLICT (id) DO NOTHING
                """), {
                    "id": q_id,
                    "session_id": wsi_session_id,
                    "competency": comp,
                    "question_text": q_text,
                    "expected_signals": json.dumps(resp_data.get("evidences", [])),
                    "scoring_criteria": json.dumps({"bloom_target": 4, "dreyfus_target": 4}),
                    "seq": j,
                    "created_at": _dt(15),
                })

                response_text = resp_data.get("response", "Sem resposta registrada.")
                response_hash = hashlib.md5(response_text.encode()).hexdigest()
                await db.execute(text("""
                    INSERT INTO wsi_response_analyses (
                        id, session_id, question_id,
                        candidate_id, job_vacancy_id, competency,
                        response_text, response_hash,
                        autodeclaration_score, context_score,
                        bloom_level, dreyfus_level,
                        evidences, red_flags,
                        consistency_penalty, final_score, justification,
                        created_at
                    ) VALUES (
                        :id, :session_id, :question_id,
                        :candidate_id, :job_vacancy_id, :competency,
                        :response_text, :response_hash,
                        :auto_score, :ctx_score,
                        :bloom, :dreyfus,
                        :evidences, '[]'::jsonb,
                        0.0, :final_score, :justification,
                        :created_at
                    ) ON CONFLICT (id) DO NOTHING
                """), {
                    "id": resp_id,
                    "session_id": wsi_session_id,
                    "question_id": q_id,
                    "candidate_id": cid,
                    "job_vacancy_id": VACANCY_ID,
                    "competency": comp,
                    "response_text": response_text,
                    "response_hash": response_hash,
                    "auto_score": resp_data.get("auto_score", 3.0),
                    "ctx_score": resp_data.get("ctx_score", 3.0),
                    "bloom": resp_data.get("bloom", 3),
                    "dreyfus": resp_data.get("dreyfus", 3),
                    "evidences": json.dumps(resp_data.get("evidences", [])),
                    "final_score": resp_data.get("final", 3.0),
                    "justification": resp_data.get("justification", ""),
                    "created_at": _dt(15),
                })

            # WSI Result
            await db.execute(text("""
                INSERT INTO wsi_results (
                    id, session_id, candidate_id, job_vacancy_id,
                    technical_wsi, behavioral_wsi, overall_wsi,
                    classification, percentile, created_at
                ) VALUES (
                    :id, :session_id, :candidate_id, :job_vacancy_id,
                    :technical, :behavioral, :overall,
                    :classification, :percentile, :created_at
                ) ON CONFLICT (id) DO NOTHING
            """), {
                "id": wsi_result_id,
                "session_id": wsi_session_id,
                "candidate_id": cid,
                "job_vacancy_id": VACANCY_ID,
                "technical": scores["technical"],
                "behavioral": scores["behavioral"],
                "overall": scores["overall"],
                "classification": scores["classification"],
                "percentile": scores["percentile"],
                "created_at": _dt(15),
            })

            # WSI Report
            report_data = _wsi_report(level, c["name"])
            report_id = _sid(f"wsi_report_{c['key']}")
            await db.execute(text("""
                INSERT INTO wsi_reports (
                    id, wsi_result_id, candidate_id,
                    executive_summary, technical_analysis,
                    behavioral_analysis, cultural_fit, recommendation,
                    created_at
                ) VALUES (
                    :id, :result_id, :candidate_id,
                    :executive_summary, CAST(:technical_analysis AS jsonb),
                    CAST(:behavioral_analysis AS jsonb), CAST(:cultural_fit AS jsonb), CAST(:recommendation AS jsonb),
                    :created_at
                ) ON CONFLICT (id) DO NOTHING
            """), {
                "id": report_id,
                "result_id": wsi_result_id,
                "candidate_id": cid,
                "executive_summary": report_data["executive_summary"],
                "technical_analysis": json.dumps(report_data["technical_analysis"]),
                "behavioral_analysis": json.dumps(report_data["behavioral_analysis"]),
                "cultural_fit": json.dumps(report_data["cultural_fit"]),
                "recommendation": json.dumps(report_data["recommendation"]),
                "created_at": _dt(14),
            })

            # WSI Feedback
            feedback_id = _sid(f"wsi_feedback_{c['key']}")
            decision = scores["decision"]
            await db.execute(text("""
                INSERT INTO wsi_feedbacks (
                    id, wsi_result_id, candidate_id, decision,
                    main_message, technical_strengths, development_opportunities,
                    behavioral_strengths, next_steps, personalized_tip,
                    created_at
                ) VALUES (
                    :id, :result_id, :candidate_id, :decision,
                    :main_message, CAST(:tech_strengths AS jsonb), CAST(:dev_opps AS jsonb),
                    CAST(:behav_strengths AS jsonb), :next_steps, :tip,
                    :created_at
                ) ON CONFLICT (id) DO NOTHING
            """), {
                "id": feedback_id,
                "result_id": wsi_result_id,
                "candidate_id": cid,
                "decision": decision,
                "main_message": report_data["recommendation"]["justificativa"],
                "tech_strengths": json.dumps(report_data["technical_analysis"].get("pontos_fortes", [])),
                "dev_opps": json.dumps(report_data["technical_analysis"].get("gaps", [])),
                "behav_strengths": json.dumps([v["descricao"] for v in report_data["behavioral_analysis"].values()]),
                "next_steps": ", ".join(report_data["recommendation"].get("proximos_passos", [])),
                "tip": "Continue destacando casos com impacto mensurável em entrevistas.",
                "created_at": _dt(14),
            })

            # Triagem Session + Messages
            ts_id = _sid(f"triagem_sess_{c['key']}")
            await db.execute(text("""
                INSERT INTO triagem_sessions (
                    id, token, candidate_id, candidate_name, candidate_email,
                    job_id, job_title, company_id, company_name,
                    status, current_block, total_blocks,
                    wsi_final_score, recommendation,
                    invite_channel, voice_mode,
                    started_at, completed_at, expires_at, created_at, updated_at
                ) VALUES (
                    :id, :token, :candidate_id, :name, :email,
                    :job_id, :job_title, :company_id, 'Demo Company',
                    'completed', 6, 6,
                    :wsi_score, :recommendation,
                    'email', false,
                    :started_at, :completed_at, :expires_at, :created_at, :updated_at
                ) ON CONFLICT (id) DO NOTHING
            """), {
                "id": ts_id,
                "token": _sid(f"token_{c['key']}"),
                "candidate_id": cid,
                "name": c["name"],
                "email": c["email"],
                "job_id": VACANCY_ID,
                "job_title": VACANCY_TITLE,
                "company_id": COMPANY_ID,
                "wsi_score": scores["overall"] * 2,
                "recommendation": scores["decision"],
                "started_at": _dt(16),
                "completed_at": _dt(15),
                "expires_at": _dt(-14),  # expires 14 days from now (already completed)
                "created_at": _dt(17),
                "updated_at": _dt(15),
            })

            # Triagem Messages
            msgs = _triagem_msgs(level, c["name"], VACANCY_TITLE)
            for msg in msgs:
                await db.execute(text("""
                    INSERT INTO triagem_messages (
                        id, session_id, sender, content, message_type,
                        wsi_block, wsi_question_id, score, created_at
                    ) VALUES (
                        :id, :session_id, :sender, :content, 'text',
                        :wsi_block, :wsi_question_id, :score, :created_at
                    ) ON CONFLICT (id) DO NOTHING
                """), {
                    "id": msg["id"],
                    "session_id": ts_id,
                    "sender": msg["sender"],
                    "content": msg["content"],
                    "wsi_block": msg["wsi_block"],
                    "wsi_question_id": msg.get("wsi_question_id"),
                    "score": msg.get("score"),
                    "created_at": msg["created_at"],
                })

        # ── 8. Interviews (para candidatos em interview_hr / manager / offer) ──
        if c["has_interview"]:
            interview_types = {"interview_hr": "hr", "interview_manager": "technical", "offer": "final"}
            itype = interview_types.get(c["stage"], "hr")
            int_id = _sid(f"interview_{c['key']}_1")
            int_title = {"hr": "Entrevista RH", "technical": "Entrevista com Gestor", "final": "Entrevista Final / Proposta"}[itype]
            int_status = "completed" if c["stage"] in ("offer", "interview_manager") else "scheduled"
            int_start = _dt(7 if c["stage"] == "offer" else 5 if c["stage"] == "interview_manager" else 3)

            await db.execute(text("""
                INSERT INTO interviews (
                    id, title, interview_type, interview_mode,
                    candidate_id, candidate_name, candidate_email,
                    interviewer_name, interviewer_email,
                    start_time, end_time, duration_minutes, timezone,
                    status, job_vacancy_id, job_title, application_stage,
                    company_id, created_by, created_at, updated_at
                ) VALUES (
                    :id, :title, :itype, 'video',
                    :candidate_id, :name, :email,
                    'Rafaela Mendonça', 'rafaela.mendonca@democompany.com.br',
                    :start_time, :end_time, 60, 'America/Sao_Paulo',
                    :status, :vacancy_id, :vacancy_title, :stage,
                    :company_id, 'seed', :created_at, :updated_at
                ) ON CONFLICT (id) DO NOTHING
            """), {
                "id": int_id,
                "title": int_title,
                "itype": itype,
                "candidate_id": cid,
                "name": c["name"],
                "email": c["email"],
                "start_time": int_start,
                "end_time": int_start + timedelta(hours=1),
                "status": int_status,
                "vacancy_id": VACANCY_ID,
                "vacancy_title": VACANCY_TITLE,
                "stage": c["stage"],
                "company_id": COMPANY_ID,
                "created_at": _dt(20),
                "updated_at": _dt(1),
            })

            # Interview Feedback (apenas para entrevistas já realizadas)
            if int_status == "completed":
                ifb_id = _sid(f"ifeedback_{c['key']}_1")
                level = c["profile_level"]
                ratings = {"excelente": (4.8, 4.6, 4.7, 4.75), "alto": (4.0, 3.8, 3.9, 3.9), "medio": (3.2, 3.0, 3.3, 3.15)}
                r = ratings.get(level, ratings["alto"])
                await db.execute(text("""
                    INSERT INTO interview_feedbacks (
                        id, interview_id,
                        interviewer_name, interviewer_email, interviewer_role,
                        technical_skills_rating, communication_rating,
                        cultural_fit_rating, overall_rating,
                        strengths, weaknesses, notes, recommendation,
                        created_at, updated_at
                    ) VALUES (
                        :id, :interview_id,
                        'Rafaela Mendonça', 'rafaela.mendonca@democompany.com.br', 'HRBP',
                        :tech, :comm, :cult, :overall,
                        :strengths, :weaknesses, :notes, :rec,
                        :created_at, :updated_at
                    ) ON CONFLICT (id) DO NOTHING
                """), {
                    "id": ifb_id,
                    "interview_id": int_id,
                    "tech": r[0], "comm": r[1], "cult": r[2], "overall": r[3],
                    "strengths": json.dumps(["Conhecimento técnico sólido", "Comunicação clara", "Visão estratégica"]),
                    "weaknesses": json.dumps([] if level == "excelente" else ["Pode desenvolver mais experiência em X"]),
                    "notes": f"Candidato(a) demonstrou excelente domínio da área. Recomendo avanço para próxima etapa.",
                    "rec": "advance" if level in ("excelente", "alto") else "hold",
                    "created_at": _dt(6),
                    "updated_at": _dt(6),
                })

    logger.info("✅ Seed concluído com sucesso!")


async def clean(db):
    logger.info("Removendo dados do seed diretor_juridico...")
    # Remove by candidate source tag
    await db.execute(text("DELETE FROM candidates WHERE source = :tag"), {"tag": SEED_TAG})
    logger.info("✅ Limpeza concluída.")


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if not any([args.seed, args.clean, args.reset]):
        parser.print_help()
        return

    async with AsyncSessionLocal() as db:
        async with db.begin():
            if args.clean or args.reset:
                await clean(db)
            if args.seed or args.reset:
                await seed(db)


if __name__ == "__main__":
    asyncio.run(main())
