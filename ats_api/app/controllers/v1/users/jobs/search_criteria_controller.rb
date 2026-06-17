# frozen_string_literal: true

module V1
  module Users
    module Jobs
      class SearchCriteriaController < ApplicationController
        include RenderDefault

        before_action :set_job

        def generate
          result = ::Jobs::GenerateSearchCriteriaService.new(
            job: @job,
            force: ActiveModel::Type::Boolean.new.cast(params[:force])
          ).call

          unless result.success?
            return render json: { error: result.error }, status: :unprocessable_entity
          end

          render json: {
            data: {
              agent_search_criteria: result.criteria,
              generated: result.generated
            }
          }, status: :ok
        end

        def update
          @job.update!(agent_search_criteria: params[:agent_search_criteria])

          render json: {
            data: { agent_search_criteria: @job.agent_search_criteria }
          }, status: :ok
        end

        private

        def set_job
          @job = Job.where(is_deleted: false, account_id: @current_user.account_id).find_by(id: params[:job_id])
          render_not_found("Job") unless @job
        end
      end
    end
  end
end
