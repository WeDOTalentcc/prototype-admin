# frozen_string_literal: true

module PhoneCallInterviews
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
      return fail_result("Candidate has no phone number") unless candidate.mobile_phone.present?

      ActiveRecord::Base.transaction do
        @scheduling_link = create_scheduling_link
        @evaluation_candidate = create_evaluation_candidate
      end

      dispatch_invite

      success_result(@evaluation_candidate.reload)
    rescue StandardError => e
      Rails.logger.error "❌ [PhoneCallInterviews::CreateService] #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      fail_result(e.message)
    end

    private

    attr_reader :user, :account, :params

    def create_evaluation_candidate
      EvaluationCandidate.create!(
        evaluation: evaluation,
        candidate: candidate,
        account: account,
        user: user,
        apply_id: params[:apply_id],
        job: job,
        evaluation_type: :phone_call,
        phone_call_status: "pending_schedule",
        custom_invite_message: params[:custom_invite_message],
        scheduling_link: @scheduling_link,
        date_expiration: params[:date_expiration] || 7.days.from_now
      )
    end

    def create_scheduling_link
      link = SchedulingLink.create!(
        account: account,
        created_by: user,
        candidate_id: candidate.id,
        job_id: job.id,
        apply_id: params[:apply_id],
        duration_minutes: params[:duration_minutes] || 30,
        interview_type: "behavioral",
        subject: "Entrevista por telefone — #{job.title}",
        message: invite_message,
        expires_at: params[:date_expiration] || 7.days.from_now,
        channels: []
      )

      generate_slots(link)
      link
    end

    def generate_slots(link)
      slots_data = params[:slots] || default_slots
      slots_data.each do |slot|
        link.scheduling_slots.create!(
          start_time: slot[:start_time],
          end_time: slot[:end_time],
          is_available: true
        )
      end
    end

    def invite_message
      return params[:custom_invite_message] if params[:custom_invite_message].present?

      "Olá #{candidate.name&.split&.first}! Gostaríamos de conversar com você sobre a vaga de #{job.title}. " \
        "Escolha um horário disponível para que nossa IA entre em contato por telefone."
    end

    def default_slots
      settings = user.try(:scheduling_setting)
      start_hour = settings&.try(:work_hours_start) || "09:00"
      end_hour = settings&.try(:work_hours_end) || "18:00"
      duration = params[:duration_minutes]&.to_i || 30
      lookahead = settings&.try(:lookahead_days) || 7

      slots = []
      (1..lookahead).each do |day_offset|
        date = Date.current + day_offset
        next if date.saturday? || date.sunday?

        current_time = Time.zone.parse("#{date} #{start_hour}")
        end_time = Time.zone.parse("#{date} #{end_hour}")

        while current_time + duration.minutes <= end_time
          slots << {
            start_time: current_time.iso8601,
            end_time: (current_time + duration.minutes).iso8601
          }
          current_time += duration.minutes
        end
      end

      slots
    end

    def dispatch_invite
      PhoneCallInterviews::InviteNotificationJob.perform_later(
        @evaluation_candidate.id,
        account.id,
        params[:channels] || %w[email whatsapp]
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
      Result.new(success?: false, data: nil, errors: Array(errors))
    end
  end
end
