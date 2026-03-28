# Candidatura via WhatsApp com LIA

## Visão Geral

Sistema de candidatura conversacional via WhatsApp onde a LIA conduz todo o processo de inscrição, coleta LGPD, parsing de CV, avaliação de aderência e triagem inicial. O candidato entra no pipeline normal e recebe feedback após avaliação do recrutador.

## Público-Alvo

- Clientes sem ATS próprio
- Vagas divulgadas via link público
- Candidatos que preferem canal conversacional

---

## Fluxo Completo da Conversa

### Fase 1: Entrada e Autorização LGPD

```
CANDIDATO: Olá! Tenho interesse na vaga de Desenvolvedor Full Stack - Ref: dev-fullstack-abc123

LIA: Olá! 👋 Que bom que você se interessou pela vaga de Desenvolvedor Full Stack!

Eu sou a LIA, assistente de recrutamento da [Empresa]. Vou te ajudar com o processo 
de candidatura.

Antes de começarmos, preciso da sua autorização:

📋 TERMO DE CONSENTIMENTO (LGPD)
Ao continuar, você autoriza:
• Coleta e armazenamento dos seus dados pessoais e profissionais
• Análise do seu currículo por inteligência artificial
• Compartilhamento das informações com o time de recrutamento
• Contato por WhatsApp, email ou telefone sobre esta e outras oportunidades

Seus dados serão tratados conforme nossa Política de Privacidade.
Você pode solicitar exclusão a qualquer momento.

Para continuar, responda: ACEITO
```

### Fase 2: Apresentação e Solicitação de CV

```
CANDIDATO: ACEITO

LIA: Perfeito! Obrigada pela autorização. ✅

Agora vou te conhecer melhor. Meu papel é:
1. Receber e analisar seu currículo
2. Avaliar sua aderência à vaga
3. Fazer algumas perguntas de triagem
4. Encaminhar sua candidatura para o recrutador

📄 Por favor, envie seu currículo (PDF ou Word).
```

### Fase 3: Parsing e Análise do CV

```
CANDIDATO: [Envia arquivo PDF]

LIA: Recebi seu currículo! Estou analisando... ⏳

[Após parsing - 5-10 segundos]

LIA: Analisei seu perfil, [Nome do Candidato]! 

📊 Resumo do que encontrei:
• Experiência: [X] anos em [área principal]
• Última posição: [Cargo] na [Empresa]
• Principais skills: [Skill 1], [Skill 2], [Skill 3]
• Formação: [Formação]

Está correto? Se precisar corrigir algo, me avise. 
Caso contrário, vamos para as perguntas de triagem.
```

### Fase 4: Triagem (Screening Questions)

```
CANDIDATO: Está correto!

LIA: Ótimo! Agora vou fazer algumas perguntas rápidas sobre a vaga:

1️⃣ Qual sua pretensão salarial para esta posição?

---

CANDIDATO: Entre 12 e 15 mil

LIA: Anotado! ✅

2️⃣ Qual sua disponibilidade para início caso seja aprovado?

---

CANDIDATO: Imediata

LIA: Perfeito! ✅

3️⃣ Você tem experiência com [tecnologia específica da vaga]?

---

CANDIDATO: Sim, 3 anos

LIA: Excelente! ✅

4️⃣ Você tem disponibilidade para trabalho [modelo da vaga: remoto/híbrido/presencial]?

---

CANDIDATO: Sim

LIA: Ótimo! ✅
```

### Fase 5: Perguntas Adicionais e Encerramento

```
LIA: Estamos quase terminando! Mais algumas informações:

📧 Qual seu melhor email para contato?
📱 Posso usar este WhatsApp para atualizações sobre o processo?

---

CANDIDATO: email@exemplo.com e sim, pode usar este WhatsApp

LIA: Perfeito! Seu cadastro está completo. ✅

📋 RESUMO DA SUA CANDIDATURA:
• Vaga: Desenvolvedor Full Stack
• Empresa: [Empresa]
• Pretensão: R$ 12.000 - R$ 15.000
• Disponibilidade: Imediata
• Status: Em análise

🔔 Próximos passos:
Vou encaminhar suas informações para o recrutador responsável. 
Você receberá um retorno sobre o andamento do processo em até [X] dias úteis.

Enquanto isso, você pode acompanhar outras vagas em: [link portal carreiras se houver]

Obrigada pelo interesse e boa sorte! 🍀
```

### Fase 6: Feedback (após avaliação do recrutador)

```
[Dias depois - Aprovado para próxima etapa]

LIA: Olá, [Nome]! 👋

Tenho novidades sobre sua candidatura para Desenvolvedor Full Stack!

🎉 Parabéns! Você foi aprovado para a próxima etapa do processo seletivo.

O recrutador [Nome] vai entrar em contato para agendar uma conversa.
Fique atento ao seu email e WhatsApp!

---

[Dias depois - Não aprovado]

LIA: Olá, [Nome]! 👋

Obrigada por participar do processo seletivo para Desenvolvedor Full Stack.

Após análise cuidadosa, decidimos seguir com outros candidatos cujos perfis 
estão mais alinhados aos requisitos específicos desta vaga.

Seu currículo permanece em nossa base e você será considerado para 
oportunidades futuras compatíveis com seu perfil.

Agradecemos seu interesse e desejamos sucesso! 🍀
```

---

## Arquitetura Técnica

### Componentes

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Página Vaga   │────▶│  WhatsApp API   │────▶│   LIA Backend   │
│   (Link Público)│     │    (Twilio)     │     │    (FastAPI)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                        ┌───────────────────────────────┼───────────────────────────────┐
                        │                               │                               │
                        ▼                               ▼                               ▼
                ┌───────────────┐              ┌───────────────┐              ┌───────────────┐
                │  CV Parser    │              │  Conversation │              │   Candidate   │
                │   (Gemini)    │              │    Manager    │              │    Service    │
                └───────────────┘              └───────────────┘              └───────────────┘
```

### Endpoints Necessários

```python
# Webhook para receber mensagens do WhatsApp
POST /api/v1/whatsapp/webhook

# Estado da conversa
GET  /api/v1/whatsapp/conversation/{phone_number}
POST /api/v1/whatsapp/conversation/{phone_number}/message

# Parsing de CV
POST /api/v1/cv/parse
```

### Modelo de Dados - Conversa WhatsApp

```python
class WhatsAppConversation:
    id: UUID
    phone_number: str
    job_vacancy_id: Optional[UUID]
    candidate_id: Optional[UUID]
    company_id: UUID
    
    # Estado da conversa
    state: ConversationState  # WAITING_LGPD, WAITING_CV, SCREENING, COMPLETED
    current_question_index: int
    
    # Dados coletados
    lgpd_accepted: bool
    lgpd_accepted_at: Optional[datetime]
    cv_received: bool
    cv_parsed_data: Optional[dict]
    screening_answers: dict
    
    # Metadados
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
```

### Estados da Conversa

```python
class ConversationState(str, Enum):
    INITIAL = "initial"              # Mensagem inicial recebida
    WAITING_LGPD = "waiting_lgpd"    # Aguardando aceite LGPD
    WAITING_CV = "waiting_cv"        # Aguardando envio do CV
    CONFIRMING_CV = "confirming_cv"  # Confirmando dados do CV
    SCREENING = "screening"          # Fazendo perguntas de triagem
    ADDITIONAL_INFO = "additional"   # Coletando info adicional
    COMPLETED = "completed"          # Candidatura finalizada
    FEEDBACK_SENT = "feedback_sent"  # Feedback enviado
```

---

## Integração com Pipeline Existente

### Criação Automática do Candidato

Após completar o fluxo de conversa:

1. **Criar candidato** com dados do CV parseado
2. **Associar à vaga** com status "Novo"
3. **Registrar respostas** de triagem
4. **Calcular LIA Score** inicial
5. **Notificar recrutador** via sistema de notificações

### Compatibilidade com Triagem Normal

O candidato que entrou via WhatsApp segue o mesmo fluxo:
- Aparece no pipeline da vaga
- Pode ter Voice Screening agendado
- Pode ter Video Interview
- Recebe parecer da LIA
- Recrutador pode aprovar/reprovar

---

## Integrações Externas

### Twilio WhatsApp Business API

- **Custo**: ~$0.005-0.05 por mensagem (varia por país)
- **Setup**: WhatsApp Business Account + Twilio Number
- **Webhook**: Recebe mensagens em tempo real
- **Media**: Suporta recebimento de documentos (CV)

### Alternativas

| Provedor | Custo | Vantagens | Desvantagens |
|----------|-------|-----------|--------------|
| Twilio | $$$ | Robusto, documentado | Mais caro |
| MessageBird | $$ | Bom preço | Menos features |
| 360dialog | $ | Barato | Setup mais complexo |
| Meta Cloud API | $ | Direto da Meta | Sem suporte local |

---

## Estimativa de Implementação

| Componente | Esforço | Prioridade |
|------------|---------|------------|
| Melhoria visual página pública | 4-6h | Alta |
| Disclaimer LGPD na página | 1-2h | Alta |
| Integração Twilio WhatsApp | 8-12h | Alta |
| Gerenciador de conversas | 6-8h | Alta |
| CV Parser com Gemini | 4-6h | Alta |
| Criação automática candidato | 2-3h | Alta |
| Sistema de feedback | 3-4h | Média |
| **Total** | **28-41h** | |

---

## Considerações de Segurança

1. **LGPD**: Aceite explícito registrado com timestamp
2. **Retenção**: CVs armazenados conforme política de privacidade
3. **Exclusão**: Candidato pode solicitar remoção dos dados
4. **Auditoria**: Todas as mensagens são logadas
5. **Multi-tenant**: company_id em todas as operações

---

## Métricas de Sucesso

- Taxa de conversão: visitantes da página → candidatos cadastrados
- Taxa de conclusão: iniciaram conversa → completaram candidatura
- Tempo médio do fluxo conversacional
- NPS dos candidatos sobre a experiência
- Redução de candidaturas incompletas vs formulário tradicional
