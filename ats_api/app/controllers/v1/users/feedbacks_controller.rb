# frozen_string_literal: true

module V1
  module Users
    class FeedbacksController < ApplicationController
      include SearchRenderer
      include RenderDefault

      before_action :authorize_request
      before_action :set_feedback, only: %i[show update destroy]

      def index
        params[:where] ||= {}
        params[:where][:is_deleted] = false if params[:where][:is_deleted].nil?
        params[:where][:account_id] = @current_user.account_id

        perform_search(
          model: Feedback,
          serializer: FeedbackSerializer
        )
      end

      def show
        render_success(@feedback, serializer: FeedbackSerializer)
      end

      def create
        @feedback = Feedback.create(feedback_params.merge(account_id: @current_user.account_id))

        if @feedback.save
          return render_success(@feedback, serializer: FeedbackSerializer, status: :created)
        end
        render_error(@feedback, status: :unprocessable_entity)
      end

      def update
        @feedback.update(feedback_params) ? render_success(@feedback, serializer: FeedbackSerializer) : render_error(@feedback)
      end

      def destroy
        @feedback.update(is_deleted: true)
        render_success(@feedback, serializer: FeedbackSerializer)
      end

      private

      def set_feedback
        @feedback = Feedback.find_by(id: params[:id], is_deleted: false)
        render_not_found("Feedback") unless @feedback
      end

      def feedback_params
        params.require(:feedback).permit(:title, :description, :name, :additional_text, :is_deleted, :job_id, :selective_process_id)
      end
    end
  end
end
