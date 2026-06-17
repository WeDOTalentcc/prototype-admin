# Glossário Central da Plataforma LIA

> **Fonte da verdade única** para toda a terminologia da LIA / WeDOTalent.
> Geração e sincronização automatizada via `scripts/glossary_sync.py`.
>
> **Como manter:** ver [`GLOSSARY_MAINTENANCE.md`](./GLOSSARY_MAINTENANCE.md).
> **Como rodar o sync localmente:** `python3 scripts/glossary_sync.py` ou `make glossary-sync`.
>
> **last_updated:** 2026-04-20
> **total_terms:** 55

---

## Schema de cada entrada

| Campo | Descrição |
|---|---|
| **Termo** | Nome oficial — use sempre este (nunca sinônimos) |
| **Sigla** | Abreviação canônica, se houver |
| **Definição** | Descrição curta (≤ 3 frases) |
| **Categoria** | Scoring \| Behavioral \| Compliance \| Sistema \| Tool/Action |
| **Fontes** | Documento WeDO canônico de referência |
| **Código relacionado** | Arquivo(s)/classe(s) principais no repositório |
| **Owner** | Time responsável pelo termo |
| **last_updated** | Data da última revisão |

---

## A

### Abertura (Openness)
| Campo | Valor |
|---|---|
| **Sigla** | O (OCEAN) |
| **Definição** | Dimensão do Big Five que mede curiosidade intelectual, criatividade e receptividade a novas ideias. Indicadores: projetos inovadores, diversidade de experiências, aprendizado contínuo. |
| **Categoria** | Behavioral |
| **Fontes** | `WeDO/LIA_METHODOLOGY.md` §1.1, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.5 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/schemas/screening.py` → `BigFiveProfile` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

### Amabilidade (Agreeableness)
| Campo | Valor |
|---|---|
| **Sigla** | A (OCEAN) |
| **Definição** | Dimensão do Big Five que mede cooperação, empatia e orientação ao coletivo. Indicadores: trabalho em equipe, mentoria, resolução de conflitos. |
| **Categoria** | Behavioral |
| **Fontes** | `WeDO/LIA_METHODOLOGY.md` §1.1, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.5 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/schemas/screening.py` → `BigFiveProfile` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

### Arquétipo (Archetype)
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Perfil de personalidade composto derivado de combinações das 5 dimensões OCEAN. São 8 arquétipos canônicos: Catalisador Visionário, Executor Confiável, Guardião de Clientes, Estrategista Analítico, Mediador Adaptável, Rainmaker Audacioso, Operador Resiliente, Arquiteto Metódico. |
| **Categoria** | Behavioral |
| **Fontes** | `WeDO/LIA_METHODOLOGY.md` §1.2 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

---

## B

### BARS
| Campo | Valor |
|---|---|
| **Sigla** | BARS — Behaviorally Anchored Rating Scales |
| **Definição** | Escala de avaliação com âncoras comportamentais específicas (Missing=0, Partial=40, Meets=75, Exceeds=100) usada para avaliar CV vs. requisitos da vaga. Reduz viés de avaliador. Base: Smith & Kendall (1963). |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/LIA_UNIFIED_METHODOLOGY.md` §3, `WeDO/LIA_METHODOLOGY.md` §4 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

### Big Five
| Campo | Valor |
|---|---|
| **Sigla** | OCEAN |
| **Definição** | Modelo de personalidade NEO-PI-R com 5 traços: Abertura (O), Conscienciosidade (C), Extroversão (E), Amabilidade (A), Estabilidade Emocional / Neuroticismo (N). Cada traço mapeado em escala 0–100. Base: Costa & McCrae (1992). |
| **Categoria** | Behavioral |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, `WeDO/LIA_METHODOLOGY.md` §1 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/schemas/screening.py` → `BigFiveProfile` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

### Bloco A
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Conjunto de fases (F1–F6) do pipeline WSI executadas uma única vez por vaga, durante a criação. Inclui avaliação do JD, extração Big Five, geração de perguntas. |
| **Categoria** | Sistema |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_service.py` |
| **Owner** | Engenharia |
| **last_updated** | 2026-04-20 |

### Bloco B
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Conjunto de fases (F7–F11) do pipeline WSI executadas para cada candidato em triagem. Inclui coleta de respostas, scoring, geração de relatório. |
| **Categoria** | Sistema |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py` |
| **Owner** | Engenharia |
| **last_updated** | 2026-04-20 |

### Bloom (Taxonomia de Bloom)
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Taxonomia de 6 níveis cognitivos usada para calibrar perguntas WSI: 1=Lembrar, 2=Compreender, 3=Aplicar, 4=Analisar, 5=Avaliar, 6=Criar. Base: Anderson et al. (2001), revisão de Bloom (1956). |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.3 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

---

## C

### Calibration Loop
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Camada 4 da metodologia unificada LIA. Mecanismo de aprendizado contínuo que ajusta pesos de scoring com base em feedback do recrutador sobre candidatos aprovados/reprovados. |
| **Categoria** | Sistema |
| **Fontes** | `WeDO/LIA_UNIFIED_METHODOLOGY.md` §1 (diagrama), §4.12 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/` |
| **Owner** | Data Science |
| **last_updated** | 2026-04-20 |

### CBI
| Campo | Valor |
|---|---|
| **Sigla** | CBI — Competency-Based Interview |
| **Definição** | Metodologia de entrevista estruturada baseada em evidências de comportamentos passados reais. Toda pergunta WSI deve solicitar situação passada real — perguntas hipotéticas são proibidas. Base: McClelland (Harvard, 1973). |
| **Categoria** | Behavioral |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.2 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_question_generator.py` |
| **Owner** | Produto |
| **last_updated** | 2026-04-20 |

### Compact (Modo Compact)
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Modo de triagem WSI com 6 perguntas no total: 3 técnicas + 3 comportamentais. Duração estimada: ~13 min. Alternativa ao modo Full. |
| **Categoria** | Sistema |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.13 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_screening_pipeline.py` → `MODEL_DISTRIBUTIONS` |
| **Owner** | Produto |
| **last_updated** | 2026-04-20 |

### Conscienciosidade (Conscientiousness)
| Campo | Valor |
|---|---|
| **Sigla** | C (OCEAN) |
| **Definição** | Dimensão do Big Five que mede organização, disciplina e orientação a resultados. Indicadores: entregas consistentes, progressão de carreira, certificações. |
| **Categoria** | Behavioral |
| **Fontes** | `WeDO/LIA_METHODOLOGY.md` §1.1, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.5 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/schemas/screening.py` → `BigFiveProfile` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

---

## D

### Dreyfus (Modelo Dreyfus)
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Escala de 5 níveis de proficiência em habilidades: 1=Novato, 2=Iniciante Avançado, 3=Competente, 4=Proficiente, 5=Expert. Parâmetro ativo na geração e avaliação de perguntas WSI. Base: Dreyfus & Dreyfus (1980/1986). |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.4 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

### Dreyfus Comportamental
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Adaptação do Modelo Dreyfus para medir maturidade de reflexão e agência comportamental: 1=segue regras de outros; 5=cria sistemas que outros adotam. Usado na avaliação de respostas comportamentais (Bloco 4). |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

### Dynamic Cutoff
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Threshold dinâmico de aprovação/reprovação recalculado automaticamente após 30–50 triagens por vaga. Utiliza percentis (top 25% = aprovado, 25–60% = revisão manual, <60% = reprovado). |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.10 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/` |
| **Owner** | Data Science |
| **last_updated** | 2026-04-20 |

### DEI
| Campo | Valor |
|---|---|
| **Sigla** | DEI — Diversity, Equity, Inclusion |
| **Definição** | Pilar de governança que garante que decisões de triagem e ranking da LIA sejam livres de viés discriminatório por raça, gênero, idade, deficiência ou outros atributos protegidos. Implementado via FairnessGuard e Bias Audit. |
| **Categoria** | Compliance / Governança |
| **Fontes** | `attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md` §DEI, `.agents/skills/lia-compliance/SKILL.md` |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/bias_audit_service.py` |
| **Owner** | Compliance / Produto |
| **last_updated** | 2026-04-20 |

---

## E

### Elegibilidade
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Perguntas binárias (sim/não) configuradas pelo recrutador para requisitos obrigatórios da vaga (ex.: disponibilidade, localização, PCD). Compõem o Bloco 2 do pipeline WSI. |
| **Categoria** | Sistema |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §2 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_screening_pipeline.py` |
| **Owner** | Produto |
| **last_updated** | 2026-04-20 |

### Estabilidade Emocional (Emotional Stability)
| Campo | Valor |
|---|---|
| **Sigla** | N↓ (OCEAN — inverso do Neuroticismo) |
| **Definição** | Dimensão do Big Five que mede controle emocional e resiliência sob pressão. Baixo Neuroticismo = alta estabilidade. Indicadores: gestão de pressão, adaptabilidade, tomada de decisão. |
| **Categoria** | Behavioral |
| **Fontes** | `WeDO/LIA_METHODOLOGY.md` §1.1, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.5 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/schemas/screening.py` → `BigFiveProfile` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

### EU AI Act
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Regulamentação europeia de IA (regulamento UE 2024/1689) que classifica sistemas de triagem de candidatos como alto risco. Requer explicabilidade, supervisão humana e auditabilidade dos scores. |
| **Categoria** | Compliance |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §Apêndice C |
| **Código relacionado** | `lia-agent-system/app/shared/compliance/` |
| **Owner** | Jurídico / Produto |
| **last_updated** | 2026-04-20 |

### Extroversão (Extraversion)
| Campo | Valor |
|---|---|
| **Sigla** | E (OCEAN) |
| **Definição** | Dimensão do Big Five que mede sociabilidade, assertividade e energia social. Indicadores: liderança de equipes, apresentações, networking. |
| **Categoria** | Behavioral |
| **Fontes** | `WeDO/LIA_METHODOLOGY.md` §1.1, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.5 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/schemas/screening.py` → `BigFiveProfile` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

---

## F

### FairnessGuard
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Componente transversal que bloqueia filtros discriminatórios por atributos protegidos (gênero, raça, idade, religião, etc.), adiciona disclaimers obrigatórios e registra métricas de compliance. Existe em 2 variantes: `JobFairnessGuard` (vagas) e `FairnessGuard` (sourcing). |
| **Categoria** | Compliance |
| **Fontes** | `WeDO/diagnosticos/DIAGNOSTICO_FAIRNESSGUARD_V5_vs_LIA.md` |
| **Código relacionado** | `lia-agent-system/app/domains/sourcing/fairness.py`, `lia-agent-system/app/domains/job_management/fairness.py` |
| **Owner** | Engenharia / Jurídico |
| **last_updated** | 2026-04-20 |

### Full (Modo Full)
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Modo de triagem WSI com 10 perguntas no total: 5 técnicas + 5 comportamentais (3 Big Five + 2 CBI cultural). Duração estimada: ~18 min. |
| **Categoria** | Sistema |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.13 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_screening_pipeline.py` → `MODEL_DISTRIBUTIONS` |
| **Owner** | Produto |
| **last_updated** | 2026-04-20 |

---

## G

### Gate (G1–G6)
| Campo | Valor |
|---|---|
| **Sigla** | G1, G2, G3, G4, G5, G6 |
| **Definição** | Critérios absolutos de reprovação que se sobrepõem ao score WSI. Um candidato com WSI 9.5 que ative qualquer gate é reprovado. Os 6 gates cobrem: elegibilidade, red flags críticos, integridade de respostas, score mínimo por bloco, requisitos eliminatórios de vaga, e compliance. |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, §F10 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py` → `detect_red_flags()`, `lia-agent-system/app/domains/cv_screening/constants/wsi_constants.py` |
| **Owner** | Produto / Engenharia |
| **last_updated** | 2026-04-20 |

---

## H

### HITL
| Campo | Valor |
|---|---|
| **Sigla** | HITL — Human-in-the-Loop |
| **Definição** | Modelo de supervisão em que um agente de IA executa tarefas mas aguarda aprovação humana antes de ações de alto impacto (ex.: envio de proposta, reprovação definitiva, escalonamento). Configurável por nível de autonomia na plataforma LIA. |
| **Categoria** | Sistema / Governança |
| **Fontes** | `WeDO/LIA_UNIFIED_METHODOLOGY.md` §Agentes, `attached_assets/WEDOTALENT_GUIA_COMPLETO_v3.3_PT.md` §HITL |
| **Código relacionado** | `lia-agent-system/app/domains/agent_studio/services/agent_approval_service.py` |
| **Owner** | Engenharia / Produto |
| **last_updated** | 2026-04-20 |

---

## I

### Inflação
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Padrão detectado automaticamente onde o candidato autodeclara expertise elevado (autodeclaração 4–5) mas não apresenta evidências concretas nas respostas. Gera penalidade de -1.0 a -3.0 no score da resposta. |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.9 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py` |
| **Owner** | Data Science |
| **last_updated** | 2026-04-20 |

---

## J

### JD
| Campo | Valor |
|---|---|
| **Sigla** | JD — Job Description |
| **Definição** | Descrição da vaga fornecida pelo recrutador. Deve ter JD Quality Score ≥ 50 para prosseguir para geração de perguntas. O JD é o input primário do Bloco A. |
| **Categoria** | Sistema |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, §F1 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_service.py` → `analyze_jd_and_suggest_competencies()` |
| **Owner** | Produto |
| **last_updated** | 2026-04-20 |

### JD Quality Score
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Score determinístico (0–100) calculado antes de invocar LLM que mede a qualidade do JD para geração de perguntas. Avalia 9 dimensões (título, responsabilidades, skills, comportamentais, consistência, inconsistências, contexto, linguagem inclusiva, densidade). Threshold mínimo: 50. |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, §1.4 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_service.py` |
| **Owner** | Engenharia / Produto |
| **last_updated** | 2026-04-20 |

---

## L

### LGPD
| Campo | Valor |
|---|---|
| **Sigla** | LGPD — Lei Geral de Proteção de Dados |
| **Definição** | Lei brasileira (Lei 13.709/2018) de proteção de dados pessoais. Exige consentimento para análise automatizada de candidatos, direito de opt-out e retenção de dados por período definido. |
| **Categoria** | Compliance |
| **Fontes** | `WeDO/LIA_METHODOLOGY.md` §6.3, `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §Apêndice C |
| **Código relacionado** | `lia-agent-system/app/shared/compliance/` |
| **Owner** | Jurídico |
| **last_updated** | 2026-04-20 |

### LLM Extrator
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Uso do LLM com temperature=0.0 para extrair sinais estruturados (Bloom demonstrado, Dreyfus demonstrado) de respostas de candidatos — sem atribuir notas. Dois candidatos com respostas idênticas recebem extração idêntica. |
| **Categoria** | Sistema |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, §0.3 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py` |
| **Owner** | Engenharia |
| **last_updated** | 2026-04-20 |

---

## N

### Neuroticismo
| Campo | Valor |
|---|---|
| **Sigla** | N (OCEAN) |
| **Definição** | Dimensão do Big Five que mede instabilidade emocional. No contexto WSI, usa-se o inverso (Estabilidade Emocional = N↓). Baixo Neuroticismo indica resiliência e controle sob pressão. |
| **Categoria** | Behavioral |
| **Fontes** | `WeDO/LIA_METHODOLOGY.md` §1.1 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/schemas/screening.py` → `BigFiveProfile` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

---

## O

### OCEAN
| Campo | Valor |
|---|---|
| **Sigla** | OCEAN |
| **Definição** | Acrônimo do modelo Big Five: Openness (Abertura), Conscientiousness (Conscienciosidade), Extraversion (Extroversão), Agreeableness (Amabilidade), Neuroticism (Neuroticismo). Ver **Big Five**. |
| **Categoria** | Behavioral |
| **Fontes** | `WeDO/LIA_METHODOLOGY.md` §1, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.5 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/schemas/screening.py` → `BigFiveProfile` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

---

## P

### Prior O\*NET
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Perfil de personalidade Big Five esperado por arquétipo de cargo, derivado da base ocupacional O\*NET do Departamento do Trabalho dos EUA e da meta-análise Barrick & Mount (1991). Peso 0.35 na fórmula de ranking de traits. |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, §F3 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_service.py` |
| **Owner** | Data Science |
| **last_updated** | 2026-04-20 |

### PromptInjectionGuard
| Campo | Valor |
|---|---|
| **Sigla** | SEG-1 |
| **Definição** | Componente de segurança que detecta e bloqueia tentativas de injeção de prompts em respostas de candidatos. Resposta bloqueada recebe score=0.0 (zero absoluto). |
| **Categoria** | Compliance |
| **Fontes** | `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.9 |
| **Código relacionado** | `lia-agent-system/app/shared/security/` |
| **Owner** | Engenharia / Segurança |
| **last_updated** | 2026-04-20 |

---

## R

### Red Flag
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Sinal de alerta detectado automaticamente na resposta do candidato. Não reprova o candidato, mas é destacado no relatório para o consultor. Exemplos: inflação severa, resposta evasiva, inconsistência entre autodeclaração e evidências. |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py` → `detect_red_flags()` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

---

## S

### Scoring Rubric
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Descrição textual por banda de score (1–3, 4–6, 7–9, 10) persistida junto a cada pergunta WSI. Define os critérios de avaliação de respostas para aquela pergunta específica. |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/schemas/screening.py` → `ScreeningQuestion` |
| **Owner** | Produto |
| **last_updated** | 2026-04-20 |

### SHA-256
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Hash criptográfico das respostas brutas do candidato gerado no momento da coleta. Garante integridade e imutabilidade dos dados para auditoria (EU AI Act, LGPD). Respostas alteradas após hashing são detectáveis. |
| **Categoria** | Compliance |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, §0.4 (regra 6) |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_screening_pipeline.py` |
| **Owner** | Engenharia |
| **last_updated** | 2026-04-20 |

### Smart Saturation
| Campo | Valor |
|---|---|
| **Sigla** | Saturação Inteligente |
| **Definição** | Mecanismo que pausa a triagem automática quando o número de candidatos aprovados atinge o threshold (padrão: 20). Evita gargalos no pipeline e garante foco na avaliação dos candidatos já triados. O recrutador pode desbloquear manualmente. |
| **Categoria** | Sistema |
| **Fontes** | `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.11 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/` |
| **Owner** | Produto |
| **last_updated** | 2026-04-20 |

### STAR
| Campo | Valor |
|---|---|
| **Sigla** | STAR — Situação, Tarefa, Ação, Resultado |
| **Definição** | Framework estrutural do CBI para avaliação de respostas comportamentais. Respostas sem estrutura STAR completa recebem penalidade de -0.6. Bônus de +1.0 para respostas com estrutura excepcionalmente completa e evidências mensuráveis. |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, `WeDO/LIA_UNIFIED_METHODOLOGY.md` §4.9 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

### SystemPromptBuilder
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Componente central que compõe dynamicamente system prompts para todos os agentes LIA combinando: persona base, adições de domínio, contexto de tenant, contexto do usuário, histórico de conversa e regras anti-repetição. |
| **Categoria** | Sistema |
| **Fontes** | `lia-agent-system/app/shared/prompts/system_prompt_builder.py` |
| **Código relacionado** | `lia-agent-system/app/shared/prompts/system_prompt_builder.py` → `SystemPromptBuilder` |
| **Owner** | Engenharia |
| **last_updated** | 2026-04-20 |

---

## T

### Trait
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Um dos 5 traços do Big Five (OCEAN) avaliados durante a triagem WSI. O ranking de traits determina o peso das perguntas comportamentais no score final. |
| **Categoria** | Behavioral |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_service.py` → `_select_comp_by_trait()` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

---

## W

### WSI
| Campo | Valor |
|---|---|
| **Sigla** | WSI — Work Suitability Index |
| **Definição** | Score final de triagem (0–10) que resume a adequação do candidato à vaga. Composição: WSI_tecnico + WSI_comportamental com pesos ajustados por senioridade. Aprovado ≥ 7.0, Aguardando 5.0–6.9, Reprovado < 5.0. |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, §F9 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py` → `calculate_wsi_deterministic()` |
| **Owner** | Produto / Data Science |
| **last_updated** | 2026-04-20 |

### WSI_comportamental
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Média ponderada dos scores do bloco comportamental (F9), com pesos proporcionais ao ranking de traits extraído do JD. Cada trait tem peso conforme posição no ranking Big Five da vaga. |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, §F9 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py` |
| **Owner** | Data Science |
| **last_updated** | 2026-04-20 |

### WSI Final
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Composição de WSI_tecnico e WSI_comportamental com pesos ajustados por senioridade do candidato. É 100% determinístico e auditável — nenhuma caixa preta na decisão final. |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, §F9 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py` → `calculate_wsi_deterministic()` |
| **Owner** | Data Science |
| **last_updated** | 2026-04-20 |

### WSI_tecnico
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Média simples dos scores de todas as perguntas do bloco técnico (F9). Cada pergunta técnica recebe score 0–10 via fórmula determinística (0.60×autodeclaração + 0.40×contexto ± penalidades/bônus). |
| **Categoria** | Scoring |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` §GLOSSÁRIO, §F9 |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_deterministic_scorer.py` |
| **Owner** | Data Science |
| **last_updated** | 2026-04-20 |

### WSIInterviewGraph
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | State machine LangGraph que orquestra o canal de triagem por chat (E2). Gerencia o fluxo de perguntas, respostas, scoring em tempo real e transições de estado durante a triagem. |
| **Categoria** | Sistema |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` (Índice Rápido) |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/agents/wsi_interview_graph.py` → `WSIInterviewGraph` |
| **Owner** | Engenharia |
| **last_updated** | 2026-04-20 |

### WSIVoiceOrchestrator
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | Componente que gerencia o canal de triagem por voz (E3), integrando com OpenMic.ai. Cria agente de voz, inicia chamada, processa transcrição e aciona o pipeline de scoring. |
| **Categoria** | Sistema |
| **Fontes** | `WeDO/wsi/WSI_METHODOLOGY_COMPLETE_v2.md` (Índice Rápido) |
| **Código relacionado** | `lia-agent-system/app/domains/cv_screening/services/wsi_voice_orchestrator.py` → `WSIVoiceOrchestrator` |
| **Owner** | Engenharia |
| **last_updated** | 2026-04-20 |

---


## Termos pendentes (TODO: needs definition)

<!-- glossary_sync.py adiciona automaticamente stubs aqui quando detecta novos termos -->



### AnonymizationPipeline
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### AutonomousActionsEngine
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### DemoDataGenerator
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### IntelligentDataOrchestrator
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### InterviewGraph
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### JobCreationGraph
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### JobWizardGraph
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### MainOrchestrator
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### MessageGenerator
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### OnboardingOrchestrator
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### ParamExtractor
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### PolicyEngine
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### SkillsOntologyEngine
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### SmartExtractor
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### SourcingAgentOrchestrator
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### StageAutomationEngine
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### TastingEngine
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### TeamsProactivityEngine
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### TeamsTabTriggerEngine
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### VoiceScreeningOrchestrator
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### WSICompactPipeline
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### WSIFeedbackGenerator
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### WSILayer2Extractor
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### WSIQuestionGenerator
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### WSIReportGenerator
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### WSIScreeningPipeline
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### add_candidate_to_vacancy
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### add_to_list
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### add_to_talent_pool
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### advance_campaign_stage
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### analyze_interview_recording
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### analyze_skill_gaps
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### bulk_update_candidates_stage
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### calibrate_sourcing_agent
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### cancel_vacancy
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### capture_wizard_feedback
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### compare_interview_performance
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### confirm_autonomous_action
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### confirm_placement
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### create_digital_twin
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### create_job
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### create_nurture_sequence
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### create_offer_letter
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### create_recruitment_campaign
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### create_sourcing_agent
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### create_talent_pool
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### detect_interview_bias
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### detect_pending_decisions
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### evaluate_with_twin
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### export_candidates
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### forecast_hiring_needs
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### generate_candidate_feedback
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### generate_enriched_jd
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### generate_interview_opinion
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### generate_report
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_agent_status
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_autonomous_actions
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_campaign_progress
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_candidate_details
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_candidate_stats
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_company_config
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_engagement_metrics
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_external_applications
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_intelligent_salary
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_intelligent_skills
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_job_details
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_job_suggestions
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_learning_insights
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_market_intelligence
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_pipeline_stats
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_pool_candidates
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_proactive_alerts
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_skill_adjacencies
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### get_vacancy_funnel
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### hide_candidate
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### infer_related_skills
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### list_digital_twins
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### list_talent_pools
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### map_candidate_skills_to_ontology
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### match_internal_candidates
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### move_pool_to_job
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### pause_vacancy
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### publish_job
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### publish_to_job_board
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### record_hiring_outcome
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### reject_autonomous_action
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### reject_candidate
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### run_multi_strategy_search
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### save_job_draft
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### schedule_report
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### search_candidates
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### search_candidates_pearch
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### search_jobs
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### search_salary_benchmark
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### send_email
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### send_whatsapp
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### shortlist_candidate
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### suggest_reengagement
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### update_candidate_stage
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### update_job
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### validate_job_fields
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |


### wsi_screening
| Campo | Valor |
|---|---|
| **Sigla** | — |
| **Definição** | TODO: needs definition |
| **Categoria** | TODO |
| **Fontes** | TODO |
| **Código relacionado** | TODO |
| **Owner** | TODO |
| **last_updated** | 2026-04-20 |

