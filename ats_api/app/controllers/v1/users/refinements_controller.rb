# frozen_string_literal: true

module V1
  module Users
    class RefinementsController < ApplicationController
      before_action :load_sourcing

      def create
        service = Candidates::SimilarCandidates::RefinementService.new(
          account: @current_user.account,
          user: @current_user
        )

        result = service.call(
          sourcing: @sourcing,
          liked_candidate_ids: Array(params[:liked_candidate_ids]).map(&:to_i),
          disliked_feedbacks: parse_disliked_feedbacks,
          sources: Array(params[:sources] || [ "local" ]),
          limit: (params[:limit] || 20).to_i.clamp(1, 50)
        )

        render json: result, status: :ok
      rescue ArgumentError => e
        render json: { error: "invalid_params", message: e.message }, status: :unprocessable_entity
      rescue ActiveRecord::RecordNotFound => e
        render json: { error: "not_found", message: e.message }, status: :not_found
      end

      private

      def load_sourcing
        @sourcing = Sourcing.find_by!(id: params[:sourcing_id], account_id: @current_user.account_id)
      end

      def parse_disliked_feedbacks
        return [] if params[:disliked_feedbacks].blank?

        Array(params[:disliked_feedbacks]).map do |fb|
          {
            candidate_id: fb[:candidate_id]&.to_i,
            reason: fb[:reason]&.to_s
          }
        end.compact
      end
    end
  end
end
