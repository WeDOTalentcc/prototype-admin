# Sistema de Comunicação LIA - Fluxo de Trabalho

## Visão Geral

O sistema de comunicação da LIA gerencia todas as interações com candidatos de forma automatizada, com controle human-in-the-loop para comunicações sensíveis.

## Diagrama de Fluxo Principal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FLUXO DE COMUNICAÇÃO LIA                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   TRIGGER    │     │  VALIDAÇÃO   │     │   DECISÃO    │     │    ENVIO     │
│   DO EVENTO  │────▶│   POLÍTICAS  │────▶│   APROVAÇÃO  │────▶│   MENSAGEM   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │                    │
       │                    │                    │                    │
       ▼                    ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ • Candidato  │     │ • Horários   │     │ • Automático │     │ • Email      │
│   adicionado │     │   (8h-20h)   │     │   ou         │     │ • WhatsApp   │
│ • Triagem    │     │ • Rate limit │     │ • Aprovação  │     │ • Chat       │
│   concluída  │     │   (3/dia)    │     │   manual     │     │ • Bell       │
│ • Entrevista │     │ • LGPD       │     │              │     │              │
│   agendada   │     │ • Quarentena │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

## Níveis de Aprovação por Tipo de Comunicação

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MATRIZ DE APROVAÇÃO                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────┐                    ┌─────────────────────┐        │
│  │   COM APROVAÇÃO     │                    │     AUTOMÁTICO      │        │
│  │   (Human-in-Loop)   │                    │   (Sem Aprovação)   │        │
│  └─────────────────────┘                    └─────────────────────┘        │
│           │                                          │                      │
│           ▼                                          ▼                      │
│  ┌─────────────────────┐                    ┌─────────────────────┐        │
│  │ • Contato inicial   │                    │ • Lembrete triagem  │        │
│  │ • Feedback rejeição │                    │ • Confirmação       │        │
│  │   (personalizado)   │                    │   entrevista        │        │
│  │ • Oferta de emprego │                    │ • Feedback triagem  │        │
│  │ • Envio em massa    │                    │   (aprovação/       │        │
│  │ • Encerramento      │                    │    reprovação)      │        │
│  │   processo          │                    │ • Notificações      │        │
│  └─────────────────────┘                    │   internas          │        │
│                                             └─────────────────────┘        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Fluxo de Contato Inicial (Com Aprovação)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    FLUXO DE CONTATO INICIAL                                   │
└──────────────────────────────────────────────────────────────────────────────┘

     ┌─────────────────┐
     │ Candidato       │
     │ adicionado à    │
     │ vaga            │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ Validar         │
     │ políticas:      │
     │ • Não está em   │
     │   quarentena    │
     │ • Não optou out │
     │ • Dentro do     │
     │   rate limit    │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ Gerar preview   │
     │ da mensagem     │
     │ (template)      │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ Criar           │
     │ PendingApproval │
     │ no banco        │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ Notificar       │
     │ recrutador      │
     │ (Chat + Bell)   │
     └────────┬────────┘
              │
              ▼
    ┌───────────────────┐
    │   RECRUTADOR      │
    │   DECIDE          │
    └────────┬──────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌───────┐         ┌───────┐
│APROVAR│         │REJEITAR│
└───┬───┘         └───┬───┘
    │                 │
    ▼                 ▼
┌─────────┐     ┌─────────┐
│ Verificar│    │ Registrar│
│ horário  │    │ motivo   │
│ de envio │    │ rejeição │
└────┬────┘     └─────────┘
     │
     ▼
┌─────────────┐
│ Dentro do   │────No────▶ AGENDAR PARA
│ horário?    │            PRÓXIMO HORÁRIO
│ (8h-20h)    │            PERMITIDO
└──────┬──────┘
       │
      Sim
       │
       ▼
┌─────────────┐
│ ENVIAR      │
│ MENSAGEM    │
│ (Email +    │
│  WhatsApp)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Registrar   │
│ no log de   │
│ comunicação │
└─────────────┘
```

## Fluxo de Feedback de Rejeição (Personalizado por IA)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│               FLUXO DE FEEDBACK PERSONALIZADO (REJEIÇÃO)                      │
└──────────────────────────────────────────────────────────────────────────────┘

     ┌─────────────────┐
     │ Candidato       │
     │ reprovado       │
     │ no processo     │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ Coletar dados   │
     │ do candidato:   │
     │ • Perfil        │
     │ • Pontos fortes │
     │ • Áreas desenv. │
     │ • Score WSI     │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ CLAUDE AI       │
     │ Personaliza     │
     │ feedback:       │
     │ • Específico    │
     │ • Construtivo   │
     │ • Humanizado    │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ Gera versões:   │
     │ • Email (HTML)  │
     │ • WhatsApp      │
     │   (resumido)    │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ PREVIEW para    │
     │ recrutador      │
     └────────┬────────┘
              │
              ▼
    ┌───────────────────┐
    │   RECRUTADOR      │
    │   REVISA          │
    └────────┬──────────┘
             │
    ┌────────┼────────┐
    │        │        │
    ▼        ▼        ▼
┌───────┐ ┌─────┐ ┌───────┐
│APROVAR│ │EDITAR│ │REJEITAR│
└───┬───┘ └──┬──┘ └───┬───┘
    │        │        │
    │        ▼        │
    │   ┌─────────┐   │
    │   │ Edita   │   │
    │   │ texto   │◀──┤
    │   └────┬────┘   │
    │        │        │
    └────────┼────────┘
             │
             ▼
     ┌─────────────────┐
     │ ENVIAR com      │
     │ tracking:       │
     │ • Abertura      │
     │ • Cliques       │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ Adicionar       │
     │ candidato à     │
     │ quarentena      │
     │ (90 dias)       │
     └─────────────────┘
```

## Políticas de Comunicação

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    POLÍTICAS DE COMUNICAÇÃO                                   │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────┐
│          HORÁRIOS PERMITIDOS        │
├─────────────────────────────────────┤
│                                     │
│   Segunda a Sexta: 08:00 - 20:00    │
│   Sábado/Domingo: NÃO ENVIAR        │
│   Feriados: NÃO ENVIAR              │
│                                     │
│   Timezone: America/Sao_Paulo       │
│                                     │
│   Mensagens fora do horário:        │
│   → Agendadas para próximo          │
│     horário válido                  │
│                                     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          RATE LIMITING             │
├─────────────────────────────────────┤
│                                     │
│   Por candidato/dia:                │
│   • Máximo: 3 mensagens             │
│   • Warning: 2 mensagens            │
│                                     │
│   Excedeu limite:                   │
│   → Agendar para próximo dia        │
│   → Notificar recrutador            │
│                                     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          LGPD COMPLIANCE           │
├─────────────────────────────────────┤
│                                     │
│   Opt-out:                          │
│   • Registrar solicitação           │
│   • Bloquear todos os canais        │
│   • Manter histórico (auditoria)    │
│                                     │
│   Consentimento:                    │
│   • Registrar data/hora             │
│   • Registrar IP                    │
│   • Registrar canal                 │
│                                     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│          QUARENTENA                │
├─────────────────────────────────────┤
│                                     │
│   Após rejeição:                    │
│   • Duração: 90 dias (padrão)       │
│   • Não recontatar para             │
│     mesma empresa/vaga similar      │
│                                     │
│   Após opt-out:                     │
│   • Quarentena permanente           │
│     (até opt-in explícito)          │
│                                     │
└─────────────────────────────────────┘
```

## Canais de Comunicação

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                       CANAIS DE COMUNICAÇÃO                                   │
└──────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐      │
│    │    EMAIL     │         │   WHATSAPP   │         │    CHAT      │      │
│    └──────────────┘         └──────────────┘         └──────────────┘      │
│           │                        │                        │              │
│           ▼                        ▼                        ▼              │
│    ┌──────────────┐         ┌──────────────┐         ┌──────────────┐      │
│    │ Candidatos   │         │ Candidatos   │         │ Recrutadores │      │
│    │ • Contato    │         │ • Triagem    │         │ • Aprovações │      │
│    │   inicial    │         │ • Lembretes  │         │ • Alertas    │      │
│    │ • Feedback   │         │ • Feedback   │         │ • Briefings  │      │
│    │ • Entrevista │         │ • Confirmação│         │              │      │
│    │ • Oferta     │         │              │         │              │      │
│    └──────────────┘         └──────────────┘         └──────────────┘      │
│                                                                             │
│    ┌──────────────┐         ┌──────────────┐                               │
│    │    BELL      │         │    TEAMS     │                               │
│    └──────────────┘         └──────────────┘                               │
│           │                        │                                        │
│           ▼                        ▼                                        │
│    ┌──────────────┐         ┌──────────────┐                               │
│    │ Recrutadores │         │ Stakeholders │                               │
│    │ • Pendências │         │ • Relatórios │                               │
│    │ • Alertas    │         │ • KPIs       │                               │
│    │ • Atualizações│        │ • Updates    │                               │
│    └──────────────┘         └──────────────┘                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Provedores de Comunicação

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    ABSTRAÇÃO DE PROVEDORES                                    │
└──────────────────────────────────────────────────────────────────────────────┘

                         ┌─────────────────────┐
                         │  CommunicationService│
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
     ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
     │  EmailProvider  │   │ WhatsAppProvider│   │  ChatProvider   │
     │   (Interface)   │   │   (Interface)   │   │   (Interface)   │
     └────────┬────────┘   └────────┬────────┘   └────────┬────────┘
              │                     │                     │
     ┌────────┼────────┐   ┌────────┼────────┐           │
     │        │        │   │        │        │           │
     ▼        ▼        ▼   ▼        ▼        ▼           ▼
┌─────────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐   ┌─────────────┐
│Mailgun │ │AWS │ │SMTP│ │Twilio│ │WA  │ │Mock│   │NotificationService│
│         │ │SES │ │    │ │     │ │API │ │    │   └─────────────┘
└─────────┘ └────┘ └────┘ └────┘ └────┘ └────┘

```

## Fluxo de Retry e Fallback

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    RETRY E FALLBACK                                           │
└──────────────────────────────────────────────────────────────────────────────┘

     ┌─────────────────┐
     │ Tentar enviar   │
     │ via provedor    │
     │ principal       │
     └────────┬────────┘
              │
              ▼
         ┌────────┐
         │ Sucesso?│
         └────┬───┘
              │
       ┌──────┴──────┐
       │             │
      Sim           Não
       │             │
       ▼             ▼
 ┌───────────┐ ┌───────────────┐
 │ Registrar │ │ Retry #1      │
 │ sucesso   │ │ (aguarda 60s) │
 │ no log    │ └───────┬───────┘
 └───────────┘         │
                       ▼
                  ┌────────┐
                  │ Sucesso?│
                  └────┬───┘
                       │
                ┌──────┴──────┐
                │             │
               Sim           Não
                │             │
                ▼             ▼
          ┌───────────┐ ┌───────────────┐
          │ Registrar │ │ Retry #2      │
          │ sucesso   │ │ (aguarda 120s)│
          └───────────┘ └───────┬───────┘
                                │
                                ▼
                           ┌────────┐
                           │ Sucesso?│
                           └────┬───┘
                                │
                         ┌──────┴──────┐
                         │             │
                        Sim           Não
                         │             │
                         ▼             ▼
                   ┌───────────┐ ┌───────────────┐
                   │ Registrar │ │ Retry #3      │
                   │ sucesso   │ │ (aguarda 240s)│
                   └───────────┘ └───────┬───────┘
                                         │
                                         ▼
                                    ┌────────┐
                                    │ Sucesso?│
                                    └────┬───┘
                                         │
                                  ┌──────┴──────┐
                                  │             │
                                 Sim           Não
                                  │             │
                                  ▼             ▼
                            ┌───────────┐ ┌───────────────┐
                            │ Registrar │ │ FALHA FINAL   │
                            │ sucesso   │ │ • Notificar   │
                            └───────────┘ │   recrutador  │
                                          │ • Marcar para │
                                          │   reenvio     │
                                          │   manual      │
                                          └───────────────┘
```

## Tabelas do Banco de Dados

| Tabela | Descrição |
|--------|-----------|
| `pending_approvals` | Mensagens aguardando aprovação do recrutador |
| `communication_logs` | Histórico de todas as comunicações enviadas |
| `candidate_opt_outs` | Registro de opt-outs LGPD |
| `candidate_quarantines` | Candidatos em período de quarentena |
| `personalized_feedback_records` | Feedbacks personalizados por IA |

## Métricas Disponíveis

- Taxa de aprovação de mensagens
- Tempo médio de aprovação
- Taxa de abertura de emails
- Taxa de resposta de candidatos
- Mensagens por canal
- Opt-outs por período
- Candidatos em quarentena

---

*Documentação gerada automaticamente - LIA Platform v1.0*
