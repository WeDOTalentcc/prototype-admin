# frozen_string_literal: true

module V1
  module Users
    class IssuesController < ApplicationController
      include SearchRenderer
      include RenderDefault

      before_action :authorize_request
      before_action :set_issue, only: %i[show update destroy]

      def index
        params[:where] ||= {}
        params[:where][:account_id] = @current_user.account_id

        perform_search(
          model: Issue,
          serializer: IssueSerializer
        )
      end

      def show
        render_success(@issue, serializer: IssueSerializer)
      end

      def create
        @issue = Issue.new(issue_params.merge(account_id: @current_user.account_id))

        if @issue.save
          render_success(@issue, serializer: IssueSerializer, status: :created)
        else
          render_error(@issue, status: :unprocessable_entity)
        end
      end

      def update
        if @issue.update(issue_params)
          render_success(@issue, serializer: IssueSerializer)
        else
          render_error(@issue, status: :unprocessable_entity)
        end
      end

      def destroy
        @issue.destroy
        render_no_content
      end

      private

      def set_issue
        @issue = Issue.find_by(id: params[:id], account_id: @current_user.account_id)
        render_not_found("Issue") unless @issue
      end

      def issue_params
        params.require(:issue).permit(
          :text,
          :type,
          :status,
          :candidate_id,
          :evaluation_id,
          :evaluation_candidate_id,
          :question_id,
          :job_id,
          :reference_type,
          :reference_id
        )
      end
    end
  end
end
