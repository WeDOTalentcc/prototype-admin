# Análise de Otimização: Processo de Criação de Vaga

**Data:** 13 de Dezembro de 2025  
**Objetivo:** Identificar oportunidades de preenchimento automático de campos no processo de criação de vaga baseado nos dados pré-cadastrados no Admin.

---

## 1. Resumo Executivo

O processo de criação de vaga via Super Chat da LIA possui **13 etapas** que coletam diversos campos. Muitos desses campos podem ser **pré-preenchidos** ou **sugeridos automaticamente** usando dados já cadastrados nas **Configurações do Admin**, reduzindo significativamente a fricção e o tempo do recrutador.

### Potencial de Redução de Perguntas

| Categoria | Campos | Pode Automatizar | Redução |
|-----------|--------|------------------|---------|
| Informações Básicas | 7 | 4 | 57% |
| Remuneração | 2 | 2 | 100% |
| Estrutura Org. | 4 | 4 | 100% |
| Requisitos Técnicos | 3 | 2 | 67% |
| Entrevistas | 2 | 2 | 100% |
| Governança | 3 | 3 | 100% |
| **TOTAL** | **21** | **17** | **81%** |

---

## 2. Mapeamento Completo: Campos da Vaga × Dados do Admin

### 2.1 Informações Básicas (Etapa 2)

| Campo da Vaga | Tipo | Fonte no Admin | Estratégia de Otimização |
|---------------|------|----------------|--------------------------|
| `job_title` | Obrigatório | - | Entrada manual (único) |
| `department` | Opcional | `Department.name` | **Dropdown** com lista de departamentos cadastrados |
| `location` | Opcional | `Department.location` | **Auto-preencher** ao selecionar departamento |
| `work_model` | Obrigatório | `CompanyProfile.additional_data` | Sugerir modelo padrão da empresa |
| `seniority` | Obrigatório | - | Entrada manual |
| `employment_type` | Opcional | - | Default: CLT |
| `is_confidential` | Obrigatório | - | Default: false |

**Implementação Sugerida:**
```typescript
// Ao selecionar departamento, auto-preencher:
onDepartmentSelect(dept: Department) {
  this.location = dept.location || this.location;
  this.manager_name = dept.manager_name;
  this.manager_email = dept.manager_email;
}
```

---

### 2.2 Remuneração (Etapa 3)

| Campo da Vaga | Tipo | Fonte no Admin | Estratégia de Otimização |
|---------------|------|----------------|--------------------------|
| `salary_range` | Obrigatório | `IdealProfile.salary_range_min/max` | **Sugerir** faixa do perfil ideal por cargo/senioridade |
| `benefits` | Opcional | `Benefit` (filtrado) | **Já implementado** - benefícios por senioridade |

**Já Implementado no `remuneration_collector`:**
- ✅ Benefícios são buscados via `benefits_service.get_benefits_by_seniority()`
- ✅ Benefícios destacados (`is_highlighted`) são pré-selecionados

**Melhoria Sugerida:**
- Buscar `IdealProfile` por `role_type` + `seniority_level` e sugerir `salary_range_min/max`

---

### 2.3 Estrutura Organizacional (Etapa 4)

| Campo da Vaga | Tipo | Fonte no Admin | Estratégia de Otimização |
|---------------|------|----------------|--------------------------|
| `direct_manager` | Obrigatório | `Department.manager_name` | **Auto-preencher** ao selecionar departamento |
| `team_size` | Opcional | `Department.headcount` | **Sugerir** headcount do departamento |
| `team_composition` | Opcional | - | IA pode sugerir baseado em vagas similares |
| `manager_email` | Interno | `Department.manager_email` | **Auto-preencher** |

**Implementação Sugerida:**
```python
# org_structure_collector - buscar dados do departamento
async def get_department_defaults(department_name: str, company_id: str):
    dept = await department_service.get_by_name(department_name, company_id)
    return {
        "direct_manager": dept.manager_name,
        "manager_email": dept.manager_email,
        "team_size": dept.headcount,
        "location": dept.location
    }
```

---

### 2.4 Requisitos Técnicos (Etapa 5)

| Campo da Vaga | Tipo | Fonte no Admin | Estratégia de Otimização |
|---------------|------|----------------|--------------------------|
| `technical_requirements` | Obrigatório | `IdealProfile.technical_requirements` | **Sugerir** do perfil ideal |
| `required_skills` | Legado | `IdealProfile.mandatory_skills` | **Sugerir** skills obrigatórias |
| `preferred_skills` | Opcional | `IdealProfile.preferred_skills` | **Sugerir** skills desejáveis |

**Implementação Sugerida:**
- Ao coletar `job_title` + `seniority`, buscar `IdealProfile` correspondente
- Pré-preencher matriz técnica com `technical_requirements` do perfil

---

### 2.5 Estratégia de Sourcing (Etapa 6)

| Campo da Vaga | Tipo | Fonte no Admin | Estratégia de Otimização |
|---------------|------|----------------|--------------------------|
| `target_sector` | Opcional | `CompanyProfile.sector` | **Default**: setor da empresa |
| `target_segments` | Opcional | `CompanyProfile.industry` | **Sugerir** indústria |
| `target_companies` | Opcional | - | IA sugere baseado em vagas anteriores |
| `excluded_companies` | Opcional | - | Carregar lista fixa por empresa |

---

### 2.6 Competências WSI/Comportamentais (Etapa 7)

| Campo da Vaga | Tipo | Fonte no Admin | Estratégia de Otimização |
|---------------|------|----------------|--------------------------|
| `wsi_competencies` | Auto-gerado | `IdealProfile.behavioral_requirements` | **Combinar** com perfil ideal |
| `behavioral_competencies` | Opcional | `CultureValue.behavioral_indicators` | **Incluir** indicadores culturais |

**Melhoria Sugerida:**
```python
# wsi_competencies_collector - combinar fontes
async def suggest_competencies(job_title, seniority, company_id):
    # 1. Buscar competências do perfil ideal
    ideal = await ideal_profile_service.get_by_role(job_title, seniority)
    
    # 2. Buscar valores culturais da empresa
    culture = await culture_value_service.get_active(company_id)
    
    # 3. Combinar competências técnicas + comportamentais + culturais
    return merge_competencies(
        ideal.behavioral_requirements,
        [cv.behavioral_indicators for cv in culture]
    )
```

---

### 2.7 Etapas de Entrevistas (Etapa 8)

| Campo da Vaga | Tipo | Fonte no Admin | Estratégia de Otimização |
|---------------|------|----------------|--------------------------|
| `interview_stages` | Obrigatório | `RecruitmentTemplate.stages_config` | **Carregar** template por tipo de vaga |
| `screening_questions` | Auto-gerado | `CultureValue.interview_questions` | **Incluir** perguntas culturais |

**Fluxo Otimizado:**
1. Perguntar: "Qual o tipo desta vaga?" (Technical, Executive, Operational, etc.)
2. Carregar `RecruitmentTemplate` correspondente
3. Pré-preencher `interview_stages` com `stages_config`
4. Adicionar perguntas de screening dos `CultureValue.interview_questions`

---

### 2.8 Timeline/Cronograma (Etapa 9)

| Campo da Vaga | Tipo | Fonte no Admin | Estratégia de Otimização |
|---------------|------|----------------|--------------------------|
| `timeline.total_weeks` | Calculado | `RecruitmentTemplate.default_sla_days` | **Calcular** baseado no SLA do template |
| `weekly_breakdown` | Calculado | `RecruitmentSLA` | **Usar** SLAs por etapa |

**Implementação:**
```python
# Calcular timeline baseado no template selecionado
def calculate_timeline_from_template(template: RecruitmentTemplate):
    total_days = template.default_sla_days
    total_weeks = ceil(total_days / 7)
    
    # Buscar SLAs específicas
    slas = get_slas_for_stages(template.stages_config)
    
    return Timeline(
        total_weeks=total_weeks,
        weekly_breakdown=generate_breakdown(slas)
    )
```

---

### 2.9 Governança LIA (Etapa 10)

| Campo da Vaga | Tipo | Fonte no Admin | Estratégia de Otimização |
|---------------|------|----------------|--------------------------|
| `auto_schedule_interviews` | Opcional | `RecruitmentTemplate.ai_config` | **Usar** config do template |
| `auto_send_negative_feedback` | Opcional | `RecruitmentAutomation` | **Verificar** se automação existe |
| `requires_validation_before_shortlist` | Opcional | Default da empresa | **Configuração global** |

---

### 2.10 Templates de Comunicação (Etapa 11)

| Campo da Vaga | Tipo | Fonte no Admin | Estratégia de Otimização |
|---------------|------|----------------|--------------------------|
| `whatsapp_template_type` | Auto-selecionado | - | **Já implementado** baseado em `is_confidential` |
| `communication_templates` | Opcional | `NotificationPolicy` | Carregar templates ativos |

---

### 2.11 Aprovação e Publicação (Etapa 13)

| Campo da Vaga | Tipo | Fonte no Admin | Estratégia de Otimização |
|---------------|------|----------------|--------------------------|
| `approval_status` | Workflow | `Approver` | **Carregar** aprovadores por nível |
| `approval_requested_by` | Auto | Usuário logado | - |

---

## 3. Proposta de Implementação

### 3.1 Novo Serviço: `AdminDataPrefillService`

```python
# lia-agent-system/app/services/admin_prefill_service.py

class AdminDataPrefillService:
    """Serviço para pré-preencher dados de vaga usando configurações do Admin."""
    
    async def get_prefill_data(
        self, 
        company_id: str,
        job_title: Optional[str] = None,
        department: Optional[str] = None,
        seniority: Optional[str] = None,
        template_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retorna dados pré-preenchidos baseado nos parâmetros.
        """
        prefill = {}
        
        # 1. Dados do Departamento
        if department:
            dept = await self._get_department(company_id, department)
            if dept:
                prefill["location"] = dept.location
                prefill["manager_name"] = dept.manager_name
                prefill["manager_email"] = dept.manager_email
                prefill["team_size"] = dept.headcount
        
        # 2. Perfil Ideal
        if job_title and seniority:
            ideal = await self._get_ideal_profile(company_id, job_title, seniority)
            if ideal:
                prefill["salary_range"] = {
                    "min": ideal.salary_range_min,
                    "max": ideal.salary_range_max
                }
                prefill["technical_requirements"] = ideal.technical_requirements
                prefill["behavioral_requirements"] = ideal.behavioral_requirements
        
        # 3. Template de Recrutamento
        if template_type:
            template = await self._get_template(company_id, template_type)
            if template:
                prefill["interview_stages"] = template.stages_config
                prefill["default_sla_days"] = template.default_sla_days
                prefill["ai_config"] = template.ai_config
        
        # 4. Valores Culturais
        culture = await self._get_culture_values(company_id)
        if culture:
            prefill["behavioral_competencies"] = [
                cv.behavioral_indicators for cv in culture
            ]
        
        # 5. Benefícios (já implementado)
        
        return prefill
```

### 3.2 Integração no Workflow

Modificar `job_vacancy_nodes.py` para usar o novo serviço:

```python
# No início do workflow, carregar dados de prefill
async def job_state_loader(state: Dict[str, Any]) -> Dict[str, Any]:
    """Load or initialize JobVacancyState with prefill data."""
    company_id = state.get("company_id", "default")
    
    # Buscar dados de prefill do Admin
    prefill_data = await admin_prefill_service.get_prefill_data(company_id)
    
    # Armazenar para uso nos coletores
    state["workflow_data"]["admin_prefill"] = prefill_data
    
    return state
```

---

## 4. Fluxo Otimizado Proposto

### Antes (13 etapas com muitas perguntas)
```
1. Onboarding → 2. Título/Senioridade → 3. Salário → 4. Gestor → 5. Requisitos →
6. Sourcing → 7. WSI → 8. Entrevistas → 9. Timeline → 10. Governança →
11. Comunicação → 12. Job Description → 13. Publicação
```

### Depois (Fluxo Inteligente)
```
1. Onboarding (mostra dados da empresa já configurados)
2. Título + Senioridade + Departamento (dropdown)
   → Auto-preenche: location, manager, team_size, salary_range
3. Confirmar Remuneração (mostra sugestão + benefícios)
4. Confirmar Requisitos (mostra perfil ideal + matriz técnica)
5. Tipo de Processo (dropdown: Technical, Executive, etc.)
   → Auto-carrega: interview_stages, SLAs, timeline, governance
6. Revisar Job Description (gerado automaticamente)
7. Publicar
```

**Redução: 13 etapas → 7 etapas (~46% menos interações)**

---

## 5. Benefícios Esperados

| Métrica | Antes | Depois | Melhoria |
|---------|-------|--------|----------|
| Tempo médio de criação | ~15 min | ~5 min | **67%** |
| Perguntas feitas | ~20 | ~7 | **65%** |
| Campos preenchidos manualmente | ~18 | ~5 | **72%** |
| Consistência com padrões da empresa | Variável | **100%** | - |

---

## 6. Próximos Passos

### Fase 1: Infraestrutura (Sprint 1)
- [ ] Criar `AdminDataPrefillService`
- [ ] Expor endpoint `/api/v1/admin/prefill/{company_id}`
- [ ] Testes unitários

### Fase 2: Integração no Workflow (Sprint 2)
- [ ] Modificar `job_state_loader` para carregar prefill
- [ ] Modificar coletores para usar dados pré-carregados
- [ ] Adicionar lógica de sugestão vs. obrigatoriedade

### Fase 3: UX no Chat (Sprint 3)
- [ ] Frames de confirmação em vez de coleta
- [ ] "Editar" em vez de "Preencher"
- [ ] Progress bar com campos já preenchidos

### Fase 4: Analytics (Sprint 4)
- [ ] Métricas de tempo de criação
- [ ] Taxa de aceitação de sugestões
- [ ] Campos mais editados

---

## 7. Considerações Técnicas

### 7.1 Campos que Precisam Input Manual
Estes campos são únicos por vaga e não podem ser pré-preenchidos:
- `job_title` - Título específico da vaga
- `is_confidential` - Decisão por vaga
- `target_companies` - Específico da busca
- `job_description` - Gerado pela IA, mas precisa aprovação

### 7.2 Fallbacks
Se dados do Admin não existirem:
- Departamentos: Permitir digitação livre
- Perfil Ideal: Usar padrões genéricos
- Templates: Usar "Processo Técnico" como default

### 7.3 Multi-tenancy
- Todos os dados são filtrados por `company_id`
- Cache por empresa para performance
- Invalidar cache ao modificar Admin

---

## Conclusão

A integração entre o processo de criação de vaga e as configurações do Admin pode **reduzir em até 70% o esforço do recrutador**, transformando um processo de coleta de dados em um processo de **confirmação e ajuste fino**.

O investimento principal está na criação do `AdminDataPrefillService` e na modificação dos coletores do workflow para usar dados pré-carregados.
