"""
Few-shot examples for Pipeline Analytics.

Exemplos de status do funil, análise de conversão, métricas de performance,
candidatos parados e comparação entre vagas.
"""

FUNNEL_STATUS = {
    "user": "Qual o status atual do funil da vaga de Tech Lead Frontend?",
    "assistant": """📊 **Status do Funil - Tech Lead Frontend**

**Vaga**: Tech Lead Frontend
**ID**: #TL-FE-2024-001
**Criada em**: 10/01/2024 (há 20 dias)
**Prazo**: 45 dias | **Restante**: 25 dias
**Gestor da Vaga**: Marina Costa

---

**Funil de Contratação**

```
Sourcing        ████████████████████████████████████  127 (100%)
    ↓ 35%
Triagem         ████████████████                       45 (35%)
    ↓ 40%
Entrev. RH      ██████████                             18 (14%)
    ↓ 44%
Entrev. Técnica ██████                                  8 (6%)
    ↓ 50%
Case            ████                                    4 (3%)
    ↓ 25%
Proposta        █                                       1 (0.8%)
```

| Etapa | Candidatos | Conversão | Tempo Médio |
|-------|------------|-----------|-------------|
| Sourcing | 127 | - | 2 dias |
| Triagem | 45 | 35% | 1.5 dias |
| Entrevista RH | 18 | 40% | 3 dias |
| Entrevista Técnica | 8 | 44% | 4 dias |
| Case | 4 | 50% | 5 dias |
| Proposta | 1 | 25% | Em andamento |

---

**Candidatos por Etapa**

*Proposta (1)*
| Candidato | Score | Dias na Etapa | Status |
|-----------|-------|---------------|--------|
| Ricardo Mendes | 89/100 | 3 dias | ⏳ Aguardando resposta |

*Case (4)*
| Candidato | Score | Dias na Etapa | Status |
|-----------|-------|---------------|--------|
| Amanda Silva | 82/100 | 2 dias | 🔄 Em avaliação |
| Pedro Oliveira | 78/100 | 2 dias | 🔄 Em avaliação |
| Juliana Martins | 75/100 | 5 dias | ⚠️ Atrasado |
| Lucas Costa | 73/100 | 4 dias | 🔄 Em avaliação |

*Entrevista Técnica (8)*
| Candidato | Score | Agendado | Status |
|-----------|-------|----------|--------|
| Fernanda Lima | 77/100 | 01/02 10h | ✅ Confirmado |
| Marcelo Santos | 76/100 | 01/02 14h | ✅ Confirmado |
| +6 outros | 70-75 | Diversos | ✅ Agendados |

---

**Métricas de Saúde**

| Métrica | Valor | Benchmark | Status |
|---------|-------|-----------|--------|
| Taxa conversão geral | 0.8% | 1.0% | ⚠️ Abaixo |
| Tempo médio no funil | 15 dias | 20 dias | ✅ Bom |
| Candidatos parados | 1 | 0 | ⚠️ Atenção |
| Score médio atual | 78/100 | 75/100 | ✅ Bom |
| Diversidade do pool | 35% fem. | 30% | ✅ Bom |

---

**⚠️ Alertas**

1. **Juliana Martins** está há 5 dias no Case sem retorno - prazo estava para ontem
2. **Taxa de conversão Triagem→RH** está baixa (40% vs 50% esperado)
3. **Ricardo Mendes** aguardando resposta de proposta há 3 dias

---

**💡 Insights**

- O funil está saudável com bons scores nos candidatos avançados
- A etapa de triagem pode estar com critérios muito rígidos
- Candidato em proposta tem alta chance de aceite (score 89)

---

💾 **Dados atualizados em**: 30/01/2024 15:30

➡️ **Ações Sugeridas**
1. Cobrar retorno de Juliana Martins sobre o case
2. Fazer follow-up com Ricardo Mendes sobre a proposta
3. Revisar critérios de triagem se conversão não melhorar

Deseja que eu detalhe alguma etapa ou candidato específico?""",
    "intent": "pipeline_status",
    "context": {
        "vaga": "Tech Lead Frontend",
        "vaga_id": "TL-FE-2024-001",
        "etapa": "monitoramento"
    }
}

CONVERSION_ANALYSIS = {
    "user": "Analise as taxas de conversão da vaga de Product Manager. Onde estamos perdendo candidatos?",
    "assistant": """📈 **Análise de Conversão - Product Manager**

**Vaga**: Product Manager Sênior
**ID**: #PM-2024-001
**Período Analisado**: 15/01 a 30/01/2024

---

**Funil com Análise de Perda**

```
Etapa                    Entraram    Saíram    Conversão    Perda
─────────────────────────────────────────────────────────────────
Sourcing                    200         -          -          -
    ↓
Triagem                      70       130        35%        65% ⚠️
    ↓
Entrevista RH                35        35        50%        50%
    ↓
Entrevista Técnica           18        17        51%        49%
    ↓
Case                          8        10        44%        56% ⚠️
    ↓
Proposta                      2         6        25%        75% ⚠️
    ↓
Contratado                    0         2         0%       100%
```

---

**🔴 Principais Gargalos Identificados**

**1. Triagem → Entrevista RH (65% de perda)**

| Motivo da Reprovação | Quantidade | % |
|---------------------|------------|---|
| Experiência insuficiente em B2B | 52 | 40% |
| Sem experiência com métricas | 31 | 24% |
| Pretensão salarial acima | 26 | 20% |
| Perfil mais técnico (PO) | 15 | 12% |
| Outros | 6 | 4% |

**Diagnóstico**: Sourcing está trazendo candidatos com perfil Product Owner ou B2C, não Product Manager B2B conforme requisitos.

**Recomendação**: Refinar boolean string e critérios de busca para focar em perfis B2B SaaS.

---

**2. Case → Proposta (75% de perda)**

| Motivo | Quantidade | % |
|--------|------------|---|
| Desempenho abaixo no case | 3 | 50% |
| Desistiu durante o processo | 2 | 33% |
| Não compareceu | 1 | 17% |

**Diagnóstico**: Case pode estar muito complexo ou candidatos estão recebendo outras ofertas durante o processo.

**Recomendação**: 
- Revisar complexidade do case (média de 6h para completar é alta)
- Acelerar processo - candidatos estão saindo por tempo
- Manter engajamento durante etapa de case

---

**3. Proposta → Contratado (100% de perda até agora)**

| Status das Propostas | Quantidade |
|---------------------|------------|
| Aguardando resposta | 1 |
| Recusada (contraproposta) | 1 |

**Diagnóstico**: Um candidato recebeu contraproposta. O outro está em análise há 4 dias.

**Recomendação**: 
- Agilizar proposta (enviar em até 48h após case)
- Entender competitividade salarial do mercado
- Considerar aumentar faixa se perdendo bons candidatos

---

**📊 Comparativo com Benchmark**

| Etapa | Nossa Taxa | Benchmark | Diferença |
|-------|------------|-----------|-----------|
| Sourcing → Triagem | 35% | 40% | -5% 🔴 |
| Triagem → Entrev. RH | 50% | 55% | -5% 🟡 |
| Entrev. RH → Técnica | 51% | 50% | +1% 🟢 |
| Técnica → Case | 44% | 45% | -1% 🟢 |
| Case → Proposta | 25% | 40% | -15% 🔴 |
| Proposta → Aceite | 0% | 70% | -70% 🔴 |

---

**🎯 Plano de Ação Recomendado**

| Prioridade | Ação | Impacto Esperado |
|------------|------|------------------|
| 🔴 Alta | Refinar sourcing para perfis B2B | +10% conversão triagem |
| 🔴 Alta | Simplificar case (4h max) | +15% conversão case |
| 🔴 Alta | Acelerar proposta (48h) | +30% aceite |
| 🟡 Média | Revisar faixa salarial | +20% aceite |
| 🟢 Baixa | Manter engajamento no case | +5% retenção |

---

**📉 Projeção se Mantiver Taxas Atuais**

Para contratar 1 candidato:
- Precisamos: ~300 candidatos sourced
- Tempo estimado: 45 dias
- Custo por candidato: Alto

**Com melhorias sugeridas**:
- Precisamos: ~150 candidatos sourced
- Tempo estimado: 30 dias
- Redução de 50% em esforço

---

💾 **Análise gerada em**: 30/01/2024 16:00

➡️ **Próximos Passos**
1. Agendar revisão de requisitos com gestor da vaga
2. Ajustar boolean string de sourcing
3. Simplificar case técnico
4. Definir SLA de 48h para proposta

Deseja que eu prepare uma apresentação desta análise para o gestor?""",
    "intent": "conversion_analysis",
    "context": {
        "vaga": "Product Manager Sênior",
        "vaga_id": "PM-2024-001",
        "etapa": "analise"
    }
}

PERFORMANCE_METRICS = {
    "user": "Me mostre as métricas de performance do recrutamento deste mês.",
    "assistant": """📊 **Métricas de Performance - Janeiro/2024**

**Período**: 01/01 a 30/01/2024
**Recrutadores Ativos**: 5
**Vagas Ativas**: 8

---

**Resumo Executivo**

| Métrica | Valor | vs Dez/23 | Meta |
|---------|-------|-----------|------|
| Vagas Fechadas | 3 | +1 (↑50%) | 4 ⚠️ |
| Candidatos Sourced | 847 | +120 (↑16%) | 800 ✅ |
| Entrevistas Realizadas | 156 | +23 (↑17%) | 150 ✅ |
| Propostas Enviadas | 8 | +2 (↑33%) | 10 ⚠️ |
| Time to Fill (média) | 32 dias | -3 (↓9%) | 35 ✅ |
| Cost per Hire (média) | R$ 4.200 | -R$ 300 (↓7%) | R$ 4.500 ✅ |

---

**Funil Agregado (Todas as Vagas)**

```
Candidatos Sourced      ██████████████████████████████  847 (100%)
    ↓ 38%
Triados                 ████████████                    322 (38%)
    ↓ 48%
Entrevistas RH          ██████                          156 (18%)
    ↓ 45%
Entrevistas Técnicas    ███                              70 (8%)
    ↓ 43%
Cases/Avaliações        ██                               30 (4%)
    ↓ 27%
Propostas               █                                 8 (1%)
    ↓ 38%
Contratados             █                                 3 (0.4%)
```

---

**Performance por Vaga**

| Vaga | Status | Sourced | Contratados | Time to Fill | Saúde |
|------|--------|---------|-------------|--------------|-------|
| Dev Python Sênior | ✅ Fechada | 127 | 1 | 28 dias | 🟢 |
| Analista de Dados | ✅ Fechada | 95 | 1 | 25 dias | 🟢 |
| Product Designer | ✅ Fechada | 68 | 1 | 35 dias | 🟢 |
| Tech Lead Frontend | 🟡 Em andamento | 127 | 0 | 20 dias* | 🟢 |
| Product Manager | 🟡 Em andamento | 200 | 0 | 15 dias* | 🟡 |
| Data Engineer | 🟡 Em andamento | 85 | 0 | 12 dias* | 🟢 |
| DevOps Engineer | 🔴 Atrasada | 110 | 0 | 42 dias* | 🔴 |
| UX Researcher | 🟡 Em andamento | 35 | 0 | 8 dias* | 🟢 |

*Em andamento

---

**Métricas de Qualidade**

| Indicador | Janeiro | Meta | Status |
|-----------|---------|------|--------|
| Score WSI médio contratados | 84/100 | 80/100 | ✅ Acima |
| NPS candidatos | 72 | 70 | ✅ Atingido |
| Taxa de aceite de propostas | 38% | 50% | ⚠️ Abaixo |
| Candidatos desistentes | 12% | 10% | ⚠️ Acima |
| No-shows em entrevistas | 5% | 5% | ✅ Na meta |
| Feedback em 48h | 78% | 90% | ⚠️ Abaixo |

---

**Performance por Recrutador**

| Recrutador | Vagas | Contratações | Entrevistas | Score Médio |
|------------|-------|--------------|-------------|-------------|
| Ana Silva | 3 | 2 | 45 | 82/100 |
| Bruno Costa | 2 | 1 | 38 | 79/100 |
| Carla Mendes | 2 | 0 | 42 | 81/100 |
| Diego Lima | 1 | 0 | 31 | 78/100 |

---

**Fontes de Candidatos**

| Fonte | Quantidade | % | Conversão | Custo/Candidato |
|-------|------------|---|-----------|-----------------|
| Banco Interno | 234 | 28% | 2.1% | R$ 0 |
| LinkedIn | 312 | 37% | 0.6% | R$ 45 |
| Pearch AI | 189 | 22% | 0.5% | R$ 32 |
| Indicações | 67 | 8% | 4.5% | R$ 0 |
| Candidaturas Espontâneas | 45 | 5% | 2.2% | R$ 0 |

**Insight**: Indicações têm a maior taxa de conversão (4.5%). Considerar programa de referral.

---

**Tendências e Insights**

📈 **Positivo**
- Time to Fill reduziu 9% vs mês anterior
- Qualidade dos contratados acima da meta (score 84)
- Volume de sourcing superou meta

📉 **Atenção**
- Taxa de aceite de propostas está 12% abaixo da meta
- Vaga de DevOps está travada há 42 dias
- Feedback de candidatos abaixo do SLA

---

**🎯 Recomendações para Fevereiro**

| Prioridade | Ação | Meta |
|------------|------|------|
| 🔴 Alta | Destravar vaga DevOps (rever requisitos) | Fechar em 15 dias |
| 🔴 Alta | Melhorar taxa de aceite (revisar propostas) | 50% |
| 🟡 Média | Acelerar feedback para candidatos | 90% em 48h |
| 🟢 Baixa | Implementar programa de indicações | +20% indicações |

---

💾 **Relatório gerado em**: 30/01/2024 17:00

➡️ Deseja que eu exporte este relatório em PDF ou aprofunde alguma métrica específica?""",
    "intent": "performance_metrics",
    "context": {
        "periodo": "Janeiro/2024",
        "etapa": "relatorio_mensal"
    }
}

STALLED_CANDIDATES = {
    "user": "Quais candidatos estão parados há mais de 5 dias sem movimentação?",
    "assistant": """⚠️ **Candidatos Parados - Análise de Estagnação**

**Critério**: Sem movimentação há mais de 5 dias
**Data de Análise**: 30/01/2024

---

**Resumo**

| Categoria | Quantidade | Ação Necessária |
|-----------|------------|-----------------|
| 🔴 Crítico (>10 dias) | 4 | Ação imediata |
| 🟡 Alerta (5-10 dias) | 7 | Acompanhar |
| **Total parados** | **11** | |

---

**🔴 Candidatos Críticos (>10 dias parados)**

| Candidato | Vaga | Etapa | Dias Parado | Último Contato | Motivo |
|-----------|------|-------|-------------|----------------|--------|
| Juliana Martins | Tech Lead Frontend | Case | 12 dias | 18/01 | Aguardando entrega do case |
| Fernando Silva | DevOps Engineer | Entrev. Técnica | 15 dias | 13/01 | Entrevistador indisponível |
| Marcela Costa | Product Manager | Proposta | 11 dias | 19/01 | Aguardando aprovação de budget |
| Roberto Almeida | DevOps Engineer | Triagem | 14 dias | 16/01 | Esquecido no pipeline |

**Ações Recomendadas - Críticos**

1. **Juliana Martins** (12 dias)
   - Risco: Candidata pode desistir
   - Ação: Contatar imediatamente para cobrar case ou entender bloqueio
   - Template: "Oi Juliana, como está a evolução do case? Posso ajudar com alguma dúvida?"

2. **Fernando Silva** (15 dias)
   - Risco: Alto - candidato provavelmente frustrado
   - Ação: Reagendar entrevista técnica urgentemente com outro entrevistador
   - Template: "Fernando, peço desculpas pelo atraso. Consegui vaga para amanhã às 14h, funciona?"

3. **Marcela Costa** (11 dias)
   - Risco: Pode aceitar outra proposta
   - Ação: Escalar para gerência aprovar budget
   - Template: "Marcela, estamos finalizando aprovações internas. Devo ter novidades até amanhã."

4. **Roberto Almeida** (14 dias)
   - Risco: Experiência negativa com a marca
   - Ação: Triar imediatamente ou dar feedback de reprovação
   - Template: Depende do resultado da triagem

---

**🟡 Candidatos em Alerta (5-10 dias)**

| Candidato | Vaga | Etapa | Dias | Motivo | Ação Sugerida |
|-----------|------|-------|------|--------|---------------|
| Amanda Oliveira | Tech Lead FE | Case | 7 dias | Realizando case | Checar progresso |
| Pedro Santos | Data Engineer | Entrev. Técnica | 6 dias | Aguardando agenda | Confirmar data |
| Carla Mendes | Analista Dados | Triagem | 8 dias | Backlog de triagem | Priorizar análise |
| Lucas Ferreira | Product Manager | Entrev. RH | 5 dias | Feriado + fim de semana | Normal, monitorar |
| Bruno Costa | DevOps | Entrev. Técnica | 9 dias | Técnico de férias | Realocar entrevistador |
| Tatiana Lima | UX Researcher | Sourced | 6 dias | Outreach não respondido | Fazer follow-up |
| Rafael Nunes | Data Engineer | Triagem | 5 dias | CV recebido tarde | Triar amanhã |

---

**Análise por Etapa**

| Etapa | Parados | % do Total | Causa Raiz Principal |
|-------|---------|------------|---------------------|
| Triagem | 3 | 27% | Backlog de CVs |
| Entrevista RH | 1 | 9% | Agenda lotada |
| Entrevista Técnica | 3 | 27% | Entrevistadores indisponíveis |
| Case | 2 | 18% | Candidatos não entregando |
| Proposta | 1 | 9% | Aprovação de budget |
| Outreach | 1 | 9% | Sem resposta |

---

**Análise por Vaga**

| Vaga | Candidatos Parados | Saúde do Pipeline |
|------|-------------------|-------------------|
| DevOps Engineer | 3 | 🔴 Crítico |
| Tech Lead Frontend | 2 | 🟡 Alerta |
| Data Engineer | 2 | 🟡 Alerta |
| Product Manager | 2 | 🟡 Alerta |
| Analista Dados | 1 | 🟢 Ok |
| UX Researcher | 1 | 🟢 Ok |

---

**📊 Impacto no Tempo de Contratação**

| Métrica | Com Parados | Sem Parados | Impacto |
|---------|-------------|-------------|---------|
| Time to Fill médio | 35 dias | 28 dias | +7 dias |
| Custo adicional estimado | - | - | R$ 2.800/vaga |
| Risco de desistência | 25% | 8% | +17% |

---

**🎯 Plano de Ação Imediato**

| Prioridade | Ação | Responsável | Prazo |
|------------|------|-------------|-------|
| 1 | Reagendar Fernando Silva | Recruiter Bruno | Hoje |
| 2 | Cobrar case Juliana Martins | Recruiter Ana | Hoje |
| 3 | Escalar budget Marcela Costa | Gerente RH | Hoje |
| 4 | Decidir Roberto Almeida | Recruiter Carla | Amanhã |
| 5 | Triar 3 CVs pendentes | Triagem | Amanhã |
| 6 | Follow-up Tatiana Lima | Sourcing | Amanhã |

---

💾 **Alertas configurados**: Notificação automática quando candidato ficar >5 dias parado

➡️ **Próximos Passos**
1. Executar ações do plano imediato
2. Revisar processo para evitar gargalos recorrentes
3. Considerar mais entrevistadores técnicos no pool

Deseja que eu envie mensagens de follow-up para algum destes candidatos?""",
    "intent": "stalled_candidates",
    "context": {
        "criterio": "5+ dias sem movimentação",
        "etapa": "monitoramento"
    }
}

JOB_COMPARISON = {
    "user": "Compare as vagas de Desenvolvedor Python e Tech Lead Frontend em termos de performance.",
    "assistant": """📊 **Comparativo de Vagas**

**Vagas Comparadas**:
1. Desenvolvedor Python Sênior (#DEV-PY-2024-001)
2. Tech Lead Frontend (#TL-FE-2024-001)

**Período**: Janeiro/2024

---

**Visão Geral**

| Métrica | Dev Python | Tech Lead FE | Diferença |
|---------|------------|--------------|-----------|
| Status | ✅ Fechada | 🟡 Em andamento | - |
| Dias aberta | 28 | 20 (em curso) | -8 |
| Candidatos sourced | 127 | 127 | = |
| Taxa conversão geral | 0.8% | 0.8%* | = |
| Score médio | 76/100 | 78/100 | +2 |
| Contratados | 1 | 0 | -1 |

*Estimada (vaga em andamento)

---

**Comparativo de Funil**

```
                        Dev Python          Tech Lead FE
Etapa                   Qtd    Conv%       Qtd    Conv%       Melhor
────────────────────────────────────────────────────────────────────
Sourcing                127     -          127     -           =
Triagem                  45    35%          45    35%          =
Entrevista RH            20    44%          18    40%         Python
Entrevista Técnica       10    50%           8    44%         Python
Case                      4    40%           4    50%         TL FE
Proposta                  2    50%           1    25%         Python
Contratado                1    50%           0     0%         Python
```

---

**Análise de Gargalos**

| Etapa | Dev Python | Tech Lead FE | Observação |
|-------|------------|--------------|------------|
| Sourcing→Triagem | 35% | 35% | Igual - critérios similares |
| Triagem→Entrev. RH | 44% 🟢 | 40% 🟡 | Python melhor qualificação inicial |
| RH→Técnica | 50% | 44% | Tech Lead mais exigente tecnicamente |
| Técnica→Case | 40% | 50% 🟢 | Cases TL FE mais acessíveis |
| Case→Proposta | 50% | 25% 🔴 | TL FE perdendo candidatos no case |
| Proposta→Aceite | 50% | 0% | TL FE ainda sem fechamento |

---

**Qualidade dos Candidatos**

| Métrica | Dev Python | Tech Lead FE |
|---------|------------|--------------|
| Score médio triagem | 72/100 | 75/100 |
| Score médio finalistas | 85/100 | 82/100 |
| Candidatos >80 score | 8 (6%) | 6 (5%) |
| Desistências | 3 (2%) | 2 (2%) |
| No-shows | 1 (1%) | 0 (0%) |

---

**Tempo por Etapa (dias)**

| Etapa | Dev Python | Tech Lead FE | Benchmark |
|-------|------------|--------------|-----------|
| Sourcing | 3 | 4 | 5 |
| Triagem | 2 | 2 | 2 |
| Entrevista RH | 4 | 3 | 3 |
| Entrevista Técnica | 5 | 4 | 4 |
| Case | 7 | 5* | 5 |
| Proposta | 4 | 2* | 3 |
| **Total** | **25** | **20*** | **22** |

*Em andamento

---

**Custos**

| Item | Dev Python | Tech Lead FE |
|------|------------|--------------|
| Custo sourcing | R$ 1.200 | R$ 1.350 |
| Horas recrutador | 45h | 38h |
| Custo por candidato | R$ 9.45 | R$ 10.63 |
| Custo por contratação | R$ 4.200 | R$ 4.800* |

*Estimado

---

**Insights Comparativos**

**Dev Python (Sucesso)**
- ✅ Fechou dentro do prazo (28 dias)
- ✅ Taxa de aceite de proposta alta (50%)
- ✅ Bom fluxo do início ao fim
- 📌 Pode ser modelo para outras vagas técnicas

**Tech Lead Frontend (Em andamento)**
- ⚠️ Gargalo na etapa Case→Proposta
- ⚠️ Candidata em proposta há 3 dias sem resposta
- ✅ Bom tempo de processo até agora
- 📌 Risco de perder candidatos se demorar

---

**🎯 Lições Aprendidas**

| Aprendizado | Dev Python | Aplicar em TL FE |
|-------------|------------|------------------|
| Proposta rápida | Enviou em 24h | Acelerar atual |
| Case objetivo | 4h para completar | Case está OK |
| Entrevistador fixo | Mesmo técnico | Manter consistência |
| Feedback rápido | 48h máximo | Implementar |

---

**Projeção Tech Lead FE**

Se mantiver taxa atual:
- Fechamento estimado: 35 dias total
- Candidato mais provável: Ricardo Mendes (score 89)
- Chance de sucesso: 75%

Se aplicar melhorias do Python:
- Fechamento estimado: 28 dias total
- Chance de sucesso: 90%

---

💾 **Comparativo gerado em**: 30/01/2024 18:00

➡️ **Recomendações**
1. Aplicar práticas do processo de Dev Python no TL Frontend
2. Acelerar resposta de proposta para Ricardo Mendes
3. Usar esta análise como benchmark para próximas vagas

Deseja que eu detalhe algum aspecto específico ou gere um relatório para a liderança?""",
    "intent": "job_comparison",
    "context": {
        "vagas": ["Desenvolvedor Python Sênior", "Tech Lead Frontend"],
        "etapa": "analise_comparativa"
    }
}

PIPELINE_EXAMPLES = [
    FUNNEL_STATUS,
    CONVERSION_ANALYSIS,
    PERFORMANCE_METRICS,
    STALLED_CANDIDATES,
    JOB_COMPARISON,
]
