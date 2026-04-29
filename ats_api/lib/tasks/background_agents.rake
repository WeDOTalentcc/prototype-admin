# frozen_string_literal: true

namespace :background_agents do
  desc "Trigger a background agent manually. Usage: rake background_agents:run[AGENT_ID,ACCOUNT_ID]"
  task :run, %i[agent_id account_id] => :environment do |_t, args|
    abort "Usage: rake background_agents:run[AGENT_ID,ACCOUNT_ID]" unless args[:agent_id]

    account = if args[:account_id]
                Account.find_by(id: args[:account_id])
              else
                Account.first
              end
    abort "Account not found" unless account

    Apartment::Tenant.switch(account.tenant) do
      agent = BackgroundAgent.where(is_deleted: false).find_by(id: args[:agent_id])
      abort "Agent ##{args[:agent_id]} not found (or deleted) in tenant #{account.tenant}" unless agent

      Rails.logger.info "🚀 Triggering agent ##{agent.id} — #{agent.name} | Job: #{agent.job&.title || 'N/A'} | Status: #{agent.status} | Mode: #{agent.mode} | Account: #{account.tenant} | Remaining: #{agent.remaining_today}"

      unless agent.status == "active"
        abort "Agent is '#{agent.status}' — activate manually before running" unless ENV["FORCE_ACTIVATE"] == "true"

        agent.resume!
        Rails.logger.info "✅ Agent activated via FORCE_ACTIVATE"
      end

      result = BackgroundAgents::PublishToAgentService.new(background_agent: agent).call

      if result[:success]
        Rails.logger.info "✅ Published! Cycle ##{result[:cycle_number]} (id: #{result[:cycle_id]})"
      else
        Rails.logger.error "❌ Failed: #{result[:error]}"
      end
    end
  end
end
