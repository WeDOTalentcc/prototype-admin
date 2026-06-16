# frozen_string_literal: true

module Evaluations
  class QuestionsIntegrityHashBuilder
    def self.call(evaluation_id:)
      new(evaluation_id: evaluation_id).call
    end

    def initialize(evaluation_id:)
      @evaluation_id = evaluation_id
    end

    def call
      Digest::SHA256.hexdigest(JSON.generate(canonical_payload))
    end

    private

    def canonical_payload
      Question
        .where(evaluation_id: @evaluation_id, is_deleted: false)
        .order(Arel.sql("questions.position ASC NULLS LAST"), "questions.id ASC")
        .map { |question| entry_for(question) }
    end

    def entry_for(question)
      {
        "bloom_level" => question.bloom_level,
        "category" => question.category,
        "choices" => deep_sort_for_json(question.choices),
        "competence_type" => question.competence_type,
        "description" => normalize_utf8(question.description),
        "details" => normalize_utf8(question.details),
        "dreyfus_target" => question.dreyfus_target,
        "expected_response" => normalize_utf8(question.expected_response),
        "extra_params" => deep_sort_for_json(question.extra_params),
        "framework" => question.framework,
        "framework_weights" => deep_sort_for_json(question.framework_weights),
        "id" => question.id,
        "is_required" => question.is_required,
        "number_retakers" => question.number_retakers,
        "ocean_trait" => question.ocean_trait,
        "parent_question_id" => question.parent_question_id,
        "position" => question.position,
        "response_type" => question.response_type,
        "selective_process_id" => question.selective_process_id,
        "time" => question.time,
        "title" => normalize_utf8(question.title),
        "validation_type_weight" => question.validation_type_weight,
        "value_father" => deep_sort_for_json(question.value_father),
        "wsi_metadata" => deep_sort_for_json(question.wsi_metadata),
        "wsi_reviewed" => question.wsi_reviewed
      }
    end

    def normalize_utf8(text)
      text.to_s.unicode_normalize(:nfc)
    end

    def deep_sort_for_json(value)
      case value
      when Hash
        value.keys.map(&:to_s).sort.each_with_object({}) do |key, acc|
          acc[key] = deep_sort_for_json(value[key] || value[key.to_sym])
        end
      when Array
        value.map { |v| deep_sort_for_json(v) }
      else
        value
      end
    end
  end
end
