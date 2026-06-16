# frozen_string_literal: true

module BackgroundAgents
  class SetupJob
    include Sidekiq::Job

    sidekiq_options queue: :background_agents, retry: 3

    def perform(agent_id, account_id)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch!(account.tenant) do
        agent = BackgroundAgent.find_by(id: agent_id)
        return unless agent

        Rails.logger.info "🔄 [BackgroundAgents::SetupJob] Setting up agent #{agent.id} for job #{agent.job_id}"

        BackgroundAgents::PublishToAgentService.new(background_agent: agent).call
      end
    rescue StandardError => e
      Rails.logger.error "❌ [BackgroundAgents::SetupJob] #{e.message}"
      raise
    end
  end
end
