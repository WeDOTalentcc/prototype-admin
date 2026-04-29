# frozen_string_literal: true

module InterviewSessions
  class CreateService
    Result = Struct.new(:success?, :data, :errors, keyword_init: true)

    def initialize(user:, params:)
      @user = user
      @account = user.account
      @params = params
    end

    def call
      return fail_result("Evaluation not found") unless evaluation
      return fail_result("Candidate not found") unless candidate
      return fail_result("Job not found") unless job

      session = build_session
      return fail_result(session.errors.full_messages) unless session.save

      eval_candidate = find_or_create_evaluation_candidate
      session.update!(evaluation_candidate: eval_candidate)

      notify_candidate(session) if @params[:channels].present?

      success_result(session)
    rescue StandardError => e
      Rails.logger.error "❌ [InterviewSessions::CreateService] #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      fail_result(e.message)
    end

    private

    attr_reader :user, :account, :params

    def build_session
      InterviewSession.new(
        account: account,
        evaluation: evaluation,
        candidate: candidate,
        job: job,
        apply_id: params[:apply_id],
        created_by: user,
        interview_type: params[:interview_type] || "voice",
        duration_minutes: params[:duration_minutes] || 30,
        language: params[:language] || "pt-BR"
      )
    end

    def find_or_create_evaluation_candidate
      EvaluationCandidate.find_or_create_by!(
        evaluation: evaluation,
        candidate: candidate,
        account: account
      ) do |ec|
        ec.user = user
        ec.apply_id = params[:apply_id]
        ec.job_id = job.id
      end
    end

    def notify_candidate(session)
      InterviewSessions::InviteNotificationJob.perform_later(
        session.id,
        account.id,
        params[:channels]
      )
    end

    def evaluation
      @evaluation ||= Evaluation.find_by(id: params[:evaluation_id], account_id: account.id)
    end

    def candidate
      @candidate ||= Candidate.find_by(id: params[:candidate_id], account_id: account.id)
    end

    def job
      @job ||= Job.find_by(id: params[:job_id], account_id: account.id)
    end

    def success_result(data)
      Result.new(success?: true, data: data, errors: [])
    end

    def fail_result(errors)
      errors = Array(errors)
      Result.new(success?: false, data: nil, errors: errors)
    end
  end
end
