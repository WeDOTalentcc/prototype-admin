# frozen_string_literal: true

module V1
  module Users
    class AgentFeedbacksController < ApplicationController
      include RenderDefault

      BULK_LIMIT = 100

      before_action :authorize_request
      before_action :set_background_agent

      def create
        result = BackgroundAgents::ProcessFeedbackService.new(
          background_agent: @background_agent,
          feedbacks: feedback_params
        ).call

        return render_simple_error(result[:error], status: :unprocessable_entity) unless result[:success]

        render json: result.slice(:processed, :calibration_state, :mode), status: :created
      end

      def bulk
        feedbacks = bulk_feedback_params
        if feedbacks.size > BULK_LIMIT
          return render_simple_error("Maximum #{BULK_LIMIT} feedbacks per request", status: :unprocessable_entity)
        end

        result = BackgroundAgents::ProcessFeedbackService.new(
          background_agent: @background_agent,
          feedbacks: feedbacks
        ).call

        return render_simple_error(result[:error], status: :unprocessable_entity) unless result[:success]

        render json: result.slice(:processed, :calibration_state, :mode), status: :created
      end

      private

      def set_background_agent
        @background_agent = BackgroundAgent.where(account: @current_user.account, is_deleted: false)
                                           .find_by(id: params[:background_agent_id])
        render_not_found("BackgroundAgent") unless @background_agent
      end

      def feedback_params
        fp = params[:feedback] || params[:agent_feedback]
        raise ActionController::ParameterMissing, :feedback if fp.blank?

        data = fp.permit(
          :sourced_profile_sourcing_id, :agent_candidate_id,
          :agent_cycle_id, :action, :status, :reason
        ).to_h

        data["sourced_profile_sourcing_id"] ||= data.delete("agent_candidate_id")
        data["action"] ||= data.delete("status")
        data.except!("agent_candidate_id", "status")

        [data.symbolize_keys]
      end

      def bulk_feedback_params
        params.require(:feedbacks).map do |f|
          f.permit(:sourced_profile_sourcing_id, :agent_cycle_id, :action, :reason).to_h
        end
      end
    end
  end
end
