# frozen_string_literal: true

module Wsi
  class QuestionRetryCoordinator
    def self.call(max_attempts: 3)
      last_error = nil
      last_text = nil
      max_attempts.times do |i|
        attempt = i + 1
        last_text = yield(attempt, last_error)
        result = QuestionValidator.call(text: last_text)
        if result.valid
          return {
            success: true,
            text: last_text,
            generation_attempts: attempt,
            needs_manual_review: false,
            error: nil
          }
        end
        last_error = result.error
      end

      {
        success: false,
        text: last_text,
        generation_attempts: max_attempts,
        needs_manual_review: true,
        error: last_error
      }
    end
  end
end
