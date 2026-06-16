# Proposta: Sincronização Inteligente de Configurações

**Status:** Proposta  
**Data:** Janeiro 2026  
**Autor:** Equipe LIA  

---

## Visão Geral

Adicionar uma etapa final no wizard de criação de vagas onde a LIA analisa todas as informações da vaga recém-criada, cruza com os dados armazenados no Menu Configurações (Company Settings), e sugere atualizações para informações novas ou diferentes.

## Objetivo

Transformar o Menu Configurações em uma **fonte da verdade (source of truth)** que se enriquece organicamente com dados reais das vagas, sem risco de sobrescrever ou poluir informações existentes.

---

## Casos de Uso

| Cenário | Exemplo | Ação Sugerida |
|---------|---------|---------------|
| Benefício novo na vaga | "Gympass" mencionado, não está nas configs | Sugerir adicionar à lista de benefícios |
| Modelo de trabalho diferente | Vaga é "Híbrido 3x2", config só tem "Remoto" | Sugerir adicionar nova variante |
| Skill técnica nova | "Kubernetes" usado na vaga, não está no tech_stack | Sugerir adicionar à stack |
| Nova localidade | Vaga em "Campinas, SP", não cadastrada | Sugerir adicionar às localizações |
| Novo departamento | Área "Data Science" não existe | Sugerir criar departamento |

---

## Arquitetura Proposta

### Nova Etapa no Wizard

**Nome:** `config-suggestions`  
**Posição:** Após a etapa "active-search" (Próximos Passos)  
**Fase Visual:** Seleção (última etapa antes de fechar)

### Fluxo do Usuário

```
[...etapas anteriores...] 
    → Próximos Passos 
    → Sugestões de Configuração (NOVA)
    → Fechar Wizard
```

### Lógica de Comparação

```typescript
interface ConfigSuggestion {
  id: string
  type: 'benefit' | 'work_model' | 'tech_skill' | 'location' | 'department'
  value: string
  source: 'job_description' | 'competencies' | 'basic_info' | 'salary'
  reason: string
  selected: boolean
}

// Campos da vaga vs Campos das configurações
const COMPARISON_MAP = {
  'salary.benefits': 'company.benefits',
  'basicInfo.workModel': 'company.work_model', 
  'competencies.technicalSkills': 'company.tech_stack',
  'basicInfo.location': 'company.locations',
  'basicInfo.department': 'company.departments'
}
```

### Algoritmo de Detecção

```typescript
function detectConfigDifferences(jobData: JobData, companyConfig: CompanyConfig): ConfigSuggestion[] {
  const suggestions: ConfigSuggestion[] = []
  
  // 1. Benefícios
  const jobBenefits = extractBenefitsFromJob(jobData)
  const configBenefits = companyConfig.benefits.map(b => b.name.toLowerCase())
  
  jobBenefits.forEach(benefit => {
    if (!configBenefits.includes(benefit.toLowerCase())) {
      suggestions.push({
        id: generateId(),
        type: 'benefit',
        value: benefit,
        source: 'salary',
        reason: `"${benefit}" foi mencionado nesta vaga mas não está na lista de benefícios da empresa`,
        selected: false
      })
    }
  })
  
  // 2. Skills técnicas
  const jobSkills = jobData.competencies.technicalSkills
  const configSkills = companyConfig.tech_stack.map(s => s.toLowerCase())
  
  jobSkills.forEach(skill => {
    if (!configSkills.includes(skill.toLowerCase())) {
      suggestions.push({
        id: generateId(),
        type: 'tech_skill',
        value: skill,
        source: 'competencies',
        reason: `"${skill}" é uma skill técnica desta vaga mas não consta na stack configurada`,
        selected: false
      })
    }
  })
  
  // 3. Modelo de trabalho
  if (jobData.basicInfo.workModel && 
      !companyConfig.work_models.includes(jobData.basicInfo.workModel)) {
    suggestions.push({
      id: generateId(),
      type: 'work_model',
      value: jobData.basicInfo.workModel,
      source: 'basic_info',
      reason: `Modelo "${jobData.basicInfo.workModel}" não está cadastrado nas configurações`,
      selected: false
    })
  }
  
  // 4. Localidade
  if (jobData.basicInfo.location && 
      !companyConfig.locations.includes(jobData.basicInfo.location)) {
    suggestions.push({
      id: generateId(),
      type: 'location',
      value: jobData.basicInfo.location,
      source: 'basic_info',
      reason: `"${jobData.basicInfo.location}" não está na lista de localidades da empresa`,
      selected: false
    })
  }
  
  // 5. Departamento
  if (jobData.basicInfo.department && 
      !companyConfig.departments.find(d => d.name === jobData.basicInfo.department)) {
    suggestions.push({
      id: generateId(),
      type: 'department',
      value: jobData.basicInfo.department,
      source: 'basic_info',
      reason: `Área "${jobData.basicInfo.department}" não existe nos departamentos cadastrados`,
      selected: false
    })
  }
  
  return suggestions
}
```

---

## Regras de Segurança

### Princípios Fundamentais

1. **Nunca Sobrescrever**
   - Operações são exclusivamente de APPEND (adicionar ao final)
   - Dados existentes são intocáveis

2. **Nunca Deletar**
   - Não há opção de remover dados via esta funcionalidade
   - Remoções só podem ser feitas diretamente no Menu Configurações

3. **Opcional por Item**
   - Cada sugestão tem toggle individual
   - Usuário escolhe quais dados adicionar
   - Pode pular toda a etapa

4. **Rastreabilidade**
   - Log de quem adicionou cada item
   - Data/hora da adição
   - Vaga de origem dos dados

### Estrutura de Auditoria

```typescript
interface ConfigChangeLog {
  id: string
  timestamp: Date
  userId: string
  userName: string
  action: 'add'
  configType: 'benefit' | 'work_model' | 'tech_skill' | 'location' | 'department'
  value: string
  sourceJobId: string
  sourceJobTitle: string
}
```

---

## UI/UX Proposta

### Layout da Etapa

```
┌─────────────────────────────────────────────────────┐
│ 💡 Sugestões de Atualização                         │
│                                                     │
│ Encontrei informações nesta vaga que podem          │
│ enriquecer suas configurações da empresa:           │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ [Toggle] Novo Benefício                         │ │
│ │          "Gympass"                              │ │
│ │          ℹ️ Não está na lista de benefícios     │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ [Toggle] Nova Skill Técnica                     │ │
│ │          "Kubernetes"                           │ │
│ │          ℹ️ Não consta na stack configurada     │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ [Toggle] Nova Localidade                        │ │
│ │          "Campinas, SP"                         │ │
│ │          ℹ️ Não está nas localidades cadastradas│ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ┌─────────────────────────────────────────────────┐ │
│ │ ⚠️ Estas alterações apenas ADICIONAM dados.    │ │
│ │ Nenhuma informação existente será modificada.  │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ [Pular]              [Adicionar Selecionados (2)]   │
└─────────────────────────────────────────────────────┘
```

### Estados da Etapa

1. **Com sugestões**: Mostra lista de itens com toggles
2. **Sem sugestões**: Mensagem "Todas as informações já estão atualizadas ✓"
3. **Processando**: Loading enquanto cruza dados
4. **Erro**: Fallback para pular etapa

### Componentes Necessários

```typescript
// Novos componentes a criar
ConfigSuggestionCard.tsx      // Card individual de sugestão
ConfigSuggestionsList.tsx     // Lista de sugestões
ConfigSyncStage.tsx           // Etapa completa do wizard
```

---

## Integração com APIs

### Endpoints Necessários

```typescript
// GET - Buscar configurações da empresa
GET /api/backend-proxy/company/profile
GET /api/backend-proxy/company/departments  
GET /api/backend-proxy/company/benefits

// POST - Adicionar novos dados (endpoints existentes ou novos)
POST /api/backend-proxy/company/benefits
POST /api/backend-proxy/company/locations
POST /api/backend-proxy/company/tech-stack
POST /api/backend-proxy/company/departments
POST /api/backend-proxy/company/work-models

// POST - Log de auditoria
POST /api/backend-proxy/company/config-changelog
```

### Payload de Atualização

```typescript
interface ConfigUpdatePayload {
  type: 'benefit' | 'work_model' | 'tech_skill' | 'location' | 'department'
  value: string
  sourceJobId: string
  sourceJobTitle: string
}
```

---

## Considerações Futuras

### Melhorias Potenciais

1. **Machine Learning**
   - Sugerir categorização automática de benefícios
   - Agrupar skills similares
   - Detectar duplicatas com nomes diferentes

2. **Bulk Sync**
   - Analisar todas as vagas existentes de uma vez
   - Gerar relatório de gaps nas configurações

3. **Validação de Consistência**
   - Alertar quando configurações parecem desatualizadas
   - Sugerir revisão periódica

4. **Permissões Granulares**
   - Definir quem pode adicionar cada tipo de dado
   - Workflow de aprovação para alguns tipos

---

## Dependências

- [ ] Menu Configurações (CompanyTeamHub) funcionando
- [ ] APIs de configuração da empresa
- [ ] Sistema de auditoria/changelog
- [ ] Wizard de criação de vagas completo

---

## Estimativa de Implementação

| Componente | Esforço |
|------------|---------|
| Lógica de comparação | Médio |
| UI da nova etapa | Médio |
| APIs de atualização | Baixo |
| Sistema de auditoria | Baixo |
| Testes | Médio |

**Total estimado:** 2-3 sprints

---

## Referências

- `plataforma-lia/src/components/expanded-chat-modal.tsx` - Wizard atual
- `plataforma-lia/src/components/settings/CompanyTeamHub.tsx` - Menu Configurações
- `docs/WSI_METHODOLOGY_REFERENCE.md` - Metodologia WSI
