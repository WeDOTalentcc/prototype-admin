## Análise de Impacto: Remoção do Bloco 3 (Elegibilidade e Formação) do Roteiro WSI

### Resumo
Remover o Bloco 3 ("Elegibilidade e Formação") do roteiro WSI de 7 blocos (0-6), passando de 7 para 6 blocos (0-5). As perguntas de elegibilidade migram para o Bloco 2 ("Perguntas Padrão da Empresa"), configuráveis pelo recruiter. O pré-qualificador de Formação Acadêmica (`FormacaoPreQualifierResult`) e o `EligibilityVerificationService` são removidos. Blocos 4 e 5 são renumerados para 3 e 4. O resultado final é um roteiro mais enxuto: 0-Abordagem, 1-Apresentação, 2-Empresa (incluindo elegibilidade), 3-Técnicas, 4-Comportamentais/Fit, 5-Encerramento.

### Dimensões Impactadas

| Dimensão | Impacto | O que fazer |
|----------|---------|-------------|
| **Frontend** | **Alto** | Remover Block 3 de WSI_BLOCKS em 3 locais, renumerar blocos 4→3, 5→4, 6→5. Remover filtros `block_id===3`, `isBlock3()`. Ajustar `WSIQuestionsStage.tsx` (remover seção "Perguntas de Elegibilidade"). Ajustar `use-screening-questions.ts` (remover `eligibilityQuestions` filtrada por `block_id===3`). Ajustar `ScreeningQuestionsPanel.tsx`. |
| **Backend API** | **Médio** | Remover `formacao_pre_qualifier` do response schema. Ajustar endpoints WSI que referenciam Block 3. |
| **Backend Services** | **Alto** | Remover `_build_eligibility_block()` do `WSIScreeningPipeline`. Remover `EligibilityVerificationService` (2 cópias). Ajustar `MODEL_DISTRIBUTIONS` (sem `eligibility` quota). Ajustar `wsi_question_adjuster.py` (remover bloco 3). Ajustar `triagem_session_service.py` (remover bloco elegibilidade). |
| **Banco de Dados** | **Baixo** | Sem migration. O campo `eligibility_questions` em `job_vacancies` já será servido via Block 2 (company questions). |
| **Constantes WSI** | **Alto** | Renumerar `WSI_BLOCK_NAMES` em `wsi_constants.py`. Remover `FORMACAO_PRE_QUALIFIER_*`. Atualizar `__init__.py` exports. |
| **Schemas** | **Médio** | Remover `FormacaoPreQualifierResult` de `screening.py` (2 locais). Remover `formacao_pre_qualifier` do `WSIScreeningPipelineResponse`. |
| **Agentes IA** | **Médio** | Ajustar `wsi_interview_graph.py` se referencia block types "eligibility". Ajustar prompts de screening em `cv_screening.yaml`. |
| **Comunicações** | **Baixo** | `transition_dispatch_service.py` — verificar se mensagens referenciam elegibilidade. |
| **Testes** | **Médio** | Ajustar `test_sprint1_wsi_constants.py`, `test_screening_pipeline_integration.py`, testes de cobertura. |
| **Compliance/LGPD** | **Nenhum** | Perguntas de elegibilidade permanecem no sistema (via Bloco 2). Nenhum dado pessoal novo. |
| **Segurança** | **Nenhum** | Sem impacto — remoção de código, não adição. |
| **Observabilidade** | **Baixo** | Logs de `_build_eligibility_block` e `EligibilityVerificationService` serão removidos naturalmente. |

### Arquivos Impactados — Detalhamento

#### Backend (lia-agent-system)
| Arquivo | Tipo de Mudança | Criticidade |
|---------|----------------|-------------|
| `app/domains/cv_screening/constants/wsi_constants.py` | Renumerar blocos, remover `FORMACAO_PRE_QUALIFIER_*` | Alta |
| `app/domains/cv_screening/constants/__init__.py` | Remover exports de `FORMACAO_PRE_QUALIFIER_*` | Alta |
| `app/schemas/screening.py` | Remover `FormacaoPreQualifierResult`, remover do response | Alta |
| `app/domains/cv_screening/schemas/screening.py` | Verificar duplicação de schema | Média |
| `app/domains/cv_screening/services/wsi_screening_pipeline.py` | Remover `_build_eligibility_block()`, remover Block 3 logic, ajustar `BLOCK_NAMES`, renumerar, ajustar `MODEL_DISTRIBUTIONS` | Alta |
| `app/domains/cv_screening/services/wsi_question_adjuster.py` | Remover bloco 3 de `WSI_BLOCKS`, renumerar | Média |
| `app/domains/cv_screening/services/eligibility_verification_service.py` | Candidato a remoção completa | Alta |
| `app/services/eligibility_verification_service.py` | Candidato a remoção completa (cópia) | Alta |
| `app/services/triagem_session_service.py` | Remover bloco "Elegibilidade" de `WSI_BLOCKS` | Média |
| `app/services/lia_score_service.py` | Remover tratamento especial `block_type == "eligibility"` | Média |
| `app/domains/cv_screening/tools/__init__.py` | Remover tool "Verificar Elegibilidade" | Baixa |
| `app/domains/cv_screening/domain.py` | Remover referência a eligibility check | Baixa |
| `app/domains/cv_screening/actions.py` | Verificar referências a eligibility | Baixa |
| `tests/test_sprint1_wsi_constants.py` | Ajustar testes de constantes | Média |
| `tests/test_screening_pipeline_integration.py` | Ajustar testes do pipeline | Média |
| `app/api/v1/wsi_screening_pipeline_endpoint.py` | Ajustar se referencia Block 3 | Baixa |

#### Frontend (plataforma-lia)
| Arquivo | Tipo de Mudança | Criticidade |
|---------|----------------|-------------|
| `src/components/jobs/jobsPageConstants.tsx` | Remover bloco 3, renumerar 4→3, 5→4, 6→5 | Alta |
| `src/components/job-creation/ScreeningQuestionsPanel.tsx` | Remover WSI_BLOCKS[3], renumerar, remover `isBlock3()` em `ScreeningScriptTab` | Alta |
| `src/components/expanded-chat/stages/WSIQuestionsStage.tsx` | Remover seção "Perguntas de Elegibilidade" (fallback quando company questions vazio) | Média |
| `src/hooks/use-screening-questions.ts` | Remover `eligibilityQuestions` (filtro `block_id===3`), remover categoria `eligibility` | Média |
| `src/hooks/use-company-eligibility-questions.ts` | Mantém (serve Bloco 2 — company questions) | Nenhuma |
| `src/components/settings/eligibility-questions-bank.ts` | Mantém (banco de templates da empresa) | Nenhuma |
| `src/components/screening-config/ScreeningScriptTab.tsx` | Remover bloco 3, remover `isBlock3()`, renumerar | Média |
| `src/components/screening-config/ScreeningConfigManager.tsx` | Verificar referências a eligibility block | Baixa |

### Nova Estrutura WSI (pós-remoção)

| Bloco | Nome | Descrição |
|-------|------|-----------|
| 0 | Abordagem Inicial | Template WhatsApp automático |
| 1 | Apresentação da Oportunidade | Pitch da vaga |
| 2 | Perguntas Padrão da Empresa | Perguntas da empresa + elegibilidade (configuráveis) |
| 3 | Competências Técnicas | Skills com Bloom/Dreyfus |
| 4 | Competências Comportamentais e Fit | Big Five/CBI + situacionais |
| 5 | Resultado e Encerramento | Score WSI + feedback |

### Ajustes em MODEL_DISTRIBUTIONS

**Antes:**
```python
MODEL_DISTRIBUTIONS = {
    "compact": {"eligibility": 2, "technical": 3, "behavioral": 3, "total": 8},
    "full": {"eligibility": 3, "technical": 5, "behavioral": 4, "total": 12},
}
```

**Depois:**
```python
MODEL_DISTRIBUTIONS = {
    "compact": {"technical": 4, "behavioral": 4, "total": 8},
    "full": {"technical": 6, "behavioral": 6, "total": 12},
}
```

### Destino das Perguntas de Ação Afirmativa

As perguntas afirmativas (`AFFIRMATIVE_QUESTIONS`) atualmente injetadas no Bloco 3 devem migrar para o **Bloco 2** (Empresa), já que se enquadram como perguntas padrão da empresa. O recruiter pode ativar/desativar conforme a vaga.

### Riscos e Mitigações

| Risco | Severidade | Mitigação |
|-------|-----------|-----------|
| Dados existentes com `block_id=3` em triagens já realizadas | Baixa | Dados históricos são read-only. Não há migration destrutiva. |
| Renumeração de blocos (4→3, 5→4, 6→5) pode quebrar referências | Média | Busca exaustiva por `block_id` e `block.*3/4/5/6` em todo o codebase |
| Perguntas afirmativas órfãs se não migradas | Média | Migrar `AFFIRMATIVE_QUESTIONS` para injeção no Bloco 2 |
| `EligibilityVerificationService` usado em fluxo de reconsideração | Média | Verificar se reconsideration flow é usado em produção — se sim, manter lógica mas mover para Block 2 |
| Testes existentes que validam Block 3 | Baixa | Ajustar testes unitários e de integração |

### Pronto para implementar? Sim

Impacto total estimado: ~25 arquivos (15 backend, 10 frontend). Sem migrations de banco. Sem breaking changes em API externa (apenas respostas internas do pipeline).
