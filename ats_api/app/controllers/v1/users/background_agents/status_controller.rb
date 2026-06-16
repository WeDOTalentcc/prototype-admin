# frozen_string_literal: true

module V1
  module Users
    module BackgroundAgents
      class StatusController < BaseController
        before_action :require_service_token, only: %i[runnable search_context update_preferences update_status]
        before_action :set_background_agent, only: %i[pause resume stop search_context update_preferences update_status]

        def pause
          @background_agent.pause!
          render_success(@background_agent, serializer: BackgroundAgentSerializer)
        end

        def resume
          @background_agent.resume!
          render_success(@background_agent, serializer: BackgroundAgentSerializer)
        end

        def stop
          @background_agent.stop!
          render_success(@background_agent, serializer: BackgroundAgentSerializer)
        end

        def runnable
          agents = BackgroundAgent.runnable.includes(:job, :user)
          render json: agents.map { |a| build_runnable_payload(a) }
        end

        def search_context
          context = ::BackgroundAgents::BuildSearchContextService.new(
            background_agent: @background_agent
          ).call

          render json: context
        end

        def update_preferences
          preferences = params[:preferences]
          return render_simple_error("preferences is required", status: :unprocessable_entity) if preferences.blank?

          @background_agent.update!(extracted_preferences: safe_jsonb_param(preferences))
          render json: { success: true }
        end

        def update_status
          status = params[:status].to_s
          unless BackgroundAgent::STATUSES.include?(status)
            return render_simple_error("Invalid status. Allowed: #{BackgroundAgent::STATUSES.join(', ')}", status: :unprocessable_entity)
          end

          @background_agent.update!(status: status)
          render json: { success: true }
        end

        private

        def build_runnable_payload(agent)
          {
            id: agent.id,
            job_id: agent.job_id,
            list_id: agent.list_id,
            target_type: agent.target_type,
            user_id: agent.user_id,
            account_id: agent.account_id,
            name: agent.name,
            criteria_text: agent.criteria_text,
            criteria_structured: agent.criteria_structured,
            calibration_state: agent.calibration_state,
            mode: agent.mode,
            sources: agent.sources,
            min_score_threshold: agent.min_score_threshold,
            remaining_today: agent.remaining_today,
            search_iteration_config: agent.search_iteration_config,
            extracted_preferences: agent.extracted_preferences
          }
        end
      end
    end
  end
end
