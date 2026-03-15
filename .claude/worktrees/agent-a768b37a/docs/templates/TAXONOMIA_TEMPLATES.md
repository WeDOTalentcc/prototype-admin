# Taxonomia de Templates de Vagas - LIA Fast Track

**Versão:** 1.0  
**Data:** 01/02/2026

## Objetivo

Expandir a base de templates de vagas de **60 → 480+** para acelerar o Fast Track e melhorar a cobertura de cargos.

---

## Estrutura Atual

### Categorias e Subcategorias

| Categoria | Subcategorias | Templates Atuais |
|-----------|---------------|------------------|
| **tecnologia** | desenvolvimento, dados, infra, seguranca, design, gestao, suporte | 15 |
| **financas** | contabilidade, tributario, controladoria, tesouraria, auditoria, credito | 9 |
| **rh** | recrutamento, generalista, dp, remuneracao, td, cultura | 8 |
| **comercial** | inside_sales, field_sales, vendas_tecnicas, canais, sales_ops, ecommerce | 10 |
| **marketing** | digital, conteudo, branding, produto, analytics | 8 |
| **operacoes** | logistica, supply_chain, compras, producao, qualidade, facilities | 0 |
| **juridico** | trabalhista, societario, contratos, compliance | 0 |
| **engenharia** | civil, mecanica, eletrica, producao, seguranca_trabalho | 0 |

**TOTAL ATUAL:** ~60 templates

---

## Meta de Expansão

### Fase 1: 100 Templates (Quick Wins)
Priorizar áreas com alta demanda de mercado:

| Categoria | Subcategoria | Templates Novos |
|-----------|--------------|-----------------|
| tecnologia | desenvolvimento | +10 (Backend, DevOps, QA) |
| tecnologia | dados | +8 (Data Analyst, ML Engineer) |
| comercial | inside_sales | +6 (SDR, BDR, Account Exec) |
| marketing | digital | +6 (Performance, Growth) |
| rh | generalista | +5 (Business Partner, People Ops) |
| financas | controladoria | +5 (FP&A, Controller) |
| **Subtotal** | | **+40 templates** |

### Fase 2: 250 Templates (Cobertura Ampla)
Expandir todas as categorias existentes:

| Categoria | Meta Total |
|-----------|------------|
| tecnologia | 60 |
| comercial | 40 |
| marketing | 35 |
| financas | 30 |
| rh | 30 |
| operacoes | 25 |
| juridico | 15 |
| engenharia | 15 |
| **TOTAL** | **250** |

### Fase 3: 480+ Templates (Cobertura Completa)
Adicionar variações por:
- **Senioridade:** junior, pleno, senior, especialista, coordenador, gerente, diretor
- **Modelo de trabalho:** remoto, hibrido, presencial
- **Tipo de empresa:** startup, scaleup, enterprise, consultoria

---

## Schema de Template

```json
{
  "category": "tecnologia",
  "subcategory": "desenvolvimento",
  "title": "Desenvolvedor(a) Backend Python",
  "title_alternatives": ["Python Developer", "Dev Backend", "Engenheiro de Software Python"],
  "seniority": "pleno",
  "default_description": "Responsável pelo desenvolvimento de APIs e microsserviços...",
  "default_responsibilities": [
    "Desenvolver e manter APIs RESTful",
    "Escrever testes unitários e de integração",
    "Participar de code reviews",
    "Documentar soluções técnicas",
    "Colaborar com times de produto e frontend"
  ],
  "default_requirements": "3+ anos de experiência com Python, conhecimento em frameworks como FastAPI ou Django...",
  "default_nice_to_have": "Experiência com AWS, Docker, Kubernetes...",
  "default_skills": [
    {"name": "Python", "category": "linguagem", "level": "avancado", "weight": 1.0, "required": true},
    {"name": "FastAPI", "category": "framework", "level": "intermediario", "weight": 0.9, "required": true},
    {"name": "PostgreSQL", "category": "banco_dados", "level": "intermediario", "weight": 0.8, "required": true},
    {"name": "Docker", "category": "devops", "level": "basico", "weight": 0.6, "required": false},
    {"name": "Git", "category": "ferramenta", "level": "avancado", "weight": 0.7, "required": true}
  ],
  "default_behavioral": [
    {"name": "Comunicação", "weight": 0.8, "justification": "Colaboração constante com times multidisciplinares"},
    {"name": "Pensamento Analítico", "weight": 0.9, "justification": "Resolução de problemas técnicos complexos"},
    {"name": "Proatividade", "weight": 0.7, "justification": "Busca contínua por melhorias no código"}
  ],
  "salary_range_min": 8000,
  "salary_range_max": 14000,
  "salary_currency": "BRL",
  "work_model": "hybrid",
  "employment_type": "clt",
  "experience_years_min": 3,
  "experience_years_max": 6
}
```

---

## Qualidade (WSI Quality Gates)

Cada template deve ter no mínimo:
- **5 technical skills** com levels e weights
- **3 behavioral competencies** com justificativas
- **5 responsibilities** detalhadas
- **Salary range** realista para o mercado brasileiro

---

## Arquivos de Templates

| Arquivo | Categoria | Templates |
|---------|-----------|-----------|
| `curated_templates_tech.py` | tecnologia | 15 |
| `curated_templates_vendas.py` | comercial | 10 |
| `curated_templates_rh.py` | rh | 8 |
| `curated_templates_financas.py` | financas | 9 |
| `curated_templates_marketing.py` | marketing | 8 |
| `brazilian_job_templates.py` | misto | 10 |

---

## Cargos Prioritários para Expansão

### Tecnologia (Fase 1)
1. DevOps Engineer (Júnior, Pleno, Sênior)
2. QA Engineer / Analista de Testes
3. Tech Lead / Líder Técnico
4. Arquiteto de Soluções
5. Engenheiro de Plataforma
6. SRE (Site Reliability Engineer)
7. Mobile Developer (iOS/Android/Flutter)
8. Desenvolvedor Full Stack
9. Desenvolvedor Frontend React
10. Data Engineer

### Comercial (Fase 1)
1. SDR (Sales Development Representative)
2. BDR (Business Development Representative)
3. Account Executive
4. Customer Success Manager
5. Key Account Manager
6. Gerente Comercial

### RH (Fase 1)
1. HR Business Partner
2. Talent Acquisition Specialist
3. People Operations
4. Coordenador de RH
5. Especialista em Remuneração

---

## Próximos Passos

1. ✅ Documentar taxonomia (este documento)
2. ⏳ Criar 40 templates prioritários (Fase 1)
3. ⏳ Script de importação com validação
4. ⏳ Expandir para 250 templates (Fase 2)
5. ⏳ Adicionar variações por senioridade (Fase 3)
