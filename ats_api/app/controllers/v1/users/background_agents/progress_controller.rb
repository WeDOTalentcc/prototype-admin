# frozen_string_literal: true

module V1
  module Users
    module BackgroundAgents
      class ProgressController < BaseController
        before_action :require_service_token
        before_action :set_background_agent

        def report
          step_record = @background_agent.background_agent_steps.create!(
            agent_cycle_id: params[:cycle_id],
            step: params[:step],
            status: params[:status] || "running",
            message: params[:message]&.to_s&.truncate(500),
            details: safe_jsonb_param(params[:details]),
            narrative: narrative_params,
            iteration_number: params[:iteration_number]
          )

          BackgroundAgentChannel.broadcast_to(
            "#{@background_agent.user_id}_agent_#{@background_agent.id}",
            {
              type: "progress",
              agent_id: @background_agent.id,
              cycle_id: params[:cycle_id],
              step_id: step_record.id,
              step: step_record.step,
              status: step_record.status,
              message: step_record.message,
              details: step_record.details,
              narrative: step_record.narrative,
              iteration_number: step_record.iteration_number,
              timestamp: step_record.created_at.iso8601
            }.compact
          )
          render json: { success: true, step_id: step_record.id }
        end

        def log_search_iteration
          @background_agent.log_search_iteration!(iteration_params.to_h)
          render json: { success: true, history_size: @background_agent.search_history.size }
        end

        private

        def iteration_params
          params.permit(:iteration_number, :query_used, :results_count, :selected_count, :strategy)
        end

        def narrative_params
          return nil unless params[:narrative].present?

          raw = params[:narrative].respond_to?(:to_unsafe_h) ? params[:narrative].to_unsafe_h : params[:narrative].to_h
          return nil if raw.to_json.bytesize > 10_000

          {
            summary: raw[:summary]&.to_s&.truncate(500),
            detail: raw[:detail]&.to_s&.truncate(1000),
            action: raw[:action]&.to_s&.truncate(200),
            sentiment: raw[:sentiment]&.to_s,
            metrics: raw[:metrics].is_a?(Hash) ? raw[:metrics].deep_stringify_keys : nil,
            learnings_card: raw[:learnings_card].is_a?(Hash) ? raw[:learnings_card].deep_stringify_keys : nil
          }.compact.presence
        end
      end
    end
  end
end
