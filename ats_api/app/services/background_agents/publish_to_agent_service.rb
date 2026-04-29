# frozen_string_literal: true

module BackgroundAgents
  class PublishToAgentService
    def initialize(background_agent:)
      @agent = background_agent
    end

    def call
      return error("Agent is not active") unless @agent.status == "active"
      return error("No remaining quota today") if @agent.remaining_today.zero?
      return error("Cycle already running") if @agent.current_cycle.present?

      cycle = create_cycle
      publish_message(cycle)

      { success: true, cycle_id: cycle.id, cycle_number: cycle.cycle_number }
    rescue StandardError => e
      Rails.logger.error "[BackgroundAgents::PublishToAgentService] #{e.message}"
      error(e.message)
    end

    private

    def create_cycle
      sourcing = create_sourcing

      @agent.agent_cycles.create!(
        sourcing: sourcing,
        cycle_number: @agent.next_cycle_number,
        status: "running"
      )
    end

    def create_sourcing
      Sourcing.create!(
        user_id: @agent.user_id,
        account_id: @agent.account_id,
        job_id: @agent.job_id,
        uid: SecureRandom.uuid,
        query: @agent.criteria_text || @agent.target_name,
        provider: "background_agent",
        status: "processing",
        parameters: {
          background_agent_id: @agent.id,
          target_type: @agent.target_type,
          list_id: @agent.list_id,
          sources: @agent.sources,
          min_score: @agent.min_score_threshold
        }
      )
    end

    def publish_message(cycle)
      context = BuildSearchContextService.new(background_agent: @agent).call

      payload = {
        operation: "execute_intelligent_search",
        background_agent_id: @agent.id,
        cycle_id: cycle.id,
        sourcing_id: cycle.sourcing_id,
        account_id: @agent.account_id,
        user_id: @agent.user_id,
        auth: {
          one_time_token: JsonWebToken.encode_ott(account_id: @agent.account_id, user_id: @agent.user_id),
          exchange_url: "#{api_base_url}/v1/agent_tokens/exchange",
          api_base_url: api_base_url
        },
        context: context
      }

      RabbitMqPublisher.publish(
        exchange_name: "background_agents",
        routing_key: "background_agents.search",
        payload: payload
      )
    end

    def api_base_url
      ENV.fetch("API_BASE_URL", "http://localhost:3000")
    end

    def error(message)
      { success: false, error: message }
    end
  end
end
