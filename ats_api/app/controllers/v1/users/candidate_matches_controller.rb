# frozen_string_literal: true

module V1
  module Users
    class CandidateMatchesController < ApplicationController
      def search
        return render_simple_error("text is required", status: :bad_request) if text_param.blank?

        result = Matching::CandidateForText.new(
          text: text_param,
          account_id: @current_user.account_id,
          top_k: top_k_param,
          filters: filters_param,
          page: page_param,
          per_page: per_page_param,
          min_score: min_score_param,
          max_score: max_score_param
        ).call

        return render_simple_error(result[:error], status: :unprocessable_entity) unless result[:success]

        render_success(
          result[:records],
          serializer: CandidateMatchSerializer,
          meta: result[:meta],
          serializer_params: { includes: includes_param, current_user: @current_user }
        )
      end

      private

      def text_param
        params[:text].to_s.strip
      end

      def top_k_param
        value = params[:top_k].to_i
        return 500 if value <= 0
        [value, 2000].min
      end

      def page_param
        [params[:page].to_i, 1].max
      end

      def per_page_param
        value = params[:per_page].to_i
        return 20 if value <= 0
        [value, 100].min
      end

      def min_score_param
        value = params[:min_score].to_f
        return 0.0 if value < 0
        [value, 1.0].min
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
        raw = params[:include] || params[:includes]
        return [] if raw.blank?
        raw.is_a?(String) ? raw.split(",").map(&:strip) : Array(raw)
      end
    end
  end
end
