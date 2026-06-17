# frozen_string_literal: true

module V1
  module Users
    module Jobs
      class EvaluationsController < ApplicationController
        before_action :set_job

        def index
          scope_params = build_scope_params

          perform_search(
            model: Evaluation,
            serializer: EvaluationSerializer,
            search_params: scope_params
          )
        end

        private

        def set_job
          @job = Job.find_by(id: params[:job_id], is_deleted: false)
          render_not_found("Job") unless @job
        end

        def build_scope_params
          base = (params[:search] || {}).to_unsafe_h
          base[:where] ||= {}
          base[:where][:job_id] = @job.id
          base
        end
      end
    end
  end
end
