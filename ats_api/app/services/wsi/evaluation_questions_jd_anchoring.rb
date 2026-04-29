# frozen_string_literal: true

module Wsi
  module EvaluationQuestionsJdAnchoring
    MAX_ANCHOR_ATTEMPTS = 3

    def self.apply!(parsed_response, job:)
      return parsed_response unless enabled?
      return parsed_response unless parsed_response.is_a?(Hash)

      raw_list = parsed_response[:questions] || parsed_response["questions"]
      return parsed_response unless raw_list.is_a?(Array)

      updated = raw_list.each_with_index.map do |q, idx|
        next q unless q.is_a?(Hash)

        qh = q.deep_stringify_keys
        text = qh["description"].to_s.strip
        next q.deep_symbolize_keys if text.blank?

        title = qh["title"].to_s.strip
        ctype = qh["competence_type"].to_s
        category = ctype == "behavioral" ? "behavioral" : "technical"
        skill_or_trait = title.presence || "competência da pergunta #{idx + 1}"

        meta = { "attempts" => [], "needs_manual_review" => false, "final_is_anchored" => false }
        current_text = text

        MAX_ANCHOR_ATTEMPTS.times do |i|
          attempt = i + 1
          validation = Wsi::JdAnchoringValidatorService.call(
            job: job,
            question_text: current_text,
            skill_or_trait_label: skill_or_trait,
            question_category: category
          )

          meta["attempts"] << {
            "attempt" => attempt,
            "success" => validation.success?,
            "error" => validation.error,
            "data" => validation.data.presence || {},
            "raw_response" => validation.raw_response
          }

          unless validation.success?
            meta["needs_manual_review"] = true
            break
          end

          data = validation.data
          if data[:is_anchored]
            meta["final_is_anchored"] = true
            break
          end

          if attempt >= MAX_ANCHOR_ATTEMPTS
            meta["needs_manual_review"] = true
            break
          end

          suggestion = data[:suggestion].to_s.strip
          if suggestion.blank?
            meta["needs_manual_review"] = true
            break
          end

          current_text = Wsi::AnchoredQuestionRegeneratorService.call(
            job: job,
            question_text: current_text,
            auditor_suggestion: suggestion,
            skill_or_trait_label: skill_or_trait,
            question_category: category
          )
        end

        qh["description"] = current_text
        qh["wsi_jd_anchoring"] = meta
        qh.deep_symbolize_keys
      end

      if parsed_response.key?(:questions)
        parsed_response[:questions] = updated
      else
        parsed_response["questions"] = updated.map { |row| row.is_a?(Hash) ? row.stringify_keys : row }
      end

      parsed_response
    end

    def self.enabled?
      ActiveModel::Type::Boolean.new.cast(ENV.fetch("WSI_JD_ANCHORING_ENABLED", "true"))
    end
  end
end
