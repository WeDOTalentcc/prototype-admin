# Intelligence Layer para LIA

> **Status**: ✅ IMPLEMENTADO  
> **Data de Implementação**: Janeiro 2026  
> **Versão**: 1.0  
> **Documentação Principal**: [job-wizard-enhancement-plan.md](./job-wizard-enhancement-plan.md)

---

## 1. Visão Geral

### 1.1 O que é a Intelligence Layer?

Uma camada de inteligência centralizada que:
- Detecta padrões em correções, comportamentos e outcomes
- Correlaciona características de vagas com resultados
- Ajusta dinamicamente níveis de confiança
- Fornece sugestões data-driven para o wizard

### 1.2 Status de Implementação

| Componente | Status | Arquivo |
|------------|--------|---------|
| Pattern Detector | ✅ Implementado | `intelligence_layer_service.py` |
| Outcome Correlator | ✅ Implementado | `intelligence_layer_service.py` |
| Confidence Adjuster | ✅ Implementado | `intelligence_layer_service.py` |
| Knowledge Repository | ✅ Implementado | Modelos em `intelligence_layer.py` |
| API Endpoints | ✅ Implementado | `api/v1/intelligence.py` |
| Integração com Wizard | ✅ Implementado | `job_intake_agent.py` |

---

## 2. Arquitetura Implementada

```
┌─────────────────────────────────────────────────────────────┐
│                    INTELLIGENCE LAYER                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Pattern    │  │   Outcome    │  │  Confidence  │       │
│  │   Detector   │  │  Correlator  │  │   Adjuster   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│  ┌─────────────────────────▼─────────────────────────────┐  │
│  │              Knowledge Repository                      │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐      │  │
│  │  │ Padrões │ │ Regras  │ │Histórico│ │Benchmark│      │  │
│  │  │ Sucesso │ │ Ajuste  │ │Correções│ │ Mercado │      │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘      │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  Decision Engine                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/api/v1/intelligence/data-quality` | GET | Avalia qualidade de dados |
| `/api/v1/intelligence/context` | POST | Contexto de inteligência para campo |
| `/api/v1/intelligence/adjust-field` | POST | Ajusta sugestão de campo |
| `/api/v1/intelligence/wizard-enhancements` | GET | Melhorias do wizard |
| `/api/v1/intelligence/success-profile` | GET | Perfil de sucesso |
| `/api/v1/intelligence/correlations` | GET | Correlações de outcomes |

---

## 4. Modelos de Dados

**Arquivo**: `lia-agent-system/app/models/intelligence_layer.py`

- `IntelligenceInsight` - Log de insights gerados
- `PatternCache` - Cache de padrões calculados
- `SuccessProfile` - Perfil de sucesso por tipo de vaga
- `OutcomeCorrelation` - Correlações entre características e outcomes

---

## 5. Requisitos de Dados

| Requisito | Volume Mínimo | Propósito |
|-----------|---------------|-----------|
| Total de vagas | 50+ | Detecção de padrões |
| Outcomes registrados | 30+ | Análise de correlações |
| Meses de dados | 3+ | Insights de correlação temporal |

---

## 6. Arquivos de Implementação

| Arquivo | Descrição |
|---------|-----------|
| `app/services/intelligence_layer_service.py` | Serviço principal |
| `app/models/intelligence_layer.py` | Modelos de dados |
| `app/api/v1/intelligence.py` | API endpoints |
| `app/agents/specialized/job_intake_agent.py` | Integração com wizard |

---

## 7. Próximos Passos

- [ ] Coletar 50+ vagas para ativar detecção de padrões
- [ ] Registrar 30+ contratações para análise de correlações
- [ ] Aguardar 3+ meses para insights de correlação temporal
- [ ] Implementar dashboard de inteligência para visualização

---

> **Documentação completa**: Ver seção 18 do [job-wizard-enhancement-plan.md](./job-wizard-enhancement-plan.md)
