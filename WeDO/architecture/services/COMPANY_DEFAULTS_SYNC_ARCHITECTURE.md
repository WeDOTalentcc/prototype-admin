# Company Defaults Sync - Arquitetura de Pré-Preenchimento Inteligente

> **Funcionalidade:** Sincronização inteligente entre configurações da empresa e criação de vagas  
> **Versão:** 1.0 | **Data:** 22 Janeiro 2026  
> **Objetivo:** Reduzir trabalho manual e garantir consistência com políticas da empresa

---

## 1. VISÃO GERAL

### 1.1 Problema Atual
Atualmente, o recrutador precisa:
1. Digitar todos os detalhes da vaga na Etapa 1 do Wizard
2. Revisar e ajustar manualmente nas etapas 2-8
3. Não há validação contra as políticas/padrões da empresa

### 1.2 Solução Proposta
Implementar uma camada de inteligência que:
1. **Carrega defaults da empresa** ao abrir o Wizard
2. **Cruza informações** digitadas com configurações
3. **Alerta divergências** entre o solicitado e o padrão
4. **Auto-preenche campos** com valores da empresa
5. **Informa transparentemente** o que foi auto-preenchido

---

## 2. DADOS DISPONÍVEIS EM CONFIGURAÇÕES

### 2.1 Mapeamento de Fontes

| Fonte | Tabela | Campos Úteis para Wizard |
|-------|--------|--------------------------|
| **Perfil da Empresa** | `company_profiles` | `headquarters_city`, `headquarters_state`, `industry`, `sector` |
| **Cultura Organizacional** | `company_culture_profiles` | `work_model`, `core_competencies`, `values`, `default_languages` |
| **Benefícios** | `company_benefits` | Lista de benefícios ativos |
| **Perguntas de Triagem** | `company_screening_questions` | Perguntas padrão |
| **Departamentos** | `departments` | Estrutura organizacional, gestores |
| **Pipeline Template** | `pipeline_templates` | Estágios padrão do processo |

### 2.2 Campos Auto-Preenchíveis

```yaml
etapa_2_informacoes_basicas:
  - location: company_profiles.headquarters_city + headquarters_state
  - work_model: company_culture_profiles.work_model
  - department: departments[].name (dropdown)
  - manager: departments[].manager_name (dropdown)

etapa_3_requisitos_tecnicos:
  - languages: company_culture_profiles.default_languages
  - tech_stack: company_culture_profiles.tech_stack (sugestões)

etapa_4_competencias:
  - behavioral_competencies: company_culture_profiles.core_competencies
  - values_fit: company_culture_profiles.values

etapa_5_beneficios:
  - benefits: company_benefits[] (lista ativa)

etapa_6_triagem:
  - screening_questions: company_screening_questions[] (perguntas padrão)

etapa_7_entrevistas:
  - interview_stages: pipeline_templates[].stages (template padrão)
```

---

## 3. FLUXO DE FUNCIONAMENTO

### 3.1 Opção A: Feedback Pós-Entrada (Recomendada)

```
┌─────────────────────────────────────────────────────────────────────┐
│                           ETAPA 1                                    │
│   Recrutador digita descrição → LIA detecta critérios               │
│                                                                      │
│   "Preciso de Dev Backend Sênior, CLT, remoto, Python..."           │
│                         ▼                                           │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │  🤖 LIA ANALISA:                                         │       │
│   │                                                          │       │
│   │  1. Carrega company_defaults                             │       │
│   │  2. Cruza com critérios detectados                       │       │
│   │  3. Identifica alinhamentos e divergências               │       │
│   └─────────────────────────────────────────────────────────┘       │
│                         ▼                                           │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │  💬 FEEDBACK LIA:                                        │       │
│   │                                                          │       │
│   │  "Analisei sua descrição e cruzei com as configurações   │       │
│   │   da empresa:                                            │       │
│   │                                                          │       │
│   │  ✅ Alinhados:                                           │       │
│   │  • Modelo Remoto (padrão da empresa)                     │       │
│   │  • CLT (tipo de contrato padrão)                         │       │
│   │  • Python (stack da empresa)                             │       │
│   │                                                          │       │
│   │  ⚠️ Divergências:                                        │       │
│   │  • Você informou "São Paulo" mas o padrão é "Rio"        │       │
│   │  • Não foi informado inglês (requisito padrão da empresa)│       │
│   │                                                          │       │
│   │  📋 Auto-preenchido:                                     │       │
│   │  • 8 benefícios da empresa                               │       │
│   │  • 4 competências comportamentais padrão                 │       │
│   │  • 3 perguntas de triagem padrão                         │       │
│   │                                                          │       │
│   │  Deseja manter os valores informados ou ajustar?"        │       │
│   └─────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Opção B: Pré-Preenchimento ao Abrir

```
┌─────────────────────────────────────────────────────────────────────┐
│                      ABERTURA DO WIZARD                             │
│                                                                      │
│   ┌─────────────────────────────────────────────────────────┐       │
│   │  🤖 LIA INFORMA:                                         │       │
│   │                                                          │       │
│   │  "Olá! Já pré-carreguei as configurações padrão da       │       │
│   │   empresa para agilizar a criação:                       │       │
│   │                                                          │       │
│   │  📋 Campos já preenchidos:                               │       │
│   │  • Modelo de trabalho: Híbrido                          │       │
│   │  • Localização: São Paulo - SP                          │       │
│   │  • Tipo de contrato: CLT                                │       │
│   │  • 12 benefícios padrão                                 │       │
│   │  • 5 competências comportamentais                       │       │
│   │  • Inglês intermediário (requisito padrão)              │       │
│   │                                                          │       │
│   │  ✏️ Você só precisa informar:                            │       │
│   │  • Título da vaga                                        │       │
│   │  • Departamento/Gestor                                   │       │
│   │  • Requisitos técnicos específicos                       │       │
│   │  • Faixa salarial                                        │       │
│   │                                                          │       │
│   │  Concorda com as configurações padrão?"                  │       │
│   └─────────────────────────────────────────────────────────┘       │
│                         ▼                                           │
│            [Sim, continuar] [Personalizar]                          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. ARQUITETURA TÉCNICA

### 4.1 Novo Service: CompanyDefaultsService

**Arquivo:** `lia-agent-system/app/services/company_defaults_service.py`

```python
class CompanyDefaultsService:
    """
    Service para carregar e sincronizar defaults da empresa
    com o wizard de criação de vagas.
    """
    
    async def load_company_defaults(
        self, 
        company_id: str
    ) -> CompanyDefaults:
        """
        Carrega todos os defaults configurados para a empresa.
        
        Returns:
            CompanyDefaults com:
            - work_model: str (Híbrido, Remoto, Presencial)
            - contract_types: List[str] (CLT, PJ)
            - default_location: Location (city, state, country)
            - benefits: List[Benefit]
            - behavioral_competencies: List[str]
            - default_languages: List[Language]
            - screening_questions: List[ScreeningQuestion]
            - pipeline_template: PipelineTemplate
            - culture_values: List[str]
            - tech_stack: List[str] (se tech company)
        """
        pass
    
    async def compare_with_input(
        self,
        company_id: str,
        detected_criteria: Dict
    ) -> ComparisonResult:
        """
        Compara critérios detectados com defaults da empresa.
        
        Returns:
            ComparisonResult com:
            - aligned: List[AlignedField] (campos alinhados)
            - divergent: List[DivergentField] (campos divergentes)
            - missing: List[MissingField] (campos não informados)
            - auto_filled: List[AutoFilledField] (campos preenchidos)
        """
        pass
    
    async def generate_feedback_message(
        self,
        comparison: ComparisonResult,
        language: str = "pt-BR"
    ) -> str:
        """
        Gera mensagem de feedback para o recrutador.
        """
        pass
    
    async def get_prefill_data(
        self,
        company_id: str
    ) -> PrefillData:
        """
        Retorna dados para pré-preenchimento do wizard.
        
        Returns:
            PrefillData com valores prontos para cada etapa.
        """
        pass
```

### 4.2 Estrutura de Dados

```python
@dataclass
class CompanyDefaults:
    """Defaults carregados das configurações da empresa."""
    work_model: Optional[str] = None
    contract_types: List[str] = field(default_factory=list)
    default_location: Optional[Location] = None
    benefits: List[Benefit] = field(default_factory=list)
    behavioral_competencies: List[str] = field(default_factory=list)
    default_languages: List[Language] = field(default_factory=list)
    screening_questions: List[ScreeningQuestion] = field(default_factory=list)
    pipeline_template: Optional[PipelineTemplate] = None
    culture_values: List[str] = field(default_factory=list)
    tech_stack: List[str] = field(default_factory=list)
    
@dataclass
class ComparisonResult:
    """Resultado da comparação entre input e defaults."""
    aligned: List[AlignedField]
    divergent: List[DivergentField]
    missing: List[MissingField]
    auto_filled: List[AutoFilledField]
    summary: Dict[str, int]  # counts

@dataclass
class DivergentField:
    """Campo com divergência entre input e default."""
    field_name: str
    field_label: str
    input_value: Any
    default_value: Any
    severity: str  # info, warning, critical
    recommendation: str

@dataclass 
class AutoFilledField:
    """Campo auto-preenchido com valor padrão."""
    field_name: str
    field_label: str
    value: Any
    source: str  # Origem (benefits, culture, etc)
    can_override: bool
```

### 4.3 Integração com JobIntakeAgent

**Arquivo:** `lia-agent-system/app/agents/job_intake_agent.py`

```python
class JobIntakeAgent:
    def __init__(self):
        self.company_defaults_service = CompanyDefaultsService()
    
    async def process_step_1(
        self,
        company_id: str,
        user_input: str
    ) -> JobIntakeResponse:
        """
        Processa Etapa 1 com comparação de defaults.
        """
        # 1. Detectar critérios do input
        detected = await self.detect_criteria(user_input)
        
        # 2. Carregar defaults da empresa
        defaults = await self.company_defaults_service.load_company_defaults(
            company_id
        )
        
        # 3. Comparar e gerar feedback
        comparison = await self.company_defaults_service.compare_with_input(
            company_id,
            detected
        )
        
        # 4. Gerar mensagem de feedback
        feedback_message = await self.company_defaults_service.generate_feedback_message(
            comparison
        )
        
        # 5. Preparar prefill data para próximas etapas
        prefill = await self.company_defaults_service.get_prefill_data(
            company_id
        )
        
        return JobIntakeResponse(
            detected_criteria=detected,
            comparison=comparison,
            feedback_message=feedback_message,
            prefill_data=prefill
        )
```

---

## 5. INTERFACE DO USUÁRIO

### 5.1 Componente de Feedback (React)

```typescript
interface CompanyDefaultsFeedback {
  aligned: Array<{
    field: string;
    label: string;
    value: string;
  }>;
  divergent: Array<{
    field: string;
    label: string;
    inputValue: string;
    defaultValue: string;
    severity: 'info' | 'warning' | 'critical';
  }>;
  autoFilled: Array<{
    field: string;
    label: string;
    value: string;
    source: string;
  }>;
}

// Exemplo de uso no Wizard
<CompanyDefaultsPanel 
  feedback={liaFeedback}
  onAcceptDefaults={() => applyDefaults()}
  onKeepInput={() => keepUserInput()}
  onCustomize={() => openCustomizeModal()}
/>
```

### 5.2 Visual do Painel

```
┌─────────────────────────────────────────────────────────┐
│  🏢 Configurações da Empresa                             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ✅ ALINHADOS (4)                                        │
│  ├─ Modelo de Trabalho: Remoto                          │
│  ├─ Tipo de Contrato: CLT                               │
│  ├─ Stack: Python, FastAPI                              │
│  └─ Inglês: Requisito padrão                            │
│                                                          │
│  ⚠️ DIVERGÊNCIAS (1)                                     │
│  └─ Localização                                          │
│     Informado: São Paulo                                 │
│     Padrão: Rio de Janeiro                               │
│     [Manter SP] [Usar padrão]                            │
│                                                          │
│  📋 AUTO-PREENCHIDO (3)                                  │
│  ├─ 12 benefícios da empresa                            │
│  ├─ 5 competências comportamentais                      │
│  └─ 4 perguntas de triagem padrão                       │
│                                                          │
│  [Ver detalhes] [Aceitar tudo]                          │
└─────────────────────────────────────────────────────────┘
```

---

## 6. REGRAS DE NEGÓCIO

### 6.1 Hierarquia de Valores

```
1. Input explícito do recrutador → SEMPRE PREVALECE
2. Defaults da empresa → Preenche campos vazios
3. Sugestões da LIA → Oferecidas mas não aplicadas automaticamente
```

### 6.2 Campos Obrigatórios vs Opcionais

| Campo | Pode Auto-Preencher? | Pode Divergir do Padrão? |
|-------|---------------------|--------------------------|
| Título da vaga | ❌ Não | N/A |
| Departamento | ✅ Sim (dropdown) | ✅ Sim |
| Gestor | ✅ Sim (dropdown) | ✅ Sim |
| Modelo de trabalho | ✅ Sim | ⚠️ Alertar |
| Tipo de contrato | ✅ Sim | ⚠️ Alertar |
| Localização | ✅ Sim | ✅ Sim |
| Benefícios | ✅ Sim (todos) | ✅ Sim (pode remover) |
| Competências | ✅ Sim | ✅ Sim (pode adicionar) |
| Idiomas | ✅ Sim | ⚠️ Alertar se remover padrão |
| Perguntas triagem | ✅ Sim | ✅ Sim (pode customizar) |

### 6.3 Severidade de Divergências

| Severidade | Quando Aplicar | Ação |
|------------|----------------|------|
| **Critical** | Tipo de contrato não permitido | Bloquear avanço |
| **Warning** | Localização diferente do padrão | Alertar, permitir |
| **Info** | Benefício adicional não padrão | Apenas informar |

---

## 7. CARDS JIRA RELACIONADOS

### 7.1 Backend (IA)

| ID | Título | Prioridade |
|----|--------|------------|
| **NEW-001** | [BACK-IA] CompanyDefaultsService - Carregar defaults da empresa | Alta |
| **NEW-002** | [BACK-IA] CompanyDefaultsService - Comparar input com defaults | Alta |
| **NEW-003** | [BACK-IA] Integrar defaults sync no JobIntakeAgent | Alta |
| **NEW-004** | [BACK-IA] Gerar mensagem de feedback para divergências | Média |

### 7.2 Frontend

| ID | Título | Prioridade |
|----|--------|------------|
| **NEW-005** | [FRONT] Componente CompanyDefaultsPanel no Wizard | Alta |
| **NEW-006** | [FRONT] Modal de detalhes de campos auto-preenchidos | Média |
| **NEW-007** | [FRONT] Indicadores visuais de alinhamento/divergência | Média |

### 7.3 API

| ID | Título | Prioridade |
|----|--------|------------|
| **NEW-008** | [API] GET /api/v1/companies/{id}/defaults | Alta |
| **NEW-009** | [API] POST /api/v1/jobs/wizard/compare-defaults | Alta |

---

## 8. ARQUIVOS RELACIONADOS

| Arquivo | Propósito |
|---------|-----------|
| `lia-agent-system/app/services/company_defaults_service.py` | **CRIAR** - Service principal |
| `lia-agent-system/app/agents/job_intake_agent.py` | **MODIFICAR** - Integrar defaults |
| `lia-agent-system/app/models/company.py` | Dados da empresa |
| `lia-agent-system/app/models/company_culture.py` | Cultura e competências |
| `lia-agent-system/app/models/company_benefit.py` | Benefícios padrão |
| `lia-agent-system/app/models/screening_question.py` | Perguntas de triagem |
| `plataforma-lia/src/components/job-creation/job-creation-wizard.tsx` | **MODIFICAR** - Adicionar painel |

---

## 9. CRONOGRAMA SUGERIDO

| Fase | Duração | Entregáveis |
|------|---------|-------------|
| **1. Backend Service** | 3 dias | CompanyDefaultsService funcionando |
| **2. Integração Agent** | 2 dias | JobIntakeAgent usando defaults |
| **3. API Endpoints** | 1 dia | Endpoints REST prontos |
| **4. Frontend Painel** | 3 dias | Componente visual no wizard |
| **5. Testes & Ajustes** | 2 dias | Testes E2E, refinamentos |

**Total estimado:** 11 dias

---

## 10. CHANGELOG

| Data | Versão | Alteração |
|------|--------|-----------|
| 22/01/2026 | 1.0 | Criação inicial da arquitetura |
