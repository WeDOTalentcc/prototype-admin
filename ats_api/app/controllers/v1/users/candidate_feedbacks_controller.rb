# frozen_string_literal: true

module V1
  module Users
    class CandidateFeedbacksController < ApplicationController
      include SearchRenderer
      include RenderDefault
      include SearchParams

      before_action :authorize_request
      before_action :set_feedback, only: [ :destroy ]

      def index
        params[:where] = build_base_filters

        perform_search(
          model: CandidateFeedback,
          serializer: CandidateFeedbackSerializer
        )
      end

      def create
        result = upsert_feedback

        return render_failure(result) unless result[:success]

        render_feedback_success(result)
      end

      def destroy
        @feedback.soft_delete!

        render_success(
          @feedback,
          serializer: CandidateFeedbackSerializer,
          meta: { message: "Feedback removed successfully" }
        )
      rescue StandardError => e
        render_error({ errors: [ "Error removing feedback: #{e.message}" ] })
      end

      private

      def build_base_filters
        filters = parse_json_param(params[:where]) || {}
        filters[:is_deleted] = false if filters[:is_deleted].nil?
        filters[:account_id] = @current_user.account_id
        filters
      end

      def set_feedback
        @feedback = find_feedback_by_id || find_feedback_by_where
        return if @feedback

        render_not_found("CandidateFeedback")
      end

      def find_feedback_by_id
        return unless params[:id].present?

        CandidateFeedback.find_by(
          id: params[:id],
          account_id: @current_user.account_id,
          is_deleted: false
        )
      end

      def find_feedback_by_where
        return unless params[:where].present?

        where_filters = build_base_filters
        CandidateFeedback.where(where_filters).order(created_at: :desc).first
      end

      def upsert_feedback
        CandidateFeedbacks::UpsertService.call(
          sourcing_id: feedback_params[:sourcing_id],
          apply_id: feedback_params[:apply_id],
          candidate_id: feedback_params[:candidate_id],
          sourced_profile_sourcing_id: feedback_params[:sourced_profile_sourcing_id],
          user: @current_user,
          feedback_type: feedback_params[:feedback_type],
          job_id: feedback_params[:job_id],
          reference_type: feedback_params[:reference_type],
          reference_id: feedback_params[:reference_id],
          reason: feedback_params[:reason]
        )
      end

      def render_feedback_success(result)
        status = result[:action] == :created ? :created : :ok

        render_success(
          result[:feedback],
          serializer: CandidateFeedbackSerializer,
          status: status,
          meta: {
            action: result[:action],
            message: result[:message]
          }
        )
      end

      def render_failure(result)
        render_error(
          { errors: [ result[:errors] ] },
          status: :unprocessable_entity
        )
      end

      def feedback_params
        params.permit(
          :sourcing_id,
          :apply_id,
          :candidate_id,
          :sourced_profile_sourcing_id,
          :reference_type,
          :reference_id,
          :reason,
          :feedback_type,
          :job_id
        )
      end
    end
  end
end
