# Tabs Preview Vaga - Arquivadas

**Data de arquivamento:** 15 de Janeiro de 2026
**Motivo:** Simplificação do MVP - funcionalidades com dados hardcoded

## Componentes Arquivados

### 1. lia-metrics-tab.tsx
Tab de Métricas LIA que exibia:
- Horas economizadas
- ROI da LIA
- Tempo médio por triagem
- Taxa de conclusão
- Funil de triagem
- Média de notas por critério

### 2. screening-script-tab.tsx
Tab de Roteiro de Triagem que exibia:
- Performance da triagem
- Skills WSI avaliadas
- Blocos WSI do roteiro (6 blocos)
- Configurações de canais
- Agendamento automático

### 3. ../interviews-section.tsx
Seção de notas de entrevistas com dados mock.

## Como Recuperar

1. Copiar os arquivos de volta para suas localizações originais
2. Reimportar nos componentes que os utilizavam
3. Adicionar as tabs de volta no jobs-page.tsx

## Localização Original

- lia-metrics-tab: jobs-page.tsx linhas ~5724-6017
- screening-script-tab: jobs-page.tsx linhas ~6019+
- interviews-section: src/components/interviews-section.tsx
