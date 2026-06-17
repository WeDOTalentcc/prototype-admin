// Serviço de integrações para envio de webhooks (Teams e outros)

type WebhookData = Record<string, unknown>

interface TeamsMessage {
  "@type": string
  "@context": string
  text: string
  themeColor: string
}

interface WebhookPayload {
  event: string
  data: WebhookData
  timestamp: string
  source: 'lia-platform'
}

interface Integration {
  id: string
  name: string
  type: 'teams' | 'discord' | 'email'
  webhookUrl: string
  events: string[]
  active: boolean
  templates: Record<string, string>
}

class IntegrationsService {
  private integrations: Integration[] = []

  async sendWebhook(integrationId: string, event: string, data: WebhookData): Promise<boolean> {
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

    void payload

    try {
      await new Promise(resolve => setTimeout(resolve, 500))

      const success = Math.random() > 0.05

      return success
    } catch (error) {
      return false
    }
  }

  private formatMessage(integration: Integration, event: string, data: WebhookData): TeamsMessage | { text: string } {
    const template = integration.templates[event] || this.getDefaultTemplate(event)

    switch (integration.type) {
      case 'teams':
        return this.formatTeamsMessage(template, data)
      default:
        return { text: this.interpolateTemplate(template, data) }
    }
  }

  private formatTeamsMessage(template: string, data: WebhookData): TeamsMessage {
    return {
      "@type": "MessageCard",
      "@context": "http://schema.org/extensions",
      text: this.interpolateTemplate(template, data),
      themeColor: "0076D7"
    }
  }

  private interpolateTemplate(template: string, data: WebhookData): string {
    return template.replace(/\{(\w+)\}/g, (match, key) => {
      return String(data[key] ?? match)
    })
  }

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

  async notifyNewCandidate(candidateData: WebhookData) {
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

  async notifyApproval(approvalData: WebhookData) {
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

  async notifyBatchApproval(batchData: WebhookData) {
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

  async notifyNewNote(noteData: WebhookData) {
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

  async notifyMention(mentionData: WebhookData) {
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

  async testIntegration(integrationId: string): Promise<boolean> {
    return this.sendWebhook(integrationId, 'test', {
      test: true,
      message: 'Teste de conectividade'
    })
  }
}

export const integrationsService = new IntegrationsService()

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
