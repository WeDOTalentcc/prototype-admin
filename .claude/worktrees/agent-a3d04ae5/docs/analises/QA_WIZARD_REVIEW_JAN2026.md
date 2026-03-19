# QA Review: Wizard de Criação de Vaga

**Data:** Janeiro 2026  
**Revisor:** LIA QA Agent  
**Arquivo:** `plataforma-lia/src/components/expanded-chat-modal.tsx`  

---

## Resumo Executivo

| Categoria | Status |
|-----------|--------|
| Estrutura do Wizard | ✅ OK |
| Design System | ✅ OK |
| Navegação | ✅ OK |
| Validações | ✅ OK |
| Integração IA | ✅ OK |
| Fluxo de Calibração | ✅ CORRIGIDO |
| Transição Active-Search | ✅ CORRIGIDO |
| Estados Mortos | ✅ REMOVIDOS |

---

## Correções Aplicadas (19 Jan 2026)

### 1. Fluxo de Calibração Corrigido
Quando 3 candidatos são aprovados:
- ~~`setShowCalibrationCompleteModal(true)`~~ (removido)
- ✅ Avança automaticamente para `active-search`
- ✅ Adiciona mensagem de celebração da LIA
- ✅ Inicia busca em background (`setSearchPhase('local-searching')`)

### 2. Estados Mortos Removidos
- ~~`showCalibrationCompleteModal`~~ (removido)
- ~~`showGlobalSearchModal`~~ (removido)

### 3. Funções Órfãs Removidas
- ~~`handlePostCalibrationProcessing`~~ (removido)
- ~~`handleGlobalSearchAuthorize`~~ (removido)
- ~~`handleLocalOnlySearch`~~ (removido)
- ~~`showFinalConfirmationMessage`~~ (removido)

---

## Estrutura do Wizard

### Etapas (9 total)
| # | ID | Título | Fase | Status |
|---|-----|--------|------|--------|
| 1 | description | Descrição | Construção | ✅ |
| 2 | basic-info | Informações | Construção | ✅ |
| 3 | competencies | Competências | Construção | ✅ |
| 4 | salary | Remuneração | Construção | ✅ |
| 5 | wsi-questions | Triagem WSI | Construção | ✅ |
| 6 | review | Revisão e Publicação | Ativação | ✅ |
| 7 | pre-publish | Publicação | Ativação | ✅ |
| 8 | calibration | Calibração | Seleção | ✅ |
| 9 | active-search | Busca Ativa | Seleção | ✅ |

### Fases Visuais (3 total)
- **Construção**: description → wsi-questions (5 etapas)
- **Ativação**: review → pre-publish (2 etapas)
- **Seleção**: calibration → active-search (2 etapas)

---

## Problemas Identificados

### 🔴 CRÍTICO: Estados Mortos Após Remoção de Modais

**Descrição:** Os AlertDialogs "Calibração Concluída" e "Expandir Busca" foram removidos, mas os estados e funções que dependem deles ainda existem.

**Código Afetado:**
```typescript
// Linha 488-489: Estados ainda declarados
const [showCalibrationCompleteModal, setShowCalibrationCompleteModal] = useState(false)
const [showGlobalSearchModal, setShowGlobalSearchModal] = useState(false)

// Linha 1933: Chamada ao modal removido
setShowCalibrationCompleteModal(true)

// Linha 2039-2070: Funções que usam os modais removidos
setShowCalibrationCompleteModal(false)
setShowGlobalSearchModal(true)
```

**Impacto:** Quando o usuário aprova 3 candidatos, nada acontece visualmente. O fluxo fica travado.

**Correção Necessária:**
1. Quando 3 candidatos são aprovados, avançar automaticamente para `active-search`
2. Remover estados mortos: `showCalibrationCompleteModal`, `showGlobalSearchModal`
3. Atualizar função `handleApproveCandidate` para usar a nova lógica

---

### 🟡 MÉDIO: Botão na Etapa Calibration Fecha Wizard Prematuramente

**Descrição:** Quando `calibrationComplete` é true, o botão mostra "Concluir e Ir para Pipeline" e fecha o wizard (`onClose`), pulando a etapa `active-search`.

**Código Afetado:**
```typescript
// Linha 4517-4527
{calibrationComplete ? (
  <Button onClick={onClose}>  // ❌ Fecha o wizard
    Concluir e Ir para Pipeline
  </Button>
```

**Correção Necessária:** Mudar para avançar para `active-search` ao invés de fechar.

---

### 🟡 MÉDIO: Função handlePostCalibrationProcessing Órfã

**Descrição:** A função `handlePostCalibrationProcessing` era chamada pelo modal removido. Agora não é mais chamada.

**Código Afetado:** Linhas 2034-2072

**Correção Necessária:** Integrar esta lógica na transição automática para `active-search`.

---

## Verificações OK

### ✅ Design System
- Cor primária: `#60BED1` (cyan) consistente
- Fonte títulos: `Source Serif 4`
- Fonte corpo: `Open Sans`
- Bordas: `rounded-xl` ou `rounded-lg`
- Estados de foco: `focus:border-[#60BED1]`
- Espaçamentos: Consistentes (p-3, gap-2, space-y-2.5)

### ✅ Validações por Etapa
```typescript
canAdvanceToNextStage(): boolean {
  case 'description': return filledCriteria >= 2
  case 'basic-info': return Boolean(cargo && area)
  case 'competencies': return true
  case 'salary': return true
  case 'wsi-questions': return selectedQuestions >= 1
  case 'review': return true
  default: return true
}
```

### ✅ Integração com IA
- `liaApi.generateJobScreeningQuestions()` - Gera perguntas WSI ✅
- `liaApi.createJobVacancy()` - Cria vaga no backend ✅
- `liaApi.sendMessage()` - Chat com LIA ✅

### ✅ Navegação
- Botão "Voltar" visível a partir da 2ª etapa ✅
- Botão "Avançar" com validação ✅
- Botão "Escolher Plataformas" na etapa review ✅
- Botão "Publicar Vaga" na etapa pre-publish ✅

### ✅ Campos por Etapa

**description:**
- Chat input com anexo de arquivos
- Detecção automática de critérios via IA
- Painel lateral com critérios detectados

**basic-info:**
- Cargo, Área, Gestor
- Localidade, Modelo de Trabalho, Tipo de Contrato
- Ícones indicando dados vindos das configurações

**competencies:**
- Skills técnicas com nível (Básico/Intermediário/Avançado)
- Competências comportamentais com peso (1-5 estrelas)
- Toggle obrigatório/desejável

**salary:**
- Faixa salarial (min/max)
- Bônus anual e critérios
- Lista de benefícios com toggle

**wsi-questions:**
- Perguntas padrão da empresa
- Perguntas geradas por IA (WSI)
- Seleção múltipla

**review:**
- Preview estilo LinkedIn
- Seções expansíveis (Empresa, Vaga, Requisitos)
- Edição inline

**pre-publish:**
- Toggle para plataformas (LinkedIn, Indeed, etc.)
- Contador de plataformas selecionadas

**calibration:**
- Status da busca local
- Prompt para busca global
- Resultados combinados

**active-search:**
- Header de sucesso
- Lista de 8 próximos passos automatizados
- Botão "Ver Candidatos na Tabela"

---

## Recomendações Futuras

1. **Testes E2E:** Adicionar testes automatizados para o fluxo completo do wizard
2. **Estado Persistente:** Salvar progresso do wizard em localStorage para recuperação
3. **Métricas:** Adicionar analytics para tempo gasto em cada etapa
4. **Acessibilidade:** Revisar navegação por teclado e leitores de tela
