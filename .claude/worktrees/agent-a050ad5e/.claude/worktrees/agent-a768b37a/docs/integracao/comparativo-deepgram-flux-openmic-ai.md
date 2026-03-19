# Comparativo: Deepgram vs Flux vs OpenMic AI

**Data:** Dezembro 2025  
**Propósito:** Referência para decisão de plataforma de Voice AI para LIA

---

## Resumo Executivo

| Plataforma | Tipo | Custo/min (USD) | Custo/min (BRL)* | Melhor Para |
|------------|------|-----------------|------------------|-------------|
| **Deepgram (batch)** | API transcrição | $0.0043 | R$ 0.02 | Transcrição de áudios gravados |
| **Deepgram (streaming)** | API tempo real | $0.0077 | R$ 0.04 | Transcrição ao vivo |
| **Deepgram + Flux** | API agente voz | $0.08 | R$ 0.42 | Agentes conversacionais |
| **OpenMic AI** | Plataforma pronta | $0.10-0.15 | R$ 0.52-0.78 | Setup rápido sem dev |

*Câmbio estimado: 1 USD = R$ 5.20

---

## 1. O que é cada plataforma

### Deepgram
- **Empresa/plataforma** de voz-IA com APIs para STT (speech-to-text) e TTS (text-to-speech)
- **Voice Agent API**: pipeline completo voz → texto → LLM → voz
- **Modelos disponíveis**: Nova-3 (transcrição) e Flux (conversacional)
- **Abordagem**: "Faça você mesmo" - requer integração e desenvolvimento

### Flux (modelo da Deepgram)
- **Não é uma ferramenta separada** - é um modelo dentro da plataforma Deepgram
- **Foco**: Conversação em tempo real para agentes de voz
- **Diferenciais**:
  - Detecção de fim de turno (sabe quando o usuário parou de falar)
  - Suporte a interrupções ("barge-in")
  - Turn-taking natural
  - Latência muito baixa
- **Lançado em 2025** como "modelo de reconhecimento de fala conversacional"

### OpenMic AI
- **Plataforma "pronta para uso"** de agentes de voz AI
- **Foco**: Chamadas telefônicas, automação de atendimento
- **Features**: Workflow builder, múltiplos agentes, integração CRM, agendamento, SMS
- **Abordagem**: Menos código, mais configuração via interface

---

## 2. Comparativo de Preços Detalhado

### Deepgram - Modelos de Preço

| Modelo/Uso | Preço USD | Preço BRL* | Observação |
|------------|-----------|------------|------------|
| **Nova-3 (batch)** | $0.0043/min | R$ 0.02/min | Áudio pré-gravado, transcrição barata |
| **Nova-3 (streaming)** | $0.0077/min | R$ 0.04/min | Áudio ao vivo, real-time |
| **Flux Voice Agent API** | $0.080/min | R$ 0.42/min | STT + LLM + TTS completo |
| **Voice Agent (flat)** | $4.50/hora | R$ 23.40/hora | Previsibilidade por hora |

**Bônus inicial**: $200 em créditos gratuitos para novos usuários

### OpenMic AI - Planos Mensais

| Plano | Preço Mensal USD | Preço Mensal BRL* | Minutos Incluídos | Custo/min Extra |
|-------|------------------|-------------------|-------------------|-----------------|
| **Starter** | $29 | R$ 150 | 100 min | - |
| **Business** | $199 | R$ 1.035 | 1.000 min | $0.15/min |
| **Pro** | $450 | R$ 2.340 | 2.500 min | $0.13/min |
| **Agency** | $1.500 | R$ 7.800 | 7.000 min | $0.12/min |
| **Enterprise** | Custom | Custom | Custom | ~$0.08/min |

---

## 3. Cenários de Uso - Custo Mensal

### Cenário 1: Baixo Volume (500 min/mês)

| Plataforma | Custo USD | Custo BRL* |
|------------|-----------|------------|
| Deepgram + Flux | $40 | R$ 208 |
| OpenMic Business | $199 (1000 min) | R$ 1.035 |

**Vencedor**: Deepgram (5x mais barato)

### Cenário 2: Médio Volume (2.000 min/mês)

| Plataforma | Custo USD | Custo BRL* |
|------------|-----------|------------|
| Deepgram + Flux | $160 | R$ 832 |
| OpenMic Pro | $450 (2500 min) | R$ 2.340 |

**Vencedor**: Deepgram (2.8x mais barato)

### Cenário 3: Alto Volume (10.000 min/mês)

| Plataforma | Custo USD | Custo BRL* |
|------------|-----------|------------|
| Deepgram + Flux | $800 | R$ 4.160 |
| OpenMic Agency + extra | $1.500 + $360 = $1.860 | R$ 9.672 |

**Vencedor**: Deepgram (2.3x mais barato)

---

## 4. Comparativo Técnico

| Critério | Deepgram + Flux | OpenMic AI |
|----------|-----------------|------------|
| **Natureza** | API - requer desenvolvimento | Plataforma pronta - configuração via interface |
| **Flexibilidade** | Alta: escolhe modelos, integra backend próprio, BYO LLM/TTS | Média/Baixa: mais "out-of-the-box" |
| **Complexidade de implantação** | Alta: precisa de desenvolvedor | Baixa: deploy rápido sem código |
| **Customização de LLM** | Sim - usar Claude, GPT, etc. | Limitada |
| **Detecção de turnos** | Sim (Flux) | Sim |
| **Barge-in (interrupções)** | Sim (Flux) | Sim |
| **Latência** | Muito baixa | Boa |
| **Deploy** | Cloud, VPC, On-premises | Cloud apenas |
| **Compliance** | HIPAA, GDPR, SOC2 | Não especificado |
| **Workflow Builder** | Não (precisa construir) | Sim |
| **Múltiplos agentes** | Via código | Sim, nativo |
| **Integração CRM** | Via API | Nativo |
| **Chamadas simultâneas** | Ilimitadas (paga por uso) | Por plano |

---

## 5. Quando usar cada um

### Use Deepgram + Flux quando:
- Tem equipe técnica para integrar
- Precisa de alta customização
- Volume alto de chamadas (economia de custo)
- Quer usar seu próprio LLM (Claude, GPT)
- Precisa de compliance (HIPAA, GDPR)
- Quer deploy on-premises ou VPC
- Está construindo um produto próprio

### Use OpenMic AI quando:
- Não tem time técnico grande
- Precisa colocar em produção rápido
- Volume moderado de chamadas
- Quer interface visual para configurar
- Precisa de integrações CRM prontas
- Quer workflow builder visual

### Use Deepgram Nova-3 (sem Flux) quando:
- Só precisa transcrever áudios gravados
- Legendagem de vídeos
- Análise de reuniões
- Call analytics (pós-processamento)

---

## 6. Recomendação para LIA

### Contexto LIA:
- Entrevistas de voz com candidatos
- Screening automatizado
- Análise de respostas
- Integração com sistema existente

### Recomendação: **Deepgram + Flux**

**Motivos:**
1. **Custo**: 2-5x mais barato dependendo do volume
2. **Flexibilidade**: Podemos usar Claude (já integrado na LIA)
3. **Qualidade**: Flux é otimizado para conversas naturais
4. **Compliance**: LGPD/GDPR compatível
5. **Controle**: Deploy e dados sob nosso controle
6. **Escala**: Preço por uso, sem limite de chamadas simultâneas

**Considerações:**
- Requer mais desenvolvimento inicial
- Precisa construir workflow de entrevista
- Integração com backend LIA necessária

---

## 7. Links Úteis

- **Deepgram Voice Agent API**: https://deepgram.com/product/voice-agent-api
- **Deepgram Pricing**: https://deepgram.com/pricing
- **Deepgram Docs Flux**: https://developers.deepgram.com/docs/flux
- **OpenMic AI Pricing**: https://openmic.ai/pricing

---

## 8. Próximos Passos

1. [ ] Criar conta Deepgram (usa $200 créditos gratuitos)
2. [ ] Fazer POC com Flux para entrevista simples
3. [ ] Comparar qualidade de transcrição PT-BR
4. [ ] Avaliar latência em cenário real
5. [ ] Definir arquitetura de integração com LIA

---

*Valores convertidos com câmbio estimado de 1 USD = R$ 5.20. Verificar cotação atual no momento da contratação.*
