module V1
  module Evaluations
    class ApplicationController < ApplicationController
      MAX_CONCURRENT_SESSIONS = 3

      before_action :authorize_request
      before_action :check_rate_limit

      def authorize_request
        @account = Account.find_by(uid: params[:account_uid])

        if @account.nil?
          return render json: { errors: [ "Unauthorized" ] }, status: :unauthorized
        end

        Apartment::Tenant.switch!(@account.tenant)
        @evaluation_candidate = EvaluationCandidate.where(uid: params[:evaluation_candidate_uid]).first

        if @evaluation_candidate.nil?
          return render json: { errors: [ "Unauthorized" ] }, status: :unauthorized
        end

        if @evaluation_candidate.date_expiration.present? && @evaluation_candidate.date_expiration < Time.current
          return render json: { errors: [ "Link expirado" ], expired: true }, status: :gone
        end

        @evaluation = Evaluation.find_by(id: @evaluation_candidate.evaluation_id)
      end

      private

      def check_rate_limit
        return unless @evaluation_candidate

        active_sessions = EvaluationCandidate
          .where(candidate_id: @evaluation_candidate.candidate_id, session_status: :active, completed: false)
          .where.not(id: @evaluation_candidate.id)
          .count

        return if active_sessions < MAX_CONCURRENT_SESSIONS

        render json: { errors: [ "Limite de #{MAX_CONCURRENT_SESSIONS} sessões simultâneas atingido" ] }, status: :too_many_requests
      end

      public

      def global_search_params
        @search_params = {}
        @search_params = @search_params.merge({ where: where_params })
                                      .merge({ order: order_params })
                                      .merge({ page: params[:page] || 1 })
                                      .merge({ limit: limit_params })
      end

      def where_params(base = false)
        where = base || {}
        where.merge!(parse_json_param(params[:where])) if params[:where]

        filter = parse_json_param(params[:filter]) if params[:filter].present?

        filter&.to_a&.each do |field|
          if field[1].is_a?(Array) || field[1].is_a?(Integer) || field[1].is_a?(Hash)
            where[field[0].to_s] = field[1]
            next
          end
          where[field[0].to_s] = { like: "%#{field[1]&.downcase}%" } if field[1].present?
        end

        where.deep_symbolize_keys
      end

      def order_params
        return { created_at: "desc" } if params[:search] == "*" && params[:order].blank?

        parse_json_param(params[:order])
      end

      def limit_params
        params[:limit] || 30
      end
    end
  end
end
