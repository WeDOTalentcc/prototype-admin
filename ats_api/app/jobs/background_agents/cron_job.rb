# frozen_string_literal: true

module BackgroundAgents
  class CronJob
    include Sidekiq::Job

    sidekiq_options queue: :background_agents, retry: 1

    def perform(account_id = nil)
      if account_id
        process_single_account(account_id)
      else
        dispatch_per_account
      end
    end

    private

    def dispatch_per_account
      Account.pluck(:id).each do |id|
        BackgroundAgents::CronJob.perform_async(id)
      end
    end

    def process_single_account(account_id)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch!(account.tenant) do
        process_agents
      end
    rescue StandardError => e
      Rails.logger.error "[BackgroundAgents::CronJob] Account #{account_id}: #{e.message}"
    end

    def process_agents
      BackgroundAgent.runnable.find_each do |agent|
        auto_pause_if_needed(agent)
        next unless agent.status == "active"

        result = BackgroundAgents::PublishToAgentService.new(background_agent: agent).call

        if result[:success]
          Rails.logger.info "[BackgroundAgents::CronJob] Agent #{agent.id} cycle #{result[:cycle_number]} published"
        else
          Rails.logger.warn "[BackgroundAgents::CronJob] Agent #{agent.id} skipped: #{result[:error]}"
        end
      end
    end

    def auto_pause_if_needed(agent)
      return unless agent.should_auto_pause?

      agent.pause!
      Rails.logger.info "[BackgroundAgents::CronJob] Agent #{agent.id} auto-paused (no interaction for #{agent.auto_pause_days} days)"
    end
  end
end
