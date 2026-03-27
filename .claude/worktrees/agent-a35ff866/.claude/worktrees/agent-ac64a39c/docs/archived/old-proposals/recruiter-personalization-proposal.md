# Personalização por Recrutador

> **Status**: ✅ IMPLEMENTADO  
> **Data de Implementação**: Janeiro 2026  
> **Versão**: 1.0  
> **Documentação Principal**: [job-wizard-enhancement-plan.md](./job-wizard-enhancement-plan.md)

---

## 1. Visão Geral

### 1.1 Objetivo

Personalizar a experiência do wizard para cada recrutador baseado em:
- Suas preferências históricas
- Seu padrão de correções
- Seus tipos de vagas mais comuns
- Seu estilo de interação

### 1.2 Benefícios

| Aspecto | Sem Personalização | Com Personalização |
|---------|-------------------|-------------------|
| Defaults | Iguais para todos | Ajustados por recrutador |
| Confiança | Threshold fixo | Threshold adaptativo |
| Fluxo | Linear padrão | Otimizado por padrão de uso |
| Sugestões | Genéricas | Baseadas em histórico pessoal |
| Linguagem | Padronizada | Adaptada ao estilo |

### 1.3 Status de Implementação

| Componente | Status | Arquivo |
|------------|--------|---------|
| RecruiterProfile Model | ✅ Implementado | `recruiter_profile.py` |
| RecruiterFieldPreference Model | ✅ Implementado | `recruiter_profile.py` |
| PersonalizationSettings Model | ✅ Implementado | `recruiter_profile.py` |
| ProfileCalculationLog Model | ✅ Implementado | `recruiter_profile.py` |
| RecruiterPersonalizationService | ✅ Implementado | `recruiter_personalization_service.py` |
| API Endpoints | ✅ Implementado | `api/v1/recruiter_profiles.py` |
| Integração com Wizard | ✅ Implementado | `job_intake_agent.py` |

---

## 2. Modelo de Personalização

### 2.1 RecruiterProfile

```python
class RecruiterProfile(Base):
    __tablename__ = "recruiter_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recruiter_id = Column(String(255), nullable=False, unique=True)
    company_id = Column(String(255), nullable=False)
    
    # Estatísticas de uso
    total_jobs_created = Column(Integer, default=0)
    total_corrections_made = Column(Integer, default=0)
    avg_completion_time_seconds = Column(Float, nullable=True)
    
    # Preferências detectadas
    preferred_seniorities = Column(JSON, default=list)
    preferred_departments = Column(JSON, default=list)
    correction_patterns = Column(JSON, default=dict)
    
    # Ajustes personalizados
    confidence_threshold_adjustment = Column(Float, default=0.0)
    wizard_mode = Column(String(50), nullable=True)  # "quick", "detailed", "standard"
    experience_level = Column(String(50), nullable=True)
    profile_version = Column(Integer, default=1)
```

### 2.2 RecruiterFieldPreference

```python
class RecruiterFieldPreference(Base):
    __tablename__ = "recruiter_field_preferences"
    
    recruiter_id = Column(String(255), nullable=False)
    field_name = Column(String(100), nullable=False)
    
    correction_count = Column(Integer, default=0)
    total_encounters = Column(Integer, default=0)
    correction_rate = Column(Float, default=0.0)
    
    typical_corrections = Column(JSON, default=list)
    preferred_values = Column(JSON, default=list)
    
    custom_threshold = Column(Float, nullable=True)
    always_ask = Column(Boolean, default=False)
```

### 2.3 PersonalizationSettings

```python
class PersonalizationSettings(Base):
    __tablename__ = "personalization_settings"
    
    recruiter_id = Column(String(255), nullable=False, unique=True)
    
    # Opt-in/out
    enable_personalization = Column(Boolean, default=True)
    use_correction_history = Column(Boolean, default=True)
    use_preference_detection = Column(Boolean, default=True)
    use_outcome_data = Column(Boolean, default=True)
    
    # Transparência
    show_confidence_indicators = Column(Boolean, default=True)
    explain_suggestions = Column(Boolean, default=True)
    
    # Auto-aprovação
    auto_approve_high_confidence = Column(Boolean, default=True)
    high_confidence_threshold = Column(Float, default=0.90)
```

---

## 3. API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/recruiter-profiles/me` | GET | Perfil do recrutador atual |
| `/api/v1/recruiter-profiles/me/settings` | GET | Configurações de personalização |
| `/api/v1/recruiter-profiles/me/field-preferences` | GET | Preferências por campo |
| `/api/v1/recruiter-profiles/me/thresholds` | GET | Thresholds personalizados |
| `/api/v1/recruiter-profiles/me/events` | POST | Registrar evento |
| `/api/v1/recruiter-profiles/me/recalculate` | POST | Forçar recálculo |

---

## 4. Casos de Uso

### Recrutador de Tech (Maria)
```
Perfil detectado:
- Cria principalmente vagas de Dev Sênior
- Sempre aumenta salário sugerido em ~15%
- Pula explicações detalhadas
- wizard_mode: "quick"

Comportamento:
LIA: "Dev Python Sênior para Engenharia. 
     Salário: R$ 20.000 - R$ 26.000 (ajustado ao seu padrão).
     [Próximo →]"
```

### Recrutador Novo (João)
```
Perfil detectado:
- 3 vagas criadas (dados insuficientes)
- experience_level: "beginner"

Comportamento:
LIA: "Entendi que você precisa de um Desenvolvedor Python Sênior!
     Vou preencher automaticamente:
     • Salário: R$ 18.000 - R$ 22.000 (benchmark interno)
     • Skills sugeridas: Python, SQL, REST APIs
     Quer me contar mais sobre a vaga?"
```

### Recrutador Executivo (Carla)
```
Perfil detectado:
- Cria vagas de gestão/diretoria
- wizard_mode: "detailed"
- Faz muitas correções em competências

Comportamento:
LIA: "Prezada Carla,
     Para Diretor de Tecnologia, preparei:
     
     Remuneração: R$ 45.000 - R$ 65.000
     
     Competências (gostaria de sua validação):
     - Visão Estratégica (Essencial)
     - Gestão de P&L (Essencial)
     
     Poderia confirmar?"
```

---

## 5. Fluxo de Aprendizado

```
┌────────────────────────────────────────────────────────────┐
│                   CICLO DE APRENDIZADO                      │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐ │
│  │Interação│───▶│ Registro│───▶│ Análise │───▶│Atualiza │ │
│  │ Wizard  │    │  Evento │    │ Padrão  │    │ Perfil  │ │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘ │
│       │                                             │       │
│       └─────────────────────────────────────────────┘       │
│                                                             │
│  EVENTOS REGISTRADOS:                                       │
│  • field_suggested: campo X sugerido com valor Y           │
│  • field_accepted: sugestão aceita sem alteração           │
│  • field_corrected: valor alterado de Y para Z             │
│  • step_skipped: recrutador pulou etapa opcional           │
│  • explanation_dismissed: fechou explicação rápido         │
│  • jd_imported: usou importação de JD                      │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

---

## 6. Requisitos de Dados

| Requisito | Volume Mínimo |
|-----------|---------------|
| Vagas por recrutador | 10+ |
| Feedbacks registrados | 20+ |
| Meses de atividade | 1+ |

---

## 7. Arquivos de Implementação

| Arquivo | Descrição |
|---------|-----------|
| `app/models/recruiter_profile.py` | Modelos de dados |
| `app/services/recruiter_personalization_service.py` | Serviço principal |
| `app/api/v1/recruiter_profiles.py` | API endpoints |
| `app/agents/specialized/job_intake_agent.py` | Integração com wizard |
| `app/models/feedback_learning.py` | WizardFeedback para aprendizado |

---

## 8. Privacidade e Transparência

- Usuários podem desativar personalização via `PersonalizationSettings`
- Indicadores visuais mostram quando sugestões são personalizadas
- Dados são retidos por período configurável (default: 24 meses)
- Conformidade com LGPD

---

## 9. Métricas de Sucesso

| Métrica | Baseline | Target |
|---------|----------|--------|
| Taxa de aceitação de sugestões | 65% | 90% |
| Tempo de criação (usuários frequentes) | atual | -40% |
| Correções por vaga | 5.2 | 2.0 |
| Satisfação (NPS) | - | +20 pts |

---

> **Documentação completa**: Ver seção 19 do [job-wizard-enhancement-plan.md](./job-wizard-enhancement-plan.md)
