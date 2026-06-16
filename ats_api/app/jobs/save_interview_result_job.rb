# frozen_string_literal: true

class SaveInterviewResultJob < ApplicationJob
  queue_as :default

  def perform(interview_session_id, account_id)
    account = Account.find_by(id: account_id)
    return unless account

    Apartment::Tenant.switch!(account.tenant)

    session = InterviewSession.find_by(id: interview_session_id)
    return unless session

    eval_candidate = session.evaluation_candidate
    return unless eval_candidate

    save_scores(session, eval_candidate)
    sync_apply_status(session)
    session.update!(status: "scored")

    Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Rails.logger.info "✅ [SaveInterviewResultJob] Interview scored"
    Rails.logger.info "   Session: #{session.id} | Score: #{session.score}"
    Rails.logger.info "   Candidate context present: #{session.candidate_context.present?}"
    Rails.logger.info "   Recommendation: #{session.recommendation}"
    Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  rescue StandardError => e
    Rails.logger.error "❌ [SaveInterviewResultJob] Error: #{e.message}"
    Rails.logger.error e.backtrace.first(5).join("\n")
    raise
  end

  private

  def save_scores(session, eval_candidate)
    report = session.report || {}

    eval_candidate.update!(
      completed: true,
      score: session.score,
      wsi_summary: report["summary"] || report["resumo"],
      ai_feedback: {
        source: "interview_ai_voice",
        interview_session_id: session.id,
        report: report,
        recommendation: session.recommendation,
        duration_seconds: calculate_duration(session),
        transcript_length: session.transcript&.size || 0
      }
    )
  end

  def sync_apply_status(session)
    return unless session.apply_id

    Apply.where(id: session.apply_id).first&.update(
      evaluation_candidate_status: Apply.evaluation_candidate_statuses[:answered],
      updated_at: Time.current
    )
  end

  def calculate_duration(session)
    return 0 unless session.started_at && session.completed_at

    (session.completed_at - session.started_at).to_i
  end
end
