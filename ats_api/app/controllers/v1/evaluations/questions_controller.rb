# frozen_string_literal: true

module V1
  module Evaluations
    class QuestionsController < ApplicationController
      include SearchRenderer
      include SearchParams
      include RenderDefault

      def index
        answered_question_ids = Answer.where(
          evaluation_id: @evaluation_candidate.evaluation_id,
          candidate_id: @evaluation_candidate.candidate_id
        ).pluck(:question_id)
        question = perform_search(
          model: Question,
          serializer: QuestionSerializer,
          search_with_pin: global_search_params.merge(where: { evaluation_id: @evaluation_candidate.evaluation_id, is_deleted: false, _not: { id: answered_question_ids } }),
          page: params[:page],
          return_results: true
        )

        if question[:records]&.empty?
          @evaluation_candidate.update(completed: true)
          @evaluation_candidate.save
          @evaluation_candidate.send_completion_notifications
          return render json: { message: "No questions found", finished: true }, status: :ok
        end

        render_success(question[:records]&.last, serializer: QuestionSerializer, meta: {
          total: question[:total_count],
          aggregators: question[:aggs]
        })
      end
    end
  end
end
