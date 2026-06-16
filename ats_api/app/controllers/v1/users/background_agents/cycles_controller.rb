# frozen_string_literal: true

module V1
  module Users
    module BackgroundAgents
      class CyclesController < BaseController
        before_action :require_service_token, only: %i[deliver]
        before_action :set_background_agent

        CANDIDATE_ALLOWED_KEYS = %w[
          candidate_id external_id source_provider name first_name last_name
          email title summary company city state country location
          linkedin_url linkedin_slug picture_url position_level
          experience_years estimated_age remote_work is_decision_maker
          skills experiences educations certifications awards expertise languages
          followers_count connections_count raw_profile
          score category justification strengths concerns
          requirement_coverage source_query found_in_iteration
        ].freeze

        def deliver
          cycle = @background_agent.agent_cycles.find_by(id: params[:cycle_id])
          return render_not_found("AgentCycle") unless cycle

          candidates_count = params[:candidates_count].to_i
          total_found = params[:total_found].to_i

          if candidates_count.negative? || total_found.negative?
            return render_simple_error("candidates_count and total_found must be non-negative", status: :unprocessable_entity)
          end

          metadata = safe_jsonb_param(params[:metadata])
          is_progressive = metadata["progressive_batch"].present?

          cycle.deliver!(
            candidates_count: candidates_count,
            total_found: total_found,
            execution_metadata: metadata
          )

          profiles_result = { created: 0, skipped: 0 }
          if params[:candidates].present? && cycle.sourcing.present?
            profiles_result = ::BackgroundAgents::DeliverCandidatesService.new(
              background_agent: @background_agent,
              sourcing: cycle.sourcing,
              candidates_data: sanitized_candidates_data
            ).call
          end

          unless is_progressive
            @background_agent.update!(
              total_delivered: @background_agent.agent_cycles.sum(:candidates_delivered)
            )
          end

          @background_agent.update!(
            last_run_at: Time.current,
            last_run_metadata: metadata.merge(profiles_result)
          )

          BackgroundAgentChannel.broadcast_to(
            "#{@background_agent.user_id}_agent_#{@background_agent.id}",
            { type: "cycle_delivered", cycle_id: cycle.id, cycle_number: cycle.cycle_number,
              profiles_created: profiles_result[:created], progressive: is_progressive }
          )

          render json: { success: true, cycle_id: cycle.id, **profiles_result }
        end

        def steps
          steps = @background_agent.background_agent_steps.chronological
          steps = steps.by_cycle(params[:cycle_id]) if params[:cycle_id].present?
          steps = steps.where(step: params[:step]) if params[:step].present?

          render_success(steps, serializer: BackgroundAgentStepSerializer)
        end

        def reset
          sourcing_ids = @background_agent.agent_cycles.where.not(sourcing_id: nil).pluck(:sourcing_id)

          ActiveRecord::Base.transaction do
            @background_agent.background_agent_steps.delete_all
            @background_agent.agent_feedbacks.delete_all
            @background_agent.agent_cycles.destroy_all
            Sourcing.where(id: sourcing_ids, provider: "background_agent").destroy_all if sourcing_ids.any?

            @background_agent.update!(
              total_delivered: 0,
              total_approved: 0,
              total_rejected: 0,
              consecutive_approvals: 0,
              calibration_state: "pending",
              search_history: [],
              last_run_metadata: {},
              last_run_at: nil,
              extracted_preferences: {}
            )
          end

          render json: {
            success: true,
            cleaned: {
              cycles: sourcing_ids.size,
              sourcings: sourcing_ids.size
            }
          }
        end

        private

        def sanitized_candidates_data
          Array(params[:candidates]).map do |c|
            raw = c.respond_to?(:to_unsafe_h) ? c.to_unsafe_h : c.to_h
            raw.deep_stringify_keys.slice(*CANDIDATE_ALLOWED_KEYS)
          end
        end
      end
    end
  end
end
