# frozen_string_literal: true

module V1
  module Users
    module Evaluations
      class QuestionsController < ApplicationController
        include ResourceLoader

        def index
          perform_search(
            model: Question,
            serializer: QuestionSerializer,
            search_with_pin: search_with_pin.merge(where: { is_deleted: false, evaluation_id: params[:evaluation_id] }),
          )
        end

        def show
          render_success(@question, serializer: QuestionSerializer)
        end

        def create
          @question = Question.create(question_params.merge(evaluation_id: params[:evaluation_id]))

          if @question.save
            return render_success(@question, serializer: QuestionSerializer, status: :created)
          end
          render_error(@question, status: :unprocessable_entity)
        end

        def update
          @question.update(question_params) ? render_success(@question, serializer: QuestionSerializer) : render_error(@question)
        end

        def destroy
          @question.update(is_deleted: true)
          render_no_content
        end

        private

        def question_params
          permitted = params.require(:question).permit(
            :title,
            :description,
            :details,
            :number_retakers,
            :time,
            :evaluation_id,
            :response_type,
            :position,
            :deleted,
            :selective_process_id,
            :expected_response,
            :is_required,
            :parent_question_id,
            :choices,
            :value_father,
            :extra_params,
            :category,
            :competence_type,
            :framework,
            :bloom_level,
            :dreyfus_target,
            :ocean_trait,
            :validation_type_weight,
            :wsi_reviewed,
            framework_weights: {},
            wsi_metadata: {}
          )
          if permitted.key?(:ocean_trait)
            permitted[:ocean_trait] = Wsi::OceanTraitCanonical.to_storage(permitted[:ocean_trait])
          end
          permitted
        end
      end
    end
  end
end
