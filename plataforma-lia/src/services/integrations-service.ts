// Serviço de integrações para envio de webhooks Slack/Teams

interface WebhookPayload {
  event: string
  data: any
  timestamp: string
  source: 'lia-platform'
}

interface Integration {
  id: string
  name: string
  type: 'slack' | 'teams' | 'discord' | 'email'
  webhookUrl: string
  events: string[]
  active: boolean
  templates: Record<string, string>
}

class IntegrationsService {
  private integrations: Integration[] = []

  // Simular envio de webhook
  async sendWebhook(integrationId: string, event: string, data: any): Promise<boolean> {
    const integration = this.integrations.find(i => i.id === integrationId)

    if (!integration || !integration.active || !integration.events.includes(event)) {
      return false
    }

    const payload: WebhookPayload = {
      event,
      data,
      timestamp: new Date().toISOString(),
      source: 'lia-platform'
    }

    try {
      // Simular chamada HTTP para webhook

      // Em produção, seria algo como:
      // const response = await fetch(integration.webhookUrl, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify(this.formatMessage(integration, event, data))
      // })

      // Simular delay de rede
      await new Promise(resolve => setTimeout(resolve, 500))

      // Simular 95% de sucesso
      const success = Math.random() > 0.05

      if (success) {
      } else {
      }

      return success
    } catch (error) {
      return false
    }
  }

  // Formatar mensagem baseada no template e tipo de integração
  private formatMessage(integration: Integration, event: string, data: any): any {
    const template = integration.templates[event] || this.getDefaultTemplate(event)

    switch (integration.type) {
      case 'slack':
        return this.formatSlackMessage(template, data)
      case 'teams':
        return this.formatTeamsMessage(template, data)
      default:
        return { text: this.interpolateTemplate(template, data) }
    }
  }

  // Formato para Slack
  private formatSlackMessage(template: string, data: any) {
    return {
      text: this.interpolateTemplate(template, data),
      blocks: [
        {
          type: "section",
          text: {
            type: "mrkdwn",
            text: this.interpolateTemplate(template, data)
          }
        }
      ]
    }
  }

  // Formato para Teams
  private formatTeamsMessage(template: string, data: any) {
    return {
      "@type": "MessageCard",
      "@context": "http://schema.org/extensions",
      text: this.interpolateTemplate(template, data),
      themeColor: "0076D7"
    }
  }

  // Interpolação de variáveis no template
  private interpolateTemplate(template: string, data: any): string {
    return template.replace(/\{(\w+)\}/g, (match, key) => {
      return data[key] || match
    })
  }

  // Templates padrão para cada evento
  private getDefaultTemplate(event: string): string {
    const templates = {
      novo_candidato: "🎯 Novo candidato: {candidate_name} se candidatou para {job_title}",
      aprovacao: "✅ {candidate_name} foi aprovado por {approver_name}",
      aprovacao_lote: "📦 Aprovação em lote: {approved_count} aprovados, {rejected_count} rejeitados",
      nova_nota: "💬 Nova nota sobre {candidate_name} por {author_name}",
      mencao: "👋 Você foi mencionado em uma nota sobre {candidate_name}",
      entrevista_agendada: "📅 Entrevista agendada com {candidate_name} para {interview_date}",
      relatorio_semanal: "📊 Relatório semanal: {total_candidates} candidatos processados"
    }

    return templates[event as keyof typeof templates] || "Evento: {event}"
  }

  // Eventos específicos da plataforma
  async notifyNewCandidate(candidateData: any) {
    const activeIntegrations = this.integrations.filter(i =>
      i.active && i.events.includes('novo_candidato')
    )

    const results = await Promise.all(
      activeIntegrations.map(integration =>
        this.sendWebhook(integration.id, 'novo_candidato', candidateData)
      )
    )

    return results
  }

  async notifyApproval(approvalData: any) {
    const activeIntegrations = this.integrations.filter(i =>
      i.active && i.events.includes('aprovacao')
    )

    const results = await Promise.all(
      activeIntegrations.map(integration =>
        this.sendWebhook(integration.id, 'aprovacao', approvalData)
      )
    )

    return results
  }

  async notifyBatchApproval(batchData: any) {
    const activeIntegrations = this.integrations.filter(i =>
      i.active && i.events.includes('aprovacao_lote')
    )

    const results = await Promise.all(
      activeIntegrations.map(integration =>
        this.sendWebhook(integration.id, 'aprovacao_lote', batchData)
      )
    )

    return results
  }

  async notifyNewNote(noteData: any) {
    const activeIntegrations = this.integrations.filter(i =>
      i.active && i.events.includes('nova_nota')
    )

    const results = await Promise.all(
      activeIntegrations.map(integration =>
        this.sendWebhook(integration.id, 'nova_nota', noteData)
      )
    )

    return results
  }

  async notifyMention(mentionData: any) {
    const activeIntegrations = this.integrations.filter(i =>
      i.active && i.events.includes('mencao')
    )

    const results = await Promise.all(
      activeIntegrations.map(integration =>
        this.sendWebhook(integration.id, 'mencao', mentionData)
      )
    )

    return results
  }

  // Gerenciamento de integrações
  addIntegration(integration: Integration) {
    this.integrations.push(integration)
  }

  removeIntegration(integrationId: string) {
    this.integrations = this.integrations.filter(i => i.id !== integrationId)
  }

  updateIntegration(integrationId: string, updates: Partial<Integration>) {
    const index = this.integrations.findIndex(i => i.id === integrationId)
    if (index !== -1) {
      this.integrations[index] = { ...this.integrations[index], ...updates }
    }
  }

  getIntegrations(): Integration[] {
    return this.integrations
  }

  getActiveIntegrations(): Integration[] {
    return this.integrations.filter(i => i.active)
  }

  // Teste de conectividade
  async testIntegration(integrationId: string): Promise<boolean> {
    return this.sendWebhook(integrationId, 'test', {
      test: true,
      message: 'Teste de conectividade da LIA Platform'
    })
  }
}

// Singleton instance
export const integrationsService = new IntegrationsService()

// Inicializar com integrações de exemplo
integrationsService.addIntegration({
  id: 'slack-recruiting',
  name: 'Canal #recrutamento',
  type: 'slack',
  webhookUrl: 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX',
  events: ['novo_candidato', 'aprovacao', 'nova_nota', 'mencao'],
  active: true,
  templates: {
    novo_candidato: '🎯 *Novo candidato!*\n\n*Nome:* {candidate_name}\n*Vaga:* {job_title}\n*Score LIA:* {lia_score}%\n*Match:* {match_score}%\n\n<{candidate_url}|Ver perfil completo>',
    aprovacao: '✅ *Candidato aprovado!*\n\n*Nome:* {candidate_name}\n*Vaga:* {job_title}\n*Aprovado por:* {approver_name}\n*Data:* {approval_date}\n\n💬 *Comentário:* "{approval_comment}"'
  }
})

integrationsService.addIntegration({
  id: 'teams-rh',
  name: 'Equipe RH',
  type: 'teams',
  webhookUrl: 'https://outlook.office.com/webhook/xxxxx/IncomingWebhook/yyyyy',
  events: ['aprovacao_lote', 'relatorio_semanal'],
  active: true,
  templates: {
    aprovacao_lote: '📦 **Aprovação em lote realizada**\n\n**Processado por:** {approver_name}\n**Aprovados:** {approved_count}\n**Rejeitados:** {rejected_count}\n**Movidos:** {moved_count}\n\n**Comentário:** "{batch_comment}"'
  }
})

export default integrationsService
