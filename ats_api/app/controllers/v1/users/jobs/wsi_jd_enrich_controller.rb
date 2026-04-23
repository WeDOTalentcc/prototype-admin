# frozen_string_literal: true

module V1
  module Users
    module Jobs
      class WsiJdEnrichController < ApplicationController
        before_action :set_job

        def create
          score_result = Wsi::JdQualityScoreService.call(job: @job, persist: false)

          if score_result[:score] < Wsi::JdEnrichmentService::MIN_QUALITY_SCORE
            return render json: {
              success:          false,
              error:            "jd_quality_below_threshold",
              jd_quality_score: score_result[:jd_quality_score],
              score:            score_result[:score],
              status:           score_result[:status],
              dimensions:       score_result[:dimensions]
            }, status: :unprocessable_entity
          end

          result = Wsi::JdEnrichmentService.call(
            job: @job,
            jd_quality_score: score_result[:jd_quality_score]
          )

          unless result[:success]
            return render json: {
              success: false,
              error:   result[:error]
            }, status: :unprocessable_entity
          end

          render json: {
            success:             true,
            message:             "JD enriquecido com sucesso",
            jd_quality_score:    score_result[:jd_quality_score],
            lia_job_description: result[:lia_job_description]
          }, status: :ok
        end

        private

        def set_job
          @job = Job.find_by(id: params[:id], account_id: @current_user.account_id, is_deleted: false)
          render json: { error: "Vaga não encontrada" }, status: :not_found unless @job
        end
      end
    end
  end
end
