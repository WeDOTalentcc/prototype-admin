# frozen_string_literal: true

module Evaluations
  class AnswersIntegrityHashBuilder
    def self.call(evaluation_id:, candidate_id:)
      new(evaluation_id: evaluation_id, candidate_id: candidate_id).call
    end

    def initialize(evaluation_id:, candidate_id:)
      @evaluation_id = evaluation_id
      @candidate_id = candidate_id
    end

    def call
      payload = canonical_entries
      Digest::SHA256.hexdigest(JSON.generate(payload))
    end

    private

    def canonical_entries
      Answer
        .joins(:question)
        .where(evaluation_id: @evaluation_id, candidate_id: @candidate_id)
        .order(Arel.sql("questions.position ASC NULLS LAST"), "questions.id ASC")
        .map { |answer| entry_for(answer) }
    end

    def entry_for(answer)
      {
        "question_id" => answer.question_id,
        "description" => normalize_utf8(answer.description),
        "self_declaration_score" => answer.self_declaration_score,
        "eligibility_answer" => answer.eligibility_answer
      }
    end

    def normalize_utf8(text)
      text.to_s.unicode_normalize(:nfc)
    end
  end
end
