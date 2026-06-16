# frozen_string_literal: true

module V1
  module Users
    module Jobs
      class MatchesController < ApplicationController
        before_action :set_job
        before_action :authorize_access

        def candidates
          matcher = Matching::CandidateForJob.new(
            @job.id,
            top_k: top_k_param,
            account_id: @current_user.account_id,
            filters: filters_param,
            page: page_param,
            per_page: per_page_param,
            min_score: min_score_param,
            max_score: max_score_param
          )
          result = matcher.call

          records = result[:records] || []

          fields = params[:compact]&.split(",") || ([])

          meta = result[:meta]

          if fields.any?
            data = records.map do |record|
              record.as_json(methods: [ :score ]).slice(*fields.map(&:strip).map(&:to_s))
            end
            return render json: {
              data: data,
              meta: meta
            }
          end

          render_success(
            records,
            serializer: JobCandidateMatchSerializer,
            meta: meta,
            serializer_params: { includes: includes_param, current_user: @current_user }
          )
        rescue ActiveRecord::RecordNotFound
          render_not_found("Job")
        rescue StandardError => e
          render_simple_error(e.message, status: :unprocessable_entity)
        end

        private

        def set_job
          @job = Job.find(params[:job_id])
        end

        def authorize_access
          return if @job.account_id == @current_user.account_id
          render_simple_error("Não autorizado", status: :forbidden)
        end

        def top_k_param
          value = params[:top_k].to_i
          return 500 if value <= 0
          [ value, 2000 ].min
        end

        def page_param
          [ params[:page].to_i, 1 ].max
        end

        def per_page_param
          value = params[:per_page].to_i
          return 30 if value <= 0
          [ value, 100 ].min
        end

        def min_score_param
          value = params[:min_score].to_f
          return 0.0 if value < 0
          [ value, 1.0 ].min
        end

        def max_score_param
          value = params[:max_score].to_f
          return 1.0 if value <= 0 || value > 1.0
          value
        end

        def filters_param
          return {} unless params[:filters]
          params[:filters].is_a?(Hash) ? params[:filters] : {}
        end

        def includes_param
          # Support JSON:API include param or a custom 'includes' array
          raw = params[:include] || params[:includes]
          return [] if raw.blank?
          raw.is_a?(String) ? raw.split(",").map(&:strip) : Array(raw)
        end
      end
    end
  end
end
