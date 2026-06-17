# Sistema de Ranking da LIA

## 📊 Visão Geral

O **Ranking LIA** é um sistema inteligente de priorização de candidatos que combina múltiplos fatores para determinar quais candidatos precisam de atenção imediata do recrutador.

## 🔢 Fórmula do Ranking

```
Ranking LIA = Urgência + Score LIA + Skills Match + Status Triagem + Bônus Etapa - Penalização Tempo
```

### Componentes Detalhados

#### 1. **Urgência** (0 a 3.000 pontos)

| Situação | Pontos | Nível | Emoji |
|----------|--------|-------|-------|
| Aprovação de contato inicial pendente | 3.000 | Crítico | 🔥 |
| Aprovação de entrevista pendente (pós-triagem) | 2.000 | Alto | ⚠️ |
| Outra aprovação pendente | 1.000 | Médio | 📋 |
| Sem pendências urgentes | 0 | - | - |

**Lógica:**
- Candidato identificado pela LIA aguardando aprovação para contato = **3.000 pts**
- Candidato com triagem completa aguardando aprovação para entrevista = **2.000 pts**
- Qualquer outra aprovação pendente = **1.000 pts**

#### 2. **Score LIA** (0 a 500 pontos)

```
Pontos = Score LIA (0-10) × 50
```

**Exemplos:**
- Score 10.0 = 500 pts
- Score 8.5 = 425 pts
- Score 7.0 = 350 pts
- Score 5.0 = 250 pts

**O que é o Score LIA?**
Avaliação geral da LIA sobre o candidato baseada em:
- Compatibilidade técnica
- Experiência relevante
- Soft skills inferidas
- Histórico profissional

#### 3. **Skills Match** (0 a 500 pontos)

```
Pontos = Match % (0-100) × 5
```

**Exemplos:**
- Match 100% = 500 pts
- Match 92% = 460 pts
- Match 85% = 425 pts
- Match 70% = 350 pts

**O que é o Skills Match?**
Percentual de correspondência entre as skills do candidato e os requisitos da vaga.

#### 4. **Status da Triagem** (0 a 200 pontos)

| Status | Condições | Pontos |
|--------|-----------|--------|
| Triagem completa e aprovada | Mobilidade OK + Salário compatível + Interesse alto | 200 |
| Triagem completa com ressalvas | Algum critério não ideal | 100 |
| LIA marcou triagem como completa | Status "triagem_completa" | 200 |
| Em contato inicial | Status "em_contato" | 100 |
| Não iniciada | - | 0 |

#### 5. **Bônus por Etapa Avançada**

| Etapa | Bônus |
|-------|-------|
| Final | +300 pts |
| Entrevista | +150 pts |
| Outras | 0 pts |

**Lógica:** Candidatos em etapas mais avançadas têm prioridade pois já foram validados.

#### 6. **Penalização por Tempo Parado**

```
Penalização = Dias parado × (-10)
```

**Exemplos:**
- 5 dias parado = -50 pts
- 10 dias parado = -100 pts
- 15 dias parado = -150 pts

**Lógica:** Candidatos parados há muito tempo perdem prioridade.

## 📊 Exemplos Práticos

### Exemplo 1: Candidato Crítico (4.075 pts) 🔥

**Maria Santos - Aprovação Urgente**
- Aprovação de contato pendente: **3.000 pts**
- Score LIA 8.7: **435 pts** (8.7 × 50)
- Match 92%: **460 pts** (92 × 5)
- Triagem não iniciada: **0 pts**
- Etapa "Funil": **0 pts**
- Parado 2 dias: **-20 pts** (2 × -10)
- **TOTAL: 3.875 pts** → Nível Crítico 🔥

### Exemplo 2: Candidato Alta Prioridade (2.605 pts) ⚠️

**Ana Costa - Pronta para Entrevista**
- Aprovação de entrevista pendente: **2.000 pts**
- Score LIA 9.1: **455 pts** (9.1 × 50)
- Match 96%: **480 pts** (96 × 5)
- Triagem completa aprovada: **200 pts**
- Etapa "Triagem": **0 pts**
- Parado 3 dias: **-30 pts**
- **TOTAL: 3.105 pts** → Nível Crítico 🔥

### Exemplo 3: Candidato Bom (1.205 pts) ⭐

**Carlos Oliveira - Em Processo**
- Sem aprovações pendentes: **0 pts**
- Score LIA 8.3: **415 pts**
- Match 88%: **440 pts**
- LIA em contato: **100 pts**
- Etapa "Entrevista": **150 pts**
- Parado 5 dias: **-50 pts**
- **TOTAL: 1.055 pts** → Nível Médio 📋

### Exemplo 4: Candidato Normal (885 pts) ✓

**João Silva - Novo**
- Sem aprovações pendentes: **0 pts**
- Score LIA 7.2: **360 pts**
- Match 78%: **390 pts**
- Triagem não iniciada: **0 pts**
- Etapa "Funil": **0 pts**
- Parado 1 dia: **-10 pts**
- **TOTAL: 740 pts** → Nível Normal ✓

## 🎨 Níveis de Urgência Visual

| Ranking | Nível | Emoji | Cor | Significado |
|---------|-------|-------|-----|-------------|
| ≥ 3.000 | Crítico | 🔥 | Vermelho-Laranja | Ação imediata necessária |
| 2.000 - 2.999 | Alto | ⚠️ | Laranja-Amarelo | Alta prioridade |
| 1.000 - 1.999 | Médio | 📋 | Amarelo-Laranja | Atenção necessária |
| 500 - 999 | Bom | ⭐ | Azul | Candidato promissor |
| 300 - 499 | Normal | ✓ | Verde | Em andamento normal |
| < 300 | Baixo | [número] | Cinza | Baixa prioridade |

## 🔔 Sistema de Alertas LIA

### Tipos de Alertas

#### 1. **Aprovar Contato** 🔥 (Urgente - Amarelo)
- **Quando:** Candidato identificado pela LIA aguardando aprovação
- **Ação:** Revisar perfil e aprovar/rejeitar contato inicial
- **Impacto no Ranking:** +3.000 pts

#### 2. **Aprovar Entrevista** ✅ (Urgente - Verde)
- **Quando:** Triagem completa e positiva
- **Ação:** Revisar triagem e aprovar agendamento de entrevista
- **Impacto no Ranking:** +2.000 pts

#### 3. **Parado Xd** ⏰ (Atenção - Roxo)
- **Quando:** Candidato há mais de 7 dias sem movimentação
- **Ação:** Verificar status e tomar ação
- **Impacto no Ranking:** -70 pts ou mais (10 pts/dia)

#### 4. **Enviar Feedback** 📧 (Ação - Vermelho)
- **Quando:** Candidato reprovado sem feedback enviado
- **Ação:** Enviar email de feedback
- **Impacto no Ranking:** Nenhum direto

#### 5. **Pronto p/ Avançar** 🚀 (Info - Azul)
- **Quando:** Triagem OK mas não movido para próxima etapa
- **Ação:** Mover para etapa de Entrevista
- **Impacto no Ranking:** +200 pts (triagem) + potencial +150 pts (etapa)

## 🎯 Como Usar o Ranking

### 1. **Ordenação Default**
A tabela é ordenada automaticamente por Ranking LIA (maior → menor).
Isso significa que **candidatos mais urgentes aparecem primeiro**.

### 2. **Interpretação Rápida**
- **🔥 Crítico (3.000+):** Precisa de ação IMEDIATA
- **⚠️ Alto (2.000-2.999):** Revisar hoje
- **📋 Médio (1.000-1.999):** Revisar esta semana
- **⭐ Bom (500-999):** Acompanhar
- **✓ Normal (300-499):** Em andamento
- **Número (< 300):** Baixa prioridade

### 3. **Ações Sugeridas por Nível**

**Crítico/Alto:**
1. Revisar alertas
2. Tomar ação imediata
3. Aprovar/rejeitar pendências

**Médio/Bom:**
1. Acompanhar progresso
2. Planejar próximos passos
3. Verificar se há gargalos

**Normal/Baixo:**
1. Monitorar periodicamente
2. Aguardar evolução natural
3. Considerar arquivamento se muito antigo

## 💡 Dicas de Uso

1. **Foco nos Críticos:** Sempre comece pelos candidatos com ranking 3.000+
2. **Revise Alertas:** Os alertas indicam exatamente o que fazer
3. **Tempo é Fator:** Quanto mais tempo parado, menor o ranking
4. **Etapas Avançadas:** Candidatos em Final/Entrevista têm bônus automático
5. **Triagem é Chave:** Completar triagem aumenta muito o ranking

## 🔄 Atualização do Ranking

O ranking é recalculado **em tempo real** sempre que:
- Status do candidato muda
- Triagem é completada
- Aprovações são dadas/pendentes
- Dias sem movimentação aumentam
- Score ou Match são atualizados

---

**Última atualização:** Versão 768
**Documentação:** Sistema de Ranking LIA v1.0
