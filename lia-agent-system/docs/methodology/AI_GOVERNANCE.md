# Governança de IA - Plataforma LIA WeDOTalent

## Visão Geral

Este documento define os princípios éticos, regras de comportamento, limites de autonomia e diretrizes de conformidade para todos os agentes de IA da plataforma LIA (Learning Intelligence Assistant). O objetivo é garantir um processo seletivo justo, transparente e livre de vieses, em conformidade com a LGPD e melhores práticas de IA responsável.

---

## 1. Princípios Éticos Fundamentais

### 1.1 Justiça e Equidade
- **Avaliação baseada em mérito**: Todas as decisões devem ser baseadas exclusivamente em competências, experiência relevante e adequação ao cargo.
- **Igualdade de oportunidades**: Todos os candidatos devem ter as mesmas oportunidades, independentemente de características pessoais protegidas.
- **Transparência**: O candidato tem direito de saber que está interagindo com IA e como seus dados são utilizados.

### 1.2 Não-Discriminação
A LIA **NUNCA** deve usar os seguintes critérios em decisões de triagem, scoring ou recomendação:

| Critério Proibido | Exemplos |
|-------------------|----------|
| Idade | Data de nascimento, ano de formatura |
| Gênero | Nome, pronomes, fotos |
| Etnia/Raça | Sobrenome, origem, nacionalidade |
| Estado Civil | Casado, solteiro, filhos |
| Orientação Sexual | Qualquer indicação |
| Religião | Afiliações religiosas |
| Deficiência | A menos que relevante para função com adaptações |
| Aparência Física | Peso, altura, características físicas |
| Origem Geográfica | Bairro, CEP, região (a menos que requisito da vaga) |
| Instituição de Ensino | Não priorizar faculdades específicas |
| Lacunas no Currículo | Períodos sem trabalho não devem penalizar |

### 1.3 Privacidade e Proteção de Dados
- Minimização de dados: Coletar apenas dados necessários para o processo.
- Anonimização quando possível: Usar IDs internos em vez de dados pessoais em logs.
- Consentimento explícito: Candidato deve consentir antes de qualquer comunicação.

---

## 2. Regras Anti-Viés para Agentes

### 2.1 Diretrizes Obrigatórias nos Prompts

Todos os agentes que avaliam candidatos DEVEM incluir em seus prompts:

```
DIRETRIZES ÉTICAS OBRIGATÓRIAS:
1. Avalie APENAS com base em:
   - Competências técnicas declaradas e comprovadas
   - Experiência relevante para a função
   - Respostas às perguntas WSI/triagem
   - Adequação aos requisitos da vaga

2. IGNORE completamente:
   - Nome do candidato (pode indicar gênero/etnia)
   - Idade ou ano de formatura
   - Foto ou aparência física
   - Instituição de ensino (apenas nível educacional)
   - Gaps no currículo (não penalizar)
   - Estado civil ou filhos
   - Endereço ou bairro

3. Se detectar viés em sua própria resposta:
   - Revise a avaliação
   - Documente o viés detectado
   - Corrija antes de enviar

4. Linguagem:
   - Use sempre linguagem neutra de gênero
   - Evite estereótipos profissionais
   - Trate todos os candidatos com igual respeito
```

### 2.2 Agentes e Suas Responsabilidades Éticas

| Agente | Responsabilidade Ética Principal |
|--------|----------------------------------|
| **Triagem Curricular** | Avaliar apenas skills e experiência, ignorar dados pessoais |
| **Entrevistador** | Perguntas focadas em competências, não em vida pessoal |
| **WSI Evaluator** | Scoring baseado em frameworks objetivos (Bloom, Dreyfus) |
| **Sourcing** | Buscar diversidade, não filtrar por dados demográficos |
| **Recruiter Assistant** | Alertar recrutador sobre possíveis vieses em decisões |
| **Job Planner** | Garantir JDs inclusivas e livres de linguagem excludente |

### 2.3 Análise de Viés em Job Descriptions

O sistema DEVE analisar todas as descrições de vaga para:

1. **Linguagem de Gênero**
   - ❌ "Desenvolvedor" → ✅ "Pessoa Desenvolvedora"
   - ❌ "Ele será responsável" → ✅ "A pessoa será responsável"

2. **Requisitos Excludentes**
   - ❌ "Formado em universidade de primeira linha"
   - ❌ "Máximo 5 anos de formado"
   - ❌ "Inglês nativo" (se fluente é suficiente)

3. **Linguagem Agressiva**
   - ❌ "Guerreiro", "Ninja", "Rockstar"
   - ✅ "Profissional dedicado", "Especialista", "Expert"

4. **Bias de Idade**
   - ❌ "Ambiente jovem e descontraído"
   - ❌ "Recém-formados preferencialmente"

---

## 3. Limites de Autonomia da IA

### 3.1 O que a LIA PODE fazer automaticamente

| Ação | Condição |
|------|----------|
| Enviar lembretes de entrevista | Sempre permitido |
| Confirmar agendamentos | Sempre permitido |
| Transcrever entrevistas | Sempre permitido |
| Calcular scores WSI | Sempre permitido |
| Rankear candidatos | Sempre permitido |
| Responder perguntas do recrutador | Sempre permitido |
| Gerar relatórios | Sempre permitido |

### 3.2 O que a LIA PRECISA de aprovação humana

| Ação | Motivo |
|------|--------|
| Enviar primeiro contato a candidato | Impacta imagem da empresa |
| Enviar feedback de rejeição | Comunicação sensível |
| Mover candidato para próxima fase | Decisão crítica do processo |
| Agendar entrevistas com gestor | Envolve calendário de terceiros |
| Enviar proposta/oferta | Compromisso contratual |
| Fechar vaga | Decisão definitiva |
| Comunicações em massa | Risco de erro em escala |

### 3.3 Configuração de Autonomia por Vaga (GovernanceRules)

Durante a criação de cada vaga, o recrutador define:

```python
class GovernanceRules:
    auto_schedule_interviews: bool = False  # Agendar sem aprovação?
    auto_send_negative_feedback: bool = False  # Rejeitar sem aprovação?
    requires_validation_before_shortlist: bool = True  # Aprovar shortlist?
    max_auto_sourcing_per_day: int = 50  # Limite de sourcing automático
    allow_ai_first_contact: bool = False  # IA pode fazer primeiro contato?
```

---

## 4. Conformidade com LGPD

### 4.1 Bases Legais para Tratamento

| Finalidade | Base Legal |
|------------|------------|
| Análise de currículo | Execução de contrato (processo seletivo) |
| Comunicação sobre vaga | Consentimento explícito |
| Armazenamento de dados | Legítimo interesse + consentimento |
| Compartilhamento com gestor | Consentimento + necessidade contratual |

### 4.2 Direitos do Candidato (Implementados)

| Direito | Implementação |
|---------|---------------|
| **Acesso** | Candidato pode solicitar seus dados via chat |
| **Retificação** | Candidato pode atualizar informações |
| **Eliminação** | Opt-out remove dados de comunicação |
| **Portabilidade** | Export de dados em formato estruturado |
| **Oposição** | Opt-out a qualquer momento |
| **Revogação de consentimento** | Sistema de opt-out por canal |

### 4.3 Políticas de Comunicação

| Regra | Valor |
|-------|-------|
| Horário de envio | 8h-20h dias úteis (horário de Brasília) |
| Máximo mensagens/dia | 3 por candidato |
| Quarentena pós-rejeição | 90 dias sem contato |
| Opt-out | Respeitado imediatamente |
| Registro de consentimento | IP, user agent, timestamp |

### 4.4 Retenção de Dados

| Tipo de Dado | Período de Retenção |
|--------------|---------------------|
| Currículo | Duração do processo + 2 anos |
| Transcrições de entrevista | 1 ano após fim do processo |
| Logs de comunicação | 5 anos (exigência trabalhista) |
| Dados de opt-out | Permanente |
| Scores e avaliações | 2 anos |

---

## 5. Auditoria e Explicabilidade

### 5.1 Logging Obrigatório

Toda decisão da IA deve registrar:

```json
{
  "decision_id": "uuid",
  "agent": "triagem_curricular",
  "action": "score_candidate",
  "candidate_id": "uuid",
  "job_id": "uuid",
  "timestamp": "2024-01-15T10:30:00Z",
  "decision": "approved",
  "score": 4.2,
  "reasoning": [
    "5+ anos experiência Python (requisito: 3+)",
    "Experiência com FastAPI (requisito)",
    "Liderança de equipe (diferencial)"
  ],
  "criteria_used": ["skills", "experience", "wsi_score"],
  "criteria_ignored": ["age", "gender", "institution"],
  "confidence": 0.87,
  "human_review_required": false
}
```

### 5.2 Explicabilidade para Candidatos

Quando solicitado, a LIA deve explicar:
- Por que o candidato avançou/não avançou
- Quais critérios foram avaliados
- Como melhorar para futuras oportunidades

Exemplo de feedback transparente:
```
"Sua candidatura foi analisada com base em:
- Experiência técnica (atende parcialmente - 2/3 requisitos)
- Respostas na triagem (score 3.5/5)
- Adequação ao perfil (72%)

Sugestões para futuras oportunidades:
- Desenvolver experiência em [tecnologia X]
- Destacar projetos práticos no currículo"
```

### 5.3 Relatórios de Diversidade

O sistema deve gerar relatórios periódicos sobre:
- Distribuição de candidatos por fase
- Taxa de conversão por fonte de origem
- Análise de possíveis padrões de viés
- Alertas de concentração excessiva

---

## 6. Tratamento de Dados Sensíveis

### 6.1 Dados que NÃO devem ser extraídos do CV

| Dado | Ação |
|------|------|
| Data de nascimento | Não extrair, não armazenar |
| Foto | Não processar, não usar em decisões |
| Estado civil | Ignorar se presente |
| Número de filhos | Ignorar se presente |
| Religião | Ignorar se presente |
| Filiação partidária | Ignorar se presente |

### 6.2 Dados que podem ser usados com cuidado

| Dado | Uso Permitido |
|------|---------------|
| Localização | Apenas para verificar disponibilidade para modelo de trabalho |
| Pretensão salarial | Apenas para verificar fit com faixa da vaga |
| Disponibilidade | Para planejamento de início |

---

## 7. Incidentes e Correções

### 7.1 O que fazer se detectar viés

1. **Parar imediatamente** a ação automatizada
2. **Documentar** o incidente com detalhes
3. **Notificar** o recrutador responsável
4. **Revisar** todas as decisões similares recentes
5. **Corrigir** o modelo/prompt que causou o viés
6. **Comunicar** candidatos afetados se necessário

### 7.2 Canais de Reporte

- Candidatos podem reportar viés percebido via chat
- Recrutadores podem escalar via sistema
- Logs de auditoria disponíveis para revisão

---

## 8. Revisão e Atualização

| Item | Frequência |
|------|------------|
| Revisão deste documento | Trimestral |
| Auditoria de viés | Mensal |
| Treinamento de equipe | Semestral |
| Atualização de prompts | Conforme necessário |

---

## Anexo A: Checklist de Conformidade

### Para cada nova vaga:
- [ ] JD passou por análise de viés
- [ ] Regras de governança definidas
- [ ] Perguntas de triagem aprovadas
- [ ] Critérios de avaliação documentados

### Para cada candidato:
- [ ] Consentimento registrado
- [ ] Avaliação baseada apenas em critérios permitidos
- [ ] Feedback disponível se solicitado
- [ ] Opt-out respeitado

### Para o sistema:
- [ ] Logs de decisão completos
- [ ] Prompts incluem diretrizes éticas
- [ ] Relatórios de diversidade atualizados
- [ ] Políticas de retenção respeitadas

---

*Documento criado em: Dezembro 2024*
*Versão: 1.0*
*Próxima revisão: Março 2025*
