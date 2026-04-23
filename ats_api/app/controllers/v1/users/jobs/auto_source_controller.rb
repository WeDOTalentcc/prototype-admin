# frozen_string_literal: true

module V1
  module Users
    module Jobs
      class AutoSourceController < ApplicationController
        before_action :set_job

        def create
          result = ::Jobs::AutoSourcePaginationService.call(
            job: @job,
            user: @current_user,
            target_count: limit_param,
            min_score_threshold: min_score_param,
            sources: sources_param,
            reset: reset_param
          )

          unless result[:success]
            return render json: {
              success: false,
              error: result[:error],
              metadata: result[:metadata]
            }, status: :unprocessable_entity
          end

          render json: {
            success: true,
            sourcing_id: result[:sourcing_id],
            uid: result[:uid],
            status: result[:status],
            job_id: @job.id,
            min_score_threshold: min_score_param,
            target_count: limit_param,
            pagination: result[:pagination],
            subscription: {
              channel: "SourcingChannel",
              stream: "#{@current_user.id}_sourcing_#{result[:sourcing_id]}",
              events: [
                "auto_source_started",
                "profile_analyzed",
                "auto_source_batch_completed",
                "auto_source_finished"
              ]
            },
            message: "Auto Source started. Subscribe to channel for real-time updates."
          }, status: :accepted
        end

        private

        def set_job
          @job = Job.find_by(id: params[:id])
          return render_not_found("Job") unless @job
          render_simple_error("Not authorized", status: :forbidden) unless @job.account_id == @current_user.account_id
        end

        def limit_param
          (params[:limit] || 30).to_i.clamp(1, 100)
        end

        def min_score_param
          (params[:min_score] || 70).to_f.clamp(0, 100)
        end

        def reset_param
          ActiveModel::Type::Boolean.new.cast(params[:reset]) || false
        end

        def sources_param
          raw = params[:sources] || params[:source] || [ "local" ]
          normalized = Array(raw).map { |s| s.to_s.downcase }.uniq
          normalized & %w[local global]
        end
      end
    end
  end
end
