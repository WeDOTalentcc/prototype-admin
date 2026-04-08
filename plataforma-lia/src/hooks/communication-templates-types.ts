export type TemplateChannel = 'email' | 'whatsapp'
export type TemplateSituation =
  | 'contato_inicial'
  | 'follow_up'
  | 'triagem'
  | 'agendamento'
  | 'feedback_positivo'
  | 'feedback_construtivo'
  | 'contato_rapido'
  | 'lembrete'
  | 'proposta'
  | 'proposta_aceita'
  | 'vaga_fechada'
  | 'avaliacao_tecnica'
  | 'vaga_cancelada'
  | 'vaga_pausada'
  | 'vaga_retomada'
  | string

export interface CommunicationTemplate {
  id: string
  name: string
  category: 'approval' | 'rejection' | 'scheduling' | 'followup' | 'feedback' | 'offer'
  subject: string
  body: string
  variables: string[]
  isActive: boolean
  lastUpdated: string
  channel: TemplateChannel
  situation: TemplateSituation
}

export const DEFAULT_TEMPLATES: CommunicationTemplate[] = [
  {
    id: 'default-contato-inicial-email',
    name: 'Contato Inicial (Email)',
    category: 'followup',
    subject: 'Oportunidade - {{vaga}}',
    body: `Ol\u00e1 {{candidato_nome}},

Esperamos que esteja bem!

Identificamos seu perfil e gostar\u00edamos de conversar sobre uma excelente oportunidade para a posi\u00e7\u00e3o de {{vaga}}.

Sua experi\u00eancia e qualifica\u00e7\u00f5es s\u00e3o muito alinhadas com o que buscamos.

Podemos agendar uma conversa?

Atenciosamente,
{{recrutador_nome}}
{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'email',
    situation: 'contato_inicial'
  },
  {
    id: 'default-follow-up-email',
    name: 'Follow-up (Email)',
    category: 'followup',
    subject: 'Acompanhamento - {{vaga}}',
    body: `Ol\u00e1 {{candidato_nome}},

Espero que esteja bem! Gostaria de fazer um acompanhamento sobre sua candidatura para a posi\u00e7\u00e3o de {{vaga}}.

Tem alguma d\u00favida sobre o processo ou a vaga?

Fico \u00e0 disposi\u00e7\u00e3o.

Atenciosamente,
{{recrutador_nome}}
{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'email',
    situation: 'follow_up'
  },
  {
    id: 'default-triagem-email',
    name: 'Convite Triagem (Email)',
    category: 'scheduling',
    subject: 'Pr\u00f3ximo passo: Avalia\u00e7\u00e3o - {{vaga}}',
    body: `Ol\u00e1 {{candidato_nome}},

Esperamos que esteja bem!

Estamos avan\u00e7ando em nosso processo seletivo para a posi\u00e7\u00e3o de {{vaga}} e gostar\u00edamos de convid\u00e1-lo(a) para a pr\u00f3xima etapa: uma triagem r\u00e1pida com a nossa assistente LIA.

\ud83d\udccb Sobre a triagem:
\u2022 Dura\u00e7\u00e3o estimada: 15-20 minutos
\u2022 Formato: Conversa por chat ou WhatsApp com a LIA
\u2022 Objetivo: Conhecer melhor sua forma de pensar e resolver problemas

\ud83d\udd17 Para iniciar, escolha uma das op\u00e7\u00f5es:
\u2022 INICIAR VIA CHAT WEB - Clique aqui para conversar pelo navegador
\u2022 INICIAR VIA WHATSAPP - Clique aqui para conversar pelo WhatsApp

\u26a0\ufe0f Ao iniciar, voc\u00ea ser\u00e1 apresentado aos termos de uso e pol\u00edtica de privacidade (LGPD).

Essa avalia\u00e7\u00e3o nos ajuda a entender melhor seu perfil e garantir que a vaga seja compat\u00edvel com suas habilidades e expectativas.

Qualquer d\u00favida, estamos \u00e0 disposi\u00e7\u00e3o!

Atenciosamente,
{{recrutador_nome}}
{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome', 'link_triagem', 'duracao_triagem'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'email',
    situation: 'triagem'
  },
  {
    id: 'default-agendamento-email',
    name: 'Convite Entrevista (Email)',
    category: 'scheduling',
    subject: 'Convite para Entrevista - {{vaga}}',
    body: `Ol\u00e1 {{candidato_nome}},

Parab\u00e9ns por avan\u00e7ar no processo seletivo para {{vaga}}! \ud83c\udf89

Gostar\u00edamos de convid\u00e1-lo(a) para a pr\u00f3xima etapa: uma entrevista {{formato_entrevista}}.

\ud83d\udcc5 Detalhes da Entrevista:
\u2022 Tipo: Entrevista {{formato_entrevista}}
\u2022 Dura\u00e7\u00e3o: {{duracao_entrevista}} minutos
\u2022 Plataforma: {{link_entrevista}}
\u2022 Entrevistador: {{entrevistador_nome}}

\ud83d\uddd3\ufe0f Escolha o melhor hor\u00e1rio:
Clique no link abaixo para visualizar as disponibilidades e escolher o hor\u00e1rio que melhor funciona para voc\u00ea:

{{link_calendario}}

Ap\u00f3s a confirma\u00e7\u00e3o, voc\u00ea receber\u00e1:
\u2705 Email de confirma\u00e7\u00e3o com todos os detalhes
\u2705 Convite do Outlook/Google Calendar
\u2705 Link da plataforma de v\u00eddeo (se aplic\u00e1vel)

Qualquer d\u00favida, estamos \u00e0 disposi\u00e7\u00e3o!

Atenciosamente,
{{recrutador_nome}}
{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'formato_entrevista', 'duracao_entrevista', 'entrevistador_nome', 'link_entrevista', 'link_calendario', 'data_entrevista', 'horario_entrevista', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'email',
    situation: 'agendamento'
  },
  {
    id: 'default-feedback-positivo-email',
    name: 'Feedback Positivo (Email)',
    category: 'feedback',
    subject: 'Atualiza\u00e7\u00e3o - Processo Seletivo {{vaga}}',
    body: `Ol\u00e1 {{candidato_nome}},

Esperamos que esteja bem!

\u00c9 com grande satisfa\u00e7\u00e3o que compartilhamos o feedback sobre sua participa\u00e7\u00e3o no processo seletivo para {{vaga}}.

\u2705 Pontos Positivos:
\u2022 Sua experi\u00eancia e conhecimento t\u00e9cnico impressionaram nossa equipe
\u2022 Demonstrou excelente comunica\u00e7\u00e3o e clareza nas respostas
\u2022 Alinhamento com os valores e cultura da empresa

\ud83d\udcc8 Pr\u00f3ximos Passos:
{{proximos_passos}}

Agradecemos seu interesse e dedica\u00e7\u00e3o ao processo!

Atenciosamente,
{{recrutador_nome}}
{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'pontos_positivos', 'proximos_passos', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'email',
    situation: 'feedback_positivo'
  },
  {
    id: 'default-feedback-construtivo-email',
    name: 'Feedback Construtivo (Email)',
    category: 'rejection',
    subject: 'Retorno - Processo Seletivo {{vaga}}',
    body: `Ol\u00e1 {{candidato_nome}},

Agradecemos sua participa\u00e7\u00e3o no processo seletivo para {{vaga}}.

Gostar\u00edamos de compartilhar nosso feedback:

\ud83d\udcdd Observa\u00e7\u00f5es:
{{areas_desenvolvimento}}

Agradecemos seu tempo e interesse. Mantemos seu perfil em nosso banco de talentos para futuras oportunidades que sejam mais alinhadas com seu perfil.

Desejamos sucesso em sua carreira!

Atenciosamente,
{{recrutador_nome}}
{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'areas_desenvolvimento', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'email',
    situation: 'feedback_construtivo'
  },
  {
    id: 'default-contato-rapido-whatsapp',
    name: 'Contato R\u00e1pido (WhatsApp)',
    category: 'followup',
    subject: '',
    body: `Ol\u00e1 {{candidato_nome}}! \ud83d\udc4b

Sou da equipe de recrutamento da {{empresa_nome}}. Temos uma oportunidade que pode interessar voc\u00ea.

Podemos conversar? \ud83d\ude0a`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'whatsapp',
    situation: 'contato_rapido'
  },
  {
    id: 'default-lembrete-whatsapp',
    name: 'Lembrete (WhatsApp)',
    category: 'followup',
    subject: '',
    body: `Ol\u00e1 {{candidato_nome}}! \ud83d\udcc5

Passando para confirmar nossa conversa de hoje.

Nos vemos em breve! \ud83d\ude80`,
    variables: ['candidato_nome', 'vaga'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'whatsapp',
    situation: 'lembrete'
  },
  {
    id: 'default-triagem-whatsapp',
    name: 'Convite Triagem (WhatsApp)',
    category: 'scheduling',
    subject: '',
    body: `Ol\u00e1 {{candidato_nome}}! \ud83d\udc4b

Esperamos que esteja bem!

Estamos avan\u00e7ando no processo seletivo para {{vaga}} e gostar\u00edamos de convid\u00e1-lo(a) para uma triagem r\u00e1pida.

\ud83d\udccb *Sobre a triagem:*
\u2022 Dura\u00e7\u00e3o: 15-20 min
\u2022 Formato: Conversa com a LIA, nossa assistente

\u26a0\ufe0f *Aviso LGPD*
Antes de iniciar, voc\u00ea receber\u00e1 informa\u00e7\u00f5es sobre como seus dados ser\u00e3o tratados e os termos de uso do processo.

Podemos come\u00e7ar? Ao confirmar, a LIA iniciar\u00e1 a conversa! \ud83c\udfaf

Responda "SIM" para come\u00e7ar \ud83d\ude0a`,
    variables: ['candidato_nome', 'vaga', 'link_triagem'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'whatsapp',
    situation: 'triagem'
  },
  {
    id: 'default-agendamento-whatsapp',
    name: 'Convite Entrevista (WhatsApp)',
    category: 'scheduling',
    subject: '',
    body: `Ol\u00e1 {{candidato_nome}}! \ud83c\udf89

Parab\u00e9ns por avan\u00e7ar no processo seletivo para {{vaga}}!

Gostar\u00edamos de agendar uma entrevista {{formato_entrevista}} com voc\u00ea.

\ud83d\udcc5 *Detalhes:*
\u2022 Dura\u00e7\u00e3o: {{duracao_entrevista}} min
\u2022 Formato: {{link_entrevista}}

\ud83d\uddd3\ufe0f *Escolha seu hor\u00e1rio preferido:*
A LIA vai te mostrar as op\u00e7\u00f5es dispon\u00edveis!

\u2705 Ap\u00f3s confirmar:
\u2022 Voc\u00ea receber\u00e1 email de confirma\u00e7\u00e3o
\u2022 Convite para calend\u00e1rio
\u2022 Link da videochamada

Vamos agendar? \ud83d\ude0a`,
    variables: ['candidato_nome', 'vaga', 'formato_entrevista', 'duracao_entrevista', 'link_entrevista'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'whatsapp',
    situation: 'agendamento'
  },
  {
    id: 'default-avaliacao-tecnica-email',
    name: 'Convite Avalia\u00e7\u00e3o T\u00e9cnica (Email)',
    category: 'scheduling',
    subject: 'Pr\u00f3xima etapa: Avalia\u00e7\u00e3o T\u00e9cnica - {{vaga}}',
    body: `Ol\u00e1 {{candidato_nome}},

Parab\u00e9ns por avan\u00e7ar no processo seletivo para {{vaga}}!

Gostar\u00edamos de convid\u00e1-lo(a) para a pr\u00f3xima etapa: uma avalia\u00e7\u00e3o t\u00e9cnica.

\ud83d\udccb Sobre a avalia\u00e7\u00e3o:
\u2022 Tipo: Avalia\u00e7\u00e3o t\u00e9cnica
\u2022 Objetivo: Avaliar suas compet\u00eancias t\u00e9cnicas para a posi\u00e7\u00e3o

Aguardamos sua participa\u00e7\u00e3o!

Atenciosamente,
{{recrutador_nome}}
{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'email',
    situation: 'avaliacao_tecnica'
  },
  {
    id: 'default-proposta-email',
    name: 'Proposta de Trabalho (Email)',
    category: 'offer',
    subject: 'Proposta para {{vaga}} - {{empresa_nome}}',
    body: `Ol\u00e1 {{candidato_nome}},

Temos o prazer de informar que voc\u00ea foi aprovado(a) em nosso processo seletivo para a posi\u00e7\u00e3o de {{vaga}}!

Ap\u00f3s an\u00e1lise cuidadosa de todas as etapas, ficamos muito impressionados com seu perfil e acreditamos que voc\u00ea ser\u00e1 uma excelente adi\u00e7\u00e3o \u00e0 nossa equipe.

\ud83d\udccb Detalhes da Proposta:
\u2022 Cargo: {{vaga}}
\u2022 Tipo de contrato: {{tipo_contrato}}
\u2022 Sal\u00e1rio: {{salario}}
\u2022 Benef\u00edcios: {{beneficios}}
\u2022 Data de in\u00edcio prevista: {{data_inicio}}

Gostar\u00edamos de agendar uma conversa para discutir os detalhes da proposta e esclarecer quaisquer d\u00favidas que possa ter.

Aguardamos ansiosamente sua resposta!

Atenciosamente,
{{recrutador_nome}}
{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome', 'tipo_contrato', 'salario', 'beneficios', 'data_inicio'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'email',
    situation: 'proposta'
  },
  {
    id: 'default-vaga-fechada-email',
    name: 'Vaga Fechada (Email)',
    category: 'rejection',
    subject: 'Atualiza\u00e7\u00e3o do Processo Seletivo - {{vaga}}',
    body: `Ol\u00e1 {{candidato_nome}},

Esperamos que esteja bem!

Gostar\u00edamos de agradecer o seu interesse e participa\u00e7\u00e3o no processo seletivo para a posi\u00e7\u00e3o de {{vaga}} na {{empresa_nome}}.

Informamos que a vaga foi preenchida. No entanto, mantemos seu perfil em nosso banco de talentos e entraremos em contato caso surjam novas oportunidades compat\u00edveis com sua experi\u00eancia.

Desejamos muito sucesso em sua carreira!

Atenciosamente,
{{recrutador_nome}}
{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'email',
    situation: 'vaga_fechada'
  },
  {
    id: 'default-proposta-aceita-email',
    name: 'Proposta Aceita - Boas Vindas (Email)',
    category: 'offer',
    subject: 'Bem-vindo(a) \u00e0 {{empresa_nome}}! \ud83c\udf89',
    body: `Ol\u00e1 {{candidato_nome}},

\u00c9 com grande alegria que confirmamos sua contrata\u00e7\u00e3o para a posi\u00e7\u00e3o de {{vaga}}! \ud83c\udf89

Estamos muito felizes em t\u00ea-lo(a) em nossa equipe!

\ud83d\udccb Pr\u00f3ximos passos:
\u2022 Nossa equipe de RH entrar\u00e1 em contato em breve com os detalhes do onboarding
\u2022 Data de in\u00edcio prevista: {{data_inicio}}

{{instrucoes_onboarding}}

Qualquer d\u00favida, estamos \u00e0 disposi\u00e7\u00e3o!

Bem-vindo(a) \u00e0 equipe!

Atenciosamente,
{{recrutador_nome}}
{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome', 'data_inicio', 'instrucoes_onboarding'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'email',
    situation: 'proposta_aceita'
  },
  {
    id: 'default-vaga-fechada-whatsapp',
    name: 'Vaga Fechada (WhatsApp)',
    category: 'rejection',
    subject: '',
    body: `Ol\u00e1 {{candidato_nome}}! \ud83d\udc4b

Agradecemos muito sua participa\u00e7\u00e3o no processo seletivo para {{vaga}}.

Gostar\u00edamos de informar que a vaga foi preenchida. Seu perfil est\u00e1 em nosso banco de talentos e entraremos em contato caso surjam novas oportunidades.

Desejamos sucesso em sua carreira! \ud83c\udf40

{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'whatsapp',
    situation: 'vaga_fechada'
  },
  {
    id: 'default-vaga-cancelada-email',
    name: 'Vaga Cancelada (Email)',
    category: 'rejection',
    subject: 'Atualiza\u00e7\u00e3o do Processo Seletivo - {{vaga}}',
    body: `Ol\u00e1 {{candidato_nome}},

Gostar\u00edamos de informar que o processo seletivo para a posi\u00e7\u00e3o de {{vaga}} foi encerrado.

Esta decis\u00e3o n\u00e3o est\u00e1 relacionada ao seu desempenho ou participa\u00e7\u00e3o no processo. Agradecemos sinceramente seu tempo e dedica\u00e7\u00e3o.

Seu perfil permanece em nosso banco de talentos e entraremos em contato caso surjam novas oportunidades alinhadas ao seu perfil.

Desejamos sucesso em sua carreira!

Atenciosamente,
{{recrutador_nome}}
{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'email',
    situation: 'vaga_cancelada'
  },
  {
    id: 'default-vaga-cancelada-whatsapp',
    name: 'Vaga Cancelada (WhatsApp)',
    category: 'rejection',
    subject: '',
    body: `Ol\u00e1 {{candidato_nome}}! \ud83d\udc4b

Informamos que o processo para {{vaga}} foi encerrado. Essa decis\u00e3o n\u00e3o tem rela\u00e7\u00e3o com seu desempenho.

Seu perfil permanece em nosso banco de talentos e entraremos em contato sobre novas oportunidades.

Desejamos sucesso! \ud83c\udf40`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'whatsapp',
    situation: 'vaga_cancelada'
  },
  {
    id: 'default-vaga-pausada-email',
    name: 'Vaga Pausada (Email)',
    category: 'feedback',
    subject: 'Atualiza\u00e7\u00e3o do Processo - {{vaga}}',
    body: `Ol\u00e1 {{candidato_nome}},

Gostar\u00edamos de informar que o processo seletivo para a posi\u00e7\u00e3o de {{vaga}} est\u00e1 temporariamente pausado.

Esta pausa n\u00e3o est\u00e1 relacionada ao seu desempenho no processo. Assim que tivermos atualiza\u00e7\u00f5es, entraremos em contato.

Seu perfil permanece em nossa base e voc\u00ea continua sendo considerado(a) para esta oportunidade.

Agradecemos sua compreens\u00e3o e paci\u00eancia.

Atenciosamente,
{{recrutador_nome}}
{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'email',
    situation: 'vaga_pausada'
  },
  {
    id: 'default-vaga-pausada-whatsapp',
    name: 'Vaga Pausada (WhatsApp)',
    category: 'feedback',
    subject: '',
    body: `Ol\u00e1 {{candidato_nome}}! \ud83d\udc4b

Informamos que o processo para {{vaga}} est\u00e1 temporariamente pausado. N\u00e3o se preocupe, isso n\u00e3o tem rela\u00e7\u00e3o com seu desempenho.

Assim que tivermos novidades, entraremos em contato. Seu perfil continua sendo considerado.

Agradecemos sua paci\u00eancia! \ud83d\ude4f`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'whatsapp',
    situation: 'vaga_pausada'
  },
  {
    id: 'default-vaga-retomada-email',
    name: 'Vaga Retomada (Email)',
    category: 'feedback',
    subject: 'Boas not\u00edcias! Processo reativado - {{vaga}}',
    body: `Ol\u00e1 {{candidato_nome}},

Temos boas not\u00edcias!

O processo seletivo para a posi\u00e7\u00e3o de {{vaga}} foi reativado e voc\u00ea continua sendo considerado(a).

Caso tenha alguma altera\u00e7\u00e3o em sua disponibilidade ou interesse, por favor nos avise respondendo este email.

Agradecemos sua paci\u00eancia durante o per\u00edodo de pausa.

Atenciosamente,
{{recrutador_nome}}
{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome', 'recrutador_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'email',
    situation: 'vaga_retomada'
  },
  {
    id: 'default-vaga-retomada-whatsapp',
    name: 'Vaga Retomada (WhatsApp)',
    category: 'feedback',
    subject: '',
    body: `Oi {{candidato_nome}}! \ud83c\udf89

Boas not\u00edcias! O processo para {{vaga}} foi reativado e voc\u00ea continua sendo considerado(a)!

Caso tenha mudan\u00e7as na sua disponibilidade, \u00e9 s\u00f3 me avisar.

Obrigado pela paci\u00eancia! \ud83d\ude0a`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'whatsapp',
    situation: 'vaga_retomada'
  }
]
