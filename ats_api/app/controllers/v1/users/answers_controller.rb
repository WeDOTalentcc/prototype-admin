# frozen_string_literal: true

module V1
  module Users
    class AnswersController < ApplicationController
      before_action :set_answer, only: %i[show update destroy]

      def index
        perform_search(
          model: Answer,
          serializer: AnswerSerializer,
        )
      end

      def show
        render_success(@answer, serializer: AnswerSerializer)
      end

      def create
        @answer = Answer.new(answer_params.merge(user_id: @current_user.id, account_id: @current_user.account_id, source: Answer::SOURCE_INTERNAL))
        if @answer.save
          process_answer_scoring(@answer)
          return render_success(@answer, serializer: AnswerSerializer, status: :created)
        end
        render_error(@answer, status: :unprocessable_entity)
      end

      def update
        if @answer.update(answer_params.merge(source: Answer::SOURCE_INTERNAL))
          process_answer_scoring(@answer)
          return render_success(@answer, serializer: AnswerSerializer)
        end
        render_error(@answer)
      end

      def destroy
        @answer.destroy
        render_no_content
      end

      private

      def set_answer
        @answer = Answer.find_by(id: params[:id])
        render_not_found("Answer") unless @answer
      end

      def answer_params
        params.require(:answer).permit(
          :title,
          :question_id,
          :evaluation_id,
          :candidate_id,
          :job_id,
          :time,
          :description,
          :detail,
          :apply_id,
          :user_id,
          :time_taken,
          :represent_field,
          :analysis_data,
          :final_skill_score,
          :reference_id,
          :reference_type,
          :account_id,
          :audio_file,
          :self_declaration_score,
          :eligibility_answer,
          comments_response: {},
          choices: []
        )
      end

      def process_answer_scoring(answer)
        return unless answer.question.present?

        Evaluations::ScoreCalculatorService.call(answer: answer)
        evaluation_candidate = EvaluationCandidate.find_by(
          evaluation_id: answer.evaluation_id,
          candidate_id: answer.candidate_id
        )
        return unless evaluation_candidate

        Evaluations::EvaluationAggregateService.call(evaluation_candidate: evaluation_candidate)
      rescue StandardError => e
        Rails.logger.warn("[Users::AnswersController] Failed to process scoring for answer #{answer.id}: #{e.message}")
      end
    end
  end
end
