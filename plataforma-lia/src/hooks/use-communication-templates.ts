"use client"

import { useState, useEffect, useCallback } from 'react'

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

interface UseCommunicationTemplatesOptions {
  channel?: TemplateChannel
  situation?: TemplateSituation
  autoLoad?: boolean
}

interface UseCommunicationTemplatesReturn {
  templates: CommunicationTemplate[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
  getTemplatesBySituation: (situation: TemplateSituation) => CommunicationTemplate[]
  getTemplatesByChannel: (channel: TemplateChannel) => CommunicationTemplate[]
}

const DEFAULT_TEMPLATES: CommunicationTemplate[] = [
  {
    id: 'default-contato-inicial-email',
    name: 'Contato Inicial (Email)',
    category: 'followup',
    subject: 'Oportunidade - {{vaga}}',
    body: `Olá {{candidato_nome}},

Esperamos que esteja bem!

Identificamos seu perfil e gostaríamos de conversar sobre uma excelente oportunidade para a posição de {{vaga}}.

Sua experiência e qualificações são muito alinhadas com o que buscamos.

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
    body: `Olá {{candidato_nome}},

Espero que esteja bem! Gostaria de fazer um acompanhamento sobre sua candidatura para a posição de {{vaga}}.

Tem alguma dúvida sobre o processo ou a vaga?

Fico à disposição.

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
    subject: 'Próximo passo: Avaliação - {{vaga}}',
    body: `Olá {{candidato_nome}},

Esperamos que esteja bem!

Estamos avançando em nosso processo seletivo para a posição de {{vaga}} e gostaríamos de convidá-lo(a) para a próxima etapa: uma triagem rápida com a nossa assistente LIA.

📋 Sobre a triagem:
• Duração estimada: 15-20 minutos
• Formato: Conversa por chat ou WhatsApp com a LIA
• Objetivo: Conhecer melhor sua forma de pensar e resolver problemas

🔗 Para iniciar, escolha uma das opções:
• INICIAR VIA CHAT WEB - Clique aqui para conversar pelo navegador
• INICIAR VIA WHATSAPP - Clique aqui para conversar pelo WhatsApp

⚠️ Ao iniciar, você será apresentado aos termos de uso e política de privacidade (LGPD).

Essa avaliação nos ajuda a entender melhor seu perfil e garantir que a vaga seja compatível com suas habilidades e expectativas.

Qualquer dúvida, estamos à disposição!

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
    body: `Olá {{candidato_nome}},

Parabéns por avançar no processo seletivo para {{vaga}}! 🎉

Gostaríamos de convidá-lo(a) para a próxima etapa: uma entrevista {{formato_entrevista}}.

📅 Detalhes da Entrevista:
• Tipo: Entrevista {{formato_entrevista}}
• Duração: {{duracao_entrevista}} minutos
• Plataforma: {{link_entrevista}}
• Entrevistador: {{entrevistador_nome}}

🗓️ Escolha o melhor horário:
Clique no link abaixo para visualizar as disponibilidades e escolher o horário que melhor funciona para você:

{{link_calendario}}

Após a confirmação, você receberá:
✅ Email de confirmação com todos os detalhes
✅ Convite do Outlook/Google Calendar
✅ Link da plataforma de vídeo (se aplicável)

Qualquer dúvida, estamos à disposição!

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
    subject: 'Atualização - Processo Seletivo {{vaga}}',
    body: `Olá {{candidato_nome}},

Esperamos que esteja bem!

É com grande satisfação que compartilhamos o feedback sobre sua participação no processo seletivo para {{vaga}}.

✅ Pontos Positivos:
• Sua experiência e conhecimento técnico impressionaram nossa equipe
• Demonstrou excelente comunicação e clareza nas respostas
• Alinhamento com os valores e cultura da empresa

📈 Próximos Passos:
{{proximos_passos}}

Agradecemos seu interesse e dedicação ao processo!

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
    body: `Olá {{candidato_nome}},

Agradecemos sua participação no processo seletivo para {{vaga}}.

Gostaríamos de compartilhar nosso feedback:

📝 Observações:
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
    name: 'Contato Rápido (WhatsApp)',
    category: 'followup',
    subject: '',
    body: `Olá {{candidato_nome}}! 👋

Sou da equipe de recrutamento da {{empresa_nome}}. Temos uma oportunidade que pode interessar você.

Podemos conversar? 😊`,
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
    body: `Olá {{candidato_nome}}! 📅

Passando para confirmar nossa conversa de hoje.

Nos vemos em breve! 🚀`,
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
    body: `Olá {{candidato_nome}}! 👋

Esperamos que esteja bem!

Estamos avançando no processo seletivo para {{vaga}} e gostaríamos de convidá-lo(a) para uma triagem rápida.

📋 *Sobre a triagem:*
• Duração: 15-20 min
• Formato: Conversa com a LIA, nossa assistente

⚠️ *Aviso LGPD*
Antes de iniciar, você receberá informações sobre como seus dados serão tratados e os termos de uso do processo.

Podemos começar? Ao confirmar, a LIA iniciará a conversa! 🎯

Responda "SIM" para começar 😊`,
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
    body: `Olá {{candidato_nome}}! 🎉

Parabéns por avançar no processo seletivo para {{vaga}}!

Gostaríamos de agendar uma entrevista {{formato_entrevista}} com você.

📅 *Detalhes:*
• Duração: {{duracao_entrevista}} min
• Formato: {{link_entrevista}}

🗓️ *Escolha seu horário preferido:*
A LIA vai te mostrar as opções disponíveis!

✅ Após confirmar:
• Você receberá email de confirmação
• Convite para calendário
• Link da videochamada

Vamos agendar? 😊`,
    variables: ['candidato_nome', 'vaga', 'formato_entrevista', 'duracao_entrevista', 'link_entrevista'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'whatsapp',
    situation: 'agendamento'
  },
  {
    id: 'default-avaliacao-tecnica-email',
    name: 'Convite Avaliação Técnica (Email)',
    category: 'scheduling',
    subject: 'Próxima etapa: Avaliação Técnica - {{vaga}}',
    body: `Olá {{candidato_nome}},

Parabéns por avançar no processo seletivo para {{vaga}}!

Gostaríamos de convidá-lo(a) para a próxima etapa: uma avaliação técnica.

📋 Sobre a avaliação:
• Tipo: Avaliação técnica
• Objetivo: Avaliar suas competências técnicas para a posição

Aguardamos sua participação!

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
    body: `Olá {{candidato_nome}},

Temos o prazer de informar que você foi aprovado(a) em nosso processo seletivo para a posição de {{vaga}}!

Após análise cuidadosa de todas as etapas, ficamos muito impressionados com seu perfil e acreditamos que você será uma excelente adição à nossa equipe.

📋 Detalhes da Proposta:
• Cargo: {{vaga}}
• Tipo de contrato: {{tipo_contrato}}
• Salário: {{salario}}
• Benefícios: {{beneficios}}
• Data de início prevista: {{data_inicio}}

Gostaríamos de agendar uma conversa para discutir os detalhes da proposta e esclarecer quaisquer dúvidas que possa ter.

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
    subject: 'Atualização do Processo Seletivo - {{vaga}}',
    body: `Olá {{candidato_nome}},

Esperamos que esteja bem!

Gostaríamos de agradecer o seu interesse e participação no processo seletivo para a posição de {{vaga}} na {{empresa_nome}}.

Informamos que a vaga foi preenchida. No entanto, mantemos seu perfil em nosso banco de talentos e entraremos em contato caso surjam novas oportunidades compatíveis com sua experiência.

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
    subject: 'Bem-vindo(a) à {{empresa_nome}}! 🎉',
    body: `Olá {{candidato_nome}},

É com grande alegria que confirmamos sua contratação para a posição de {{vaga}}! 🎉

Estamos muito felizes em tê-lo(a) em nossa equipe!

📋 Próximos passos:
• Nossa equipe de RH entrará em contato em breve com os detalhes do onboarding
• Data de início prevista: {{data_inicio}}

{{instrucoes_onboarding}}

Qualquer dúvida, estamos à disposição!

Bem-vindo(a) à equipe!

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
    body: `Olá {{candidato_nome}}! 👋

Agradecemos muito sua participação no processo seletivo para {{vaga}}.

Gostaríamos de informar que a vaga foi preenchida. Seu perfil está em nosso banco de talentos e entraremos em contato caso surjam novas oportunidades.

Desejamos sucesso em sua carreira! 🍀

{{empresa_nome}}`,
    variables: ['candidato_nome', 'vaga', 'empresa_nome'],
    isActive: true,
    lastUpdated: new Date().toISOString().split('T')[0],
    channel: 'whatsapp',
    situation: 'vaga_fechada'
  }
]

export function useCommunicationTemplates(options: UseCommunicationTemplatesOptions = {}): UseCommunicationTemplatesReturn {
  const { channel, situation, autoLoad = true } = options
  
  const [templates, setTemplates] = useState<CommunicationTemplate[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchTemplates = useCallback(async () => {
    setLoading(true)
    setError(null)
    
    try {
      const params = new URLSearchParams()
      if (channel) params.set('channel', channel)
      
      const queryString = params.toString()
      const url = `/api/backend-proxy/email-templates${queryString ? `?${queryString}` : ''}`
      
      const response = await fetch(url)
      
      if (response.ok) {
        const result = await response.json()
        const templatesArray = result.items || (Array.isArray(result) ? result : [])
        
        const mappedTemplates: CommunicationTemplate[] = templatesArray.map((t: Record<string, unknown>) => ({
          id: t.id,
          name: t.name,
          category: t.category || 'followup',
          subject: t.subject || '',
          body: t.body || t.body_text || (t.body_html ? stripHtmlTags(t.body_html) : ''),
          variables: t.variables || [],
          isActive: t.is_active ?? true,
          lastUpdated: t.updated_at || t.last_updated || new Date().toISOString().split('T')[0],
          channel: t.channel || 'email',
          situation: t.situation || ''
        }))
        
        if (mappedTemplates.length > 0) {
          setTemplates(mappedTemplates)
        } else {
          const filteredDefaults = channel 
            ? DEFAULT_TEMPLATES.filter(t => t.channel === channel)
            : DEFAULT_TEMPLATES
          setTemplates(filteredDefaults)
        }
      } else {
        const filteredDefaults = channel 
          ? DEFAULT_TEMPLATES.filter(t => t.channel === channel)
          : DEFAULT_TEMPLATES
        setTemplates(filteredDefaults)
      }
    } catch (err) {
      setError('Erro ao carregar templates')
      const filteredDefaults = channel 
        ? DEFAULT_TEMPLATES.filter(t => t.channel === channel)
        : DEFAULT_TEMPLATES
      setTemplates(filteredDefaults)
    } finally {
      setLoading(false)
    }
  }, [channel])

  useEffect(() => {
    if (autoLoad) {
      fetchTemplates()
    }
  }, [autoLoad, fetchTemplates])

  const getTemplatesBySituation = useCallback((sit: TemplateSituation): CommunicationTemplate[] => {
    return templates.filter(t => t.situation === sit && t.isActive)
  }, [templates])

  const getTemplatesByChannel = useCallback((ch: TemplateChannel): CommunicationTemplate[] => {
    return templates.filter(t => t.channel === ch && t.isActive)
  }, [templates])

  return {
    templates: situation ? templates.filter(t => t.situation === situation) : templates,
    loading,
    error,
    refetch: fetchTemplates,
    getTemplatesBySituation,
    getTemplatesByChannel
  }
}

function stripHtmlTags(html: string): string {
  if (!html) return ''
  const isHtml = /<[a-z][\s\S]*>/i.test(html)
  if (!isHtml) return html
  
  const text = html
    .replace(/{{#if\s+\w+}}/gi, '')
    .replace(/{{\/if}}/gi, '')
    .replace(/<style[^>]*>[\s\S]*?<\/style>/gi, '')
    .replace(/<script[^>]*>[\s\S]*?<\/script>/gi, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/p>/gi, '\n\n')
    .replace(/<p[^>]*>/gi, '')
    .replace(/<\/div>/gi, '\n')
    .replace(/<div[^>]*>/gi, '')
    .replace(/<\/li>/gi, '\n')
    .replace(/<li[^>]*>/gi, '• ')
    .replace(/<\/ul>/gi, '\n')
    .replace(/<ul[^>]*>/gi, '')
    .replace(/<\/ol>/gi, '\n')
    .replace(/<ol[^>]*>/gi, '')
    .replace(/<\/h[1-6]>/gi, '\n\n')
    .replace(/<h[1-6][^>]*>/gi, '')
    .replace(/<\/?(strong|b)[^>]*>/gi, '')
    .replace(/<\/?(em|i)[^>]*>/gi, '')
    .replace(/<a[^>]*href="([^"]*)"[^>]*>([^<]*)<\/a>/gi, '$2')
    .replace(/<img[^>]*alt="([^"]*)"[^>]*\/?>/gi, '$1')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&rsquo;/g, "'")
    .replace(/&lsquo;/g, "'")
    .replace(/&rdquo;/g, '"')
    .replace(/&ldquo;/g, '"')
    .replace(/&mdash;/g, '—')
    .replace(/&ndash;/g, '–')
    .replace(/&#\d+;/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/[ \t]+/g, ' ')
    .replace(/\n /g, '\n')
    .replace(/ \n/g, '\n')
    .trim()
  
  return text
}

export { DEFAULT_TEMPLATES }
