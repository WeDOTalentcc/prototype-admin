# frozen_string_literal: true

module V1
  module Users
    class OpinionsController < ApplicationController
      include ResourceLoader

      def index
        perform_search(
          model: Opinion,
          serializer: OpinionSerializer,
          search_with_pin: search_with_pin.merge(
            where: {
              account_id: @current_user.account_id,
              is_deleted: false
            }
          )
        )
      end

      def create
        opinion = Opinion.new(opinion_params.merge(
          user_id: @current_user.id,
          account_id: @current_user.account_id
        ))

        return render_error(opinion, status: :unprocessable_entity) unless opinion.save

        render_success(opinion, serializer: OpinionSerializer, status: :created)
      end

      def destroy
        return render_not_found("Opinion") unless @opinion

        @opinion.update(is_deleted: true)
        render_no_content
      end

      def candidate_summary
        render json: ::Opinions::CandidateSummaryService.call(
          candidate: find_candidate,
          account_id: @current_user.account_id
        ), status: :ok
      end

      def candidate_history
        candidate = find_candidate
        return render json: [] unless candidate

        opinions = Opinion.active
          .by_candidate(candidate.id)
          .where(account_id: @current_user.account_id)
          .order(created_at: :desc)

        render json: opinions.map { |opinion| flatten(opinion) }, status: :ok
      end

      private

      def find_candidate
        Candidate.find_by(id: params[:candidate_id], account_id: @current_user.account_id)
      end

      def opinion_params
        params.require(:opinion).permit(:candidate_id, :job_id, :content, :status, metadata: {})
      end

      def flatten(opinion)
        OpinionSerializer.new(opinion).serializable_hash[:data][:attributes]
      end
    end
  end
end
