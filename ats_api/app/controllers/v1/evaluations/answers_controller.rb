# frozen_string_literal: true

module V1
  module Evaluations
    class AnswersController < ApplicationController
      include RenderDefault

      before_action :set_answer, only: %i[show update destroy]

      def index
        answers = Answer.where(evaluation_id: @evaluation_candidate.evaluation_id, candidate_id: @evaluation_candidate.candidate_id)
        render_success(answers, serializer: AnswerSerializer)
      end

      def show
        render_success(@answer, serializer: AnswerSerializer)
      end

      def create
        return render json: { errors: [ "question_id is required" ] }, status: :unprocessable_entity if answer_params[:question_id].blank?
        return render json: { errors: [ "Invalid question for this evaluation" ] }, status: :unprocessable_entity unless valid_evaluation_question?(answer_params[:question_id])

        source = answer_params[:source].presence || Answer::SOURCE_INTERNAL
        source = Answer::SOURCE_INTERNAL unless Answer::SOURCES.include?(source)

        @answer = Answer.new(answer_params.except(:source).merge(
          evaluation_id: @evaluation_candidate.evaluation_id,
          candidate_id: @evaluation_candidate.candidate_id,
          job_id: @evaluation_candidate.job_id,
          apply_id: @evaluation_candidate.apply_id,
          account_id: @evaluation_candidate.account_id,
          user_id: @evaluation_candidate.user_id,
          source: source
        ))
        if @answer.save
          process_answer_scoring(@answer)
          return render_success(@answer, serializer: AnswerSerializer, status: :created)
        end
        render_error(@answer, status: :unprocessable_entity)
      end

      def update
        if @answer.candidate_forbidden_content_change?(answer_params)
          return render json: { errors: [ "Answer content cannot be changed after submit" ] }, status: :forbidden
        end

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

      def load_context
        @evaluation_candidate = EvaluationCandidate.find_by(uid: params[:uid], is_deleted: false)
        render_not_found("EvaluationCandidate") unless @evaluation_candidate
      end

      def set_answer
        @answer = Answer.find_by(id: params[:id], evaluation_id: @evaluation_candidate.evaluation_id, candidate_id: @evaluation_candidate.candidate_id)
        render_not_found("Answer") unless @answer
      end

      def answer_params
        params.require(:answer).permit(
          :title,
          :question_id,
          :time,
          :description,
          :detail,
          :time_taken,
          :represent_field,
          :reference_id,
          :reference_type,
          :audio_file,
          :source,
          :self_declaration_score,
          :eligibility_answer,
          comments_response: {},
          choices: []
        )
      end

      def valid_evaluation_question?(question_id)
        evaluation = @evaluation_candidate.evaluation
        return false if evaluation.blank?

        evaluation.questions.exists?(id: question_id)
      end

      def process_answer_scoring(answer)
        return unless answer.question.present?

        Evaluations::ScoreCalculatorService.call(answer: answer)
        Evaluations::EvaluationAggregateService.call(evaluation_candidate: @evaluation_candidate)
      rescue StandardError => e
        Rails.logger.warn("[Evaluations::AnswersController] Failed to process scoring for answer #{answer.id}: #{e.message}")
      end
    end
  end
end
