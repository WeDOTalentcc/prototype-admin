# frozen_string_literal: true

module PhoneCallInterviews
  class TriggerCallJob
    include Sidekiq::Job

    sidekiq_options queue: :default, retry: 2

    def perform(evaluation_candidate_id, account_id)
      account = Account.find_by(id: account_id)
      return unless account

      Apartment::Tenant.switch!(account.tenant)

      ec = EvaluationCandidate.find_by(id: evaluation_candidate_id)
      return unless ec&.phone_call?
      return unless ec.phone_call_status == "scheduled"

      interview_session = create_interview_session(ec)
      ec.update!(
        interview_session: interview_session,
        phone_call_status: "calling"
      )

      trigger_python_service(ec, interview_session, account)
    rescue StandardError => e
      Rails.logger.error "❌ [PhoneCallInterviews::TriggerCallJob] #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")

      ec&.update(phone_call_status: "failed") if ec&.phone_call_status == "calling"
      raise
    end

    private

    def create_interview_session(ec)
      InterviewSession.create!(
        account: ec.account,
        evaluation: ec.evaluation,
        candidate: ec.candidate,
        job: ec.job,
        apply_id: ec.apply_id,
        created_by: ec.user,
        evaluation_candidate: ec,
        interview_type: "phone",
        duration_minutes: 30,
        language: "pt-BR"
      )
    end

    def trigger_python_service(ec, session, account)
      base_url = ENV.fetch("INTERVIEW_AI_BASE_URL", "http://localhost:8001")
      conn = Faraday.new(url: base_url) do |f|
        f.request :json
        f.response :json
        f.options.timeout = 30
        f.options.open_timeout = 10
      end

      response = conn.post("/api/v1/phone-call/initiate") do |req|
        req.body = {
          token: session.token,
          account_uid: account.uid,
          candidate_phone: ec.candidate.mobile_phone,
          candidate_name: ec.candidate.name,
          job_title: ec.job&.title,
          evaluation_id: ec.evaluation_id,
          questions: session.questions_snapshot,
          callback_url: build_callback_url(account.uid, session.token)
        }
      end

      unless response.success?
        Rails.logger.error "❌ [PhoneCallInterviews::TriggerCallJob] Python service returned #{response.status}: #{response.body}"
        ec.update!(phone_call_status: "failed")
      end
    end

    def build_callback_url(account_uid, token)
      api_base = ENV.fetch("API_BASE_URL") do
        Rails.env.production? ? "https://api.wedotalent.cc" : "http://localhost:3000"
      end
      "#{api_base}/interview/#{account_uid}/#{token}"
    end
  end
end
