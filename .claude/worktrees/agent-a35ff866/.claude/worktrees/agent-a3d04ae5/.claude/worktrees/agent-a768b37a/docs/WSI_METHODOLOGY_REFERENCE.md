# Metodologia WSI - WeDoTalent Skill Index

## Referência Técnica para Implementação

**Versão:** 2.0  
**Data:** Janeiro 2026  
**Fonte:** Documentação oficial WeDoTalent  
**Última Atualização:** Adicionado Saturação Inteligente, Governança Humana, Calibração por Empresa

---

## 1. Visão Geral

A metodologia WSI (WeDoTalent Skill Index) é um sistema padronizado para validação técnica, comportamental e cultural em processos de recrutamento digital, utilizando IA generativa e fluxos conversacionais.

### 1.1 Modelos de Aplicação

| Modelo | Nº de Perguntas | Tempo Médio | Uso Ideal | Precisão |
|--------|-----------------|-------------|-----------|----------|
| WSI Compact | 6–8 | 5–7 min | Triagens rápidas, alto volume, vagas operacionais/júnior | ~90% |
| WSI Compact+ | 8–10 | 6:30–9 min | Vagas críticas, tech leads, especializadas, liderança | ~95% |

---

## 2. Fundamentação Teórica

O WSI integra 4 frameworks científicos consolidados:

### 2.1 CBI - Competency-Based Interviewing
- **Base:** McClelland, 1973 - Harvard University
- **Princípio:** "Comportamentos passados são os melhores preditores de performance futura"
- **Aplicação:** Perguntas situacionais, análise STAR (Situation, Task, Action, Result)

### 2.2 Taxonomia de Bloom (Revisada)
- **Base:** Anderson et al., 2001
- **Níveis Cognitivos:**

| Nível | Descrição | Equivalência na Triagem |
|-------|-----------|------------------------|
| 1 - Lembrar | Recordar fatos e conceitos | Autodeclaração simples |
| 2 - Compreender | Explicar ideias | Perguntas teóricas |
| 3 - Aplicar | Usar conhecimento em prática | Microcases |
| 4 - Analisar | Diferenciar e relacionar conceitos | Contexto real |
| 5 - Criar | Gerar soluções novas | Respostas de inovação/liderança |

### 2.3 Modelo Dreyfus
- **Base:** Dreyfus & Dreyfus, 1980
- **Escala 1-5 de Maturidade:**

| Score | Nível | Interpretação |
|-------|-------|---------------|
| 1 | Novice | Conhecimento básico, teórico |
| 2 | Advanced Beginner | Aplicação parcial e guiada |
| 3 | Competent | Execução estável e consistente |
| 4 | Proficient | Aplicação autônoma e adaptativa |
| 5 | Expert | Domínio intuitivo e contextual |

### 2.4 Big Five (OCEAN Model)
- **Base:** Goldberg, 1992

| Fator | Significado | Validação na Triagem |
|-------|-------------|---------------------|
| O - Abertura | Curiosidade, inovação | Inovação e aprendizado |
| C - Conscienciosidade | Organização, foco em resultado | Entregabilidade e rigor técnico |
| E - Extroversão | Energia e assertividade | Comunicação e liderança |
| A - Amabilidade | Empatia e colaboração | Trabalho em equipe |
| N - Estabilidade Emocional | Controle sob pressão | Tomada de decisão e resiliência |

---

## 3. Estrutura Conversacional

### 3.1 Fluxo da Triagem

| Etapa | Objetivo | Exemplo | Duração |
|-------|----------|---------|---------|
| 1. Abertura | Apresentar propósito e tempo | "Leva uns 7 min e no final te mostro seu score técnico." | 0:30 min |
| 2. Validação Técnica | 3–6 perguntas sobre competências técnicas | "De 1 a 5, como avalia seu domínio em Figma?" | 3–4 min |
| 3. Fit Comportamental | 2–4 perguntas situacionais | "Conte uma situação em que precisou resolver um problema em equipe." | 2–3 min |
| 4. Fechamento e Score | Apresenta resultado e próximos passos | "Seu WSI foi 4.1 – nível alto. Envio ao recrutador!" | 0:30 min |

### 3.2 Tipos de Pergunta

| Tipo | Objetivo | Exemplo |
|------|----------|---------|
| Autodeclaração | Quantificar domínio | "De 1 a 5, quanto domina Figma?" |
| Contextual | Validar aplicação real | "Cite um projeto onde aplicou Figma." |
| Microcase | Testar lógica técnica | "O que muda se trocar AND por OR neste SQL?" |
| Situacional | Avaliar comportamento | "Como você reage a feedbacks de design?" |

---

## 4. Tipos de Validação

A LIA escolhe automaticamente o tipo mais adequado para cada competência:

| Tipo de Validação | Critério de Avaliação | Peso Médio | Aplicação |
|-------------------|----------------------|------------|-----------|
| Autodeclaração + Contexto | Domínio técnico e aplicação real | 60% | Padrão para skills técnicas |
| Microcase Prático | Lógica, correção e performance | 20% | Vagas seniores e especializadas |
| Situação Contextual | Profundidade, clareza e postura | 15% | Soft skills e fit cultural |
| Pergunta Teórica Leve | Clareza conceitual e consistência | 5% | Competências analíticas |
| Autodeclaração Simples | Familiaridade e ferramentas citadas | — | Skills periféricas |

---

## 5. Sistema de Cálculo

### 5.1 Fórmula do Score por Skill

```
Score_médio = (0.6 × Autodeclaração) + (0.4 × Contexto)
```

**Componentes:**
- **Autodeclaração (0-5):** Número declarado pelo candidato ou inferido do tom da resposta
- **Contexto (0-5):** Baseado em evidências concretas (STAR), nível Bloom, profundidade técnica

### 5.2 Penalidades

| Situação | Penalidade |
|----------|------------|
| Inflação de score (autodeclara alto, contexto pobre) | -0.5 a -1.5 |
| Resposta genérica | -0.5 |
| Falta de contexto | -0.3 |
| Resposta aparenta ser copiada | -1.0 |

### 5.3 Bônus

| Situação | Bônus |
|----------|-------|
| Humildade (autodeclara baixo, contexto alto) | +0.5 |
| Evidências excepcionais | +0.3 |

### 5.4 Fórmula do WSI Final

```
WSI = Σ(Peso_i × Score_i) / 100
```

**Distribuição de Pesos Recomendada:**
- Competências Técnicas: 70%
- Competências Comportamentais/Culturais: 30%

---

## 6. Classificação e Interpretação

### 6.1 Faixas de WSI

| Faixa | Interpretação | Descrição |
|-------|---------------|-----------|
| 4.5 – 5.0 | Excelente | Especialista |
| 4.0 – 4.4 | Alto | Profissional autônomo |
| 3.0 – 3.9 | Médio | Profissional competente |
| 2.0 – 2.9 | Regular | Iniciante técnico |
| < 2.0 | Baixo | Gap crítico |

---

## 7. Sistema de Aprovação Automática

### 7.1 Corte Inicial (Sem Histórico)

Aplicado quando a vaga tem menos de 30-50 triagens:

| Faixa WSI | Decisão |
|-----------|---------|
| ≥ 4.2 | Aprovado automático |
| 3.8 – 4.1 | Revisão manual |
| 3.0 – 3.7 | Aguardando comparação |
| < 3.0 | Não aprovado |

### 7.2 Corte Dinâmico (Com Histórico)

Após 30-50 triagens por função, o sistema recalibra automaticamente:

| Percentil | Decisão |
|-----------|---------|
| Top 25% | Aprovado automático |
| 25% – 60% | Revisão manual |
| < 60% | Reprovado |

A LIA recalibra automaticamente os percentis a cada nova triagem.

### 7.3 Saturação Inteligente

Lógica de saturação quando número de aprovados atinge limite da vaga.

#### Parâmetros de Saturação

| Parâmetro | Valor Padrão | Descrição |
|-----------|--------------|-----------|
| `saturation_threshold` | 20 | Número máximo de candidatos aprovados antes de pausar |
| `is_saturated` | false/true | Flag que indica se pipeline está saturado |
| `slots_remaining` | threshold - approved | Vagas restantes antes da saturação |

#### Lógica de Decisão

```
SE approved_count >= saturation_threshold:
    is_saturated = TRUE
    recommendation = "pause_screening"
    ALERTAR: "Pipeline saturado! Já temos {n} candidatos aprovados."
SENÃO:
    is_saturated = FALSE
    recommendation = "continue_screening"
    INFORMAR: "{slots_remaining} vagas restantes antes da saturação."
```

#### Ações Automáticas ao Saturar

1. **Pausar triagem automática** - Novas candidaturas entram em fila
2. **Notificar recrutador** - Alerta sobre necessidade de decisão
3. **Sugerir próximos passos:**
   - Ver candidatos aprovados
   - Agendar entrevistas em lote
   - Desbloquear pipeline (override manual)

#### Override Manual

O recrutador pode desbloquear o pipeline a qualquer momento ajustando:
- Aumentar `saturation_threshold` para a vaga específica
- Executar ação "Desbloquear pipeline" no painel

---

## 8. Governança Humana

Regras de revisão manual, controle pelo recrutador, e casos de override.

### 8.1 Princípios de Governança

| Princípio | Descrição |
|-----------|-----------|
| **Humano no Loop** | Toda decisão crítica requer aprovação humana |
| **Transparência** | Candidato sabe que interage com IA |
| **Explicabilidade** | Toda decisão da IA é justificável |
| **Auditabilidade** | Todas as ações são registradas com timestamp |

### 8.2 Limites de Autonomia da LIA

#### O que a LIA PODE fazer automaticamente:

| Ação | Condição |
|------|----------|
| Enviar lembretes de entrevista | Sempre permitido |
| Confirmar agendamentos | Sempre permitido |
| Transcrever entrevistas | Sempre permitido |
| Calcular scores WSI | Sempre permitido |
| Rankear candidatos | Sempre permitido |
| Responder perguntas do recrutador | Sempre permitido |
| Gerar relatórios | Sempre permitido |

#### O que a LIA PRECISA de aprovação humana:

| Ação | Motivo |
|------|--------|
| Enviar primeiro contato a candidato | Impacta imagem da empresa |
| Enviar feedback de rejeição | Comunicação sensível |
| Mover candidato para próxima fase | Decisão crítica do processo |
| Agendar entrevistas com gestor | Envolve calendário de terceiros |
| Enviar proposta/oferta | Compromisso contratual |
| Fechar vaga | Decisão definitiva |
| Comunicações em massa | Risco de erro em escala |

### 8.3 Configuração de Autonomia por Vaga (GovernanceRules)

Durante a criação de cada vaga, o recrutador define:

```python
class GovernanceRules:
    auto_schedule_interviews: bool = False      # Agendar sem aprovação?
    auto_send_negative_feedback: bool = False   # Rejeitar sem aprovação?
    requires_validation_before_shortlist: bool = True  # Aprovar shortlist?
    max_auto_sourcing_per_day: int = 50         # Limite de sourcing automático
    allow_ai_first_contact: bool = False        # IA pode fazer primeiro contato?
```

### 8.4 Override pelo Recrutador

O recrutador pode sobrepor decisões da LIA em qualquer momento:

| Tipo de Override | Registro |
|------------------|----------|
| Aprovar candidato reprovado pela LIA | CalibrationEvent (IMPLICIT_OVERRIDE) |
| Reprovar candidato aprovado pela LIA | CalibrationEvent (score_delta negativo) |
| Ajustar score WSI | Feedback explícito com justificativa |
| Desbloquear pipeline saturado | Ação registrada com timestamp |

### 8.5 Ciclo de Calibração

O sistema aprende com as decisões do recrutador:

1. **Feedback Implícito**: Ações do recrutador (aprovar/reprovar) geram eventos
2. **Feedback Explícito**: Thumbs up/down em sugestões da LIA
3. **Feedback Pós-Contratação**: Sucesso/falha após 90 dias de contratação
4. **Divergências**: Sistema detecta quando LIA e recrutador discordam
5. **Calibração**: Pesos e thresholds são ajustados com base no feedback

```
Tipos de Feedback:
├─ EXPLICIT_AGREE: Recrutador concorda com LIA (+0)
├─ EXPLICIT_DISAGREE: Recrutador discorda da LIA (score_delta)
├─ IMPLICIT_ADVANCE: Avançou candidato mal rankeado (+5)
├─ IMPLICIT_REJECT: Rejeitou candidato bem rankeado (-5)
├─ POST_HIRE_SUCCESS: Contratado com sucesso (+15)
└─ POST_HIRE_FAILURE: Contratado sem sucesso (-15)
```

### 8.6 Políticas Anti-Viés

A LIA **NUNCA** considera em suas decisões:

| Critério Proibido | Exemplos |
|-------------------|----------|
| Idade | Data de nascimento, ano de formatura |
| Gênero | Nome, pronomes, fotos |
| Etnia/Raça | Sobrenome, origem, nacionalidade |
| Estado Civil | Casado, solteiro, filhos |
| Orientação Sexual | Qualquer indicação |
| Religião | Afiliações religiosas |
| Aparência Física | Peso, altura, características |
| Lacunas no Currículo | Períodos sem trabalho não penalizam |

---

## 9. Exemplo Prático de Cálculo

### Scorecard

| Skill | Peso (%) | Tipo de Validação | Score Médio |
|-------|----------|-------------------|-------------|
| Design System | 25% | Microcase | 4.0 |
| Figma | 25% | Autodeclaração + Contexto | 4.5 |
| User Research | 20% | Contextual | 3.8 |
| Cultura: Colaboração | 15% | Situacional | 4.2 |
| Cultura: Inovação | 15% | Situacional | 3.8 |

### Cálculo

| Skill | Peso | Score | Contribuição |
|-------|------|-------|--------------|
| Design System | 25% | 4.0 | 1.00 |
| Figma | 25% | 4.5 | 1.12 |
| User Research | 20% | 3.8 | 0.76 |
| Cultura: Colaboração | 15% | 4.2 | 0.63 |
| Cultura: Inovação | 15% | 3.8 | 0.57 |
| **Total WSI** | 100% | — | **4.08 (Nível Alto)** |

---

## 10. Boas Práticas

1. Defina até **7 competências totais** (5 técnicas + 2 comportamentais)
2. Prefira perguntas curtas e diretas (respostas de até 40 segundos em áudio)
3. O sistema aplica **penalização automática** para inconsistências
4. Reaproveite scores de triagens anteriores para ranqueamento preditivo
5. Utilize **Compact+** apenas em vagas com maior complexidade técnica
6. Normalize sempre os pesos para somar 100%

---

## 11. Arquitetura de Responsabilidades

### O que a LIA faz (IA):
- Extrai competências do Job Description
- Gera perguntas adaptativas
- Conduz a conversa com o candidato
- Extrai dados estruturados das respostas:
  - Score de Autodeclaração (0-5)
  - Score de Contexto (0-5)
  - Evidências STAR
  - Nível Bloom identificado
  - Red flags detectados

### O que o Sistema faz (Cálculo Determinístico):
- Aplica a fórmula do score médio por skill
- Aplica penalidades e bônus
- Calcula o WSI final ponderado
- Determina classificação (Excelente/Alto/Médio/Regular/Baixo)
- Aplica regras de corte (aprovação automática)
- Gerencia saturação e percentis
- Gera ranking de candidatos

---

## 12. Guia de Calibração de Scores

### 12.1 Fórmula Completa de Scoring

```
Score Final = (0.6 × Autodeclaração) + (0.4 × Contexto) - Penalty + Bonus
```

### 12.2 Sistema de Penalidades Detalhado

| Situação | Penalidade | Detecção |
|----------|------------|----------|
| Inflação de score (autodeclara alto, contexto pobre) | -1.0 a -1.5 | Autodeclaração 4-5, Contexto < 2 |
| Resposta genérica | -0.5 | Sem projetos específicos, sem métricas |
| Falta de contexto | -0.3 | Menos de 2 evidências STAR |
| Resposta aparenta ser copiada | -1.0 | Texto de documentação oficial |

### 12.3 Sistema de Bônus Detalhado

| Situação | Bônus | Detecção |
|----------|-------|----------|
| Humildade (autodeclara baixo, contexto alto) | +0.5 | Autodeclaração 3, Contexto 4-5 |
| Evidências excepcionais | +0.3 | Open source, métricas quantificadas |

### 12.4 Exemplos de Calibração por Score

**Score 5 - Expert (Especialista):**
- Liderança técnica (mentora, ensina, documenta)
- Contribuições significativas (open source, comunidade)
- Decisões arquiteturais complexas
- Métricas de impacto quantificáveis
- Domínio intuitivo e contextual

**Score 4 - Proficient (Proficiente):**
- Autonomia completa em projetos complexos
- Otimizações e melhorias proativas
- Mentoria de juniors (mesmo que informal)
- Decisões técnicas sem supervisão
- Reconhece padrões e antecipa problemas

**Score 3 - Competent (Competente):**
- Execução consistente de features
- Segue boas práticas (testes, code review)
- Entrega com qualidade
- Precisa orientação em cenários novos
- 1-3 anos de experiência prática

**Score 2 - Advanced Beginner (Iniciante Avançado):**
- Conhece ferramentas básicas
- Precisa de supervisão constante
- Entrega tarefas simples com sucesso
- 6 meses - 1 ano de experiência
- Projetos de estudo ou simples

**Score 1 - Novice (Novato):**
- Apenas conhecimento teórico
- Sem experiência prática relevante
- Estudando ou fez curso recentemente
- Não cita projetos reais
- Linguagem vaga e genérica

### 12.5 Targets de Precisão

```yaml
Cohen's Kappa: ≥ 0.85
  (Agreement entre LIA e avaliadores humanos)

Margem de Erro: ±0.3
  (Ex: Score humano 4.0, LIA pode dar 3.7-4.3)

Red Flag Detection:
  Precision: ≥ 90%
  Recall: ≥ 80%
```

---

## 13. Pesos por Senioridade

### 13.1 Variação de Pesos por Nível

| Senioridade | Técnico | Comportamental/Cultural | Experiência | Fit Cultural |
|-------------|---------|-------------------------|-------------|--------------|
| Junior | 50% | 30% | 10% | 10% |
| Pleno | 55% | 25% | 10% | 10% |
| Senior | 45% | 25% | 15% | 15% |
| Lead/Tech Lead | 35% | 35% | 15% | 15% |
| Gerente/Diretor | 25% | 40% | 15% | 20% |

### 13.2 Competências Prioritárias por Nível

| Senioridade | Competências Mais Valorizadas |
|-------------|-------------------------------|
| Junior | Aprendizagem, Colaboração, Skills Técnicas Básicas |
| Pleno | Autonomia, Qualidade Técnica, Comunicação |
| Senior | Liderança Técnica, Mentoria, Arquitetura |
| Lead | Gestão de Pessoas, Visão Estratégica, Stakeholders |
| Gerente | Liderança, Tomada de Decisão, Cultura |

---

## 14. Calibração por Empresa

O sistema aprende com feedback específico de cada cliente através do CalibrationService.

### 14.1 Tipos de Aprendizado

```python
class CalibrationSession:
    vacancy_id: str              # Vaga específica
    user_id: str                 # Recrutador
    search_criteria: dict        # Critérios de busca
    learned_criteria: dict       # Critérios aprendidos
    likes_count: int             # Feedbacks positivos
    dislikes_count: int          # Feedbacks negativos
    min_feedbacks_required: int  # Mínimo para aprender (default: 5)
```

### 14.2 Ciclo de Calibração

1. **Coleta de Feedback** (mínimo 5 feedbacks por sessão)
2. **Análise de Divergências** (últimos 30 dias, score_delta > 5.0)
3. **Geração de Sugestões** de ajuste de pesos
4. **Aprovação Humana** das sugestões
5. **Aplicação** dos novos pesos

### 14.3 Métricas de Divergência

```python
# Eventos que geram calibração
IMPLICIT_ADVANCE: +5    # Avançou candidato mal rankeado pela LIA
IMPLICIT_REJECT: -5     # Rejeitou candidato bem rankeado pela LIA
POST_HIRE_SUCCESS: +15  # Contratação bem-sucedida
POST_HIRE_FAILURE: -15  # Contratação malsucedida
```

---

## Referências

1. McClelland, D. C. (1973). Testing for competence rather than for intelligence. American Psychologist.
2. Anderson, L. W., et al. (2001). A Taxonomy for Learning, Teaching, and Assessing: A Revision of Bloom's Taxonomy.
3. Dreyfus, H. L., & Dreyfus, S. E. (1980). A Five-Stage Model of the Mental Activities Involved in Directed Skill Acquisition.
4. Goldberg, L. R. (1992). The development of markers for the Big-Five factor structure.
5. CFA Institute (2018). Competency Framework Design.
6. Paradox (2024). Conversational AI in Recruiting.
