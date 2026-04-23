# frozen_string_literal: true

module PostInterview
  class SaveAnswerService
    def initialize(interview_session:, question_id:, transcription:, audio_content: nil, audio_content_type: nil, audio_duration: nil)
      @session = interview_session
      @question_id = question_id
      @transcription = transcription
      @audio_content = audio_content
      @audio_content_type = audio_content_type || "audio/wav"
      @audio_duration = audio_duration
    end

    def call
      return error("No evaluation candidate") unless evaluation_candidate

      question = find_question
      return error("Question not found") unless question

      answer = persist_answer(question)
      return error(answer.errors.full_messages.join(", ")) unless answer.persisted?

      attach_audio(answer)
      score(answer)

      { success: true, answer: answer }
    rescue StandardError => e
      Rails.logger.error "❌ [PostInterview::SaveAnswerService] #{e.class}: #{e.message}"
      error(e.message)
    end

    private

    attr_reader :session, :question_id, :transcription, :audio_content, :audio_content_type, :audio_duration

    def evaluation_candidate
      @evaluation_candidate ||= session.evaluation_candidate
    end

    def find_question
      session.evaluation.questions.where(is_deleted: false).find_by(id: question_id)
    end

    def persist_answer(question)
      answer = Answer.find_or_initialize_by(
        evaluation_id: session.evaluation_id,
        candidate_id: session.candidate_id,
        question_id: question.id
      )

      answer.assign_attributes(
        title: question.title,
        description: transcription,
        detail: question.details,
        job_id: session.job_id,
        apply_id: session.apply_id,
        account_id: session.account_id,
        user_id: session.created_by_id,
        time: audio_duration,
        source: Answer::SOURCE_INTERNAL
      )

      answer.save!
      answer
    end

    def attach_audio(answer)
      return if audio_content.blank?

      answer.attach_audio_from_base64(audio_content, content_type: audio_content_type)
    end

    def score(answer)
      return unless answer.question.present?

      Evaluations::ScoreCalculatorService.call(answer: answer)
    rescue StandardError => e
      Rails.logger.warn "[PostInterview::SaveAnswerService] Scoring failed for answer #{answer.id}: #{e.message}"
    end

    def error(message)
      { success: false, error: message }
    end
  end
end
