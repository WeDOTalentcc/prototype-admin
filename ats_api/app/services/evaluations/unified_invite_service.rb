# frozen_string_literal: true

module Evaluations
  class UnifiedInviteService
    CHANNEL_CONFIG = {
      internal: { label: "Iniciar Triagem por Chat", icon: "💬" },
      voice: { label: "Triagem por Voz", icon: "🎙️" },
      phone: { label: "Triagem por Ligação", icon: "📞" }
    }.freeze

    def initialize(evaluation_candidate:, user:, channels: [], interview_session: nil, interview_sessions: {})
      @evaluation_candidate = evaluation_candidate
      @user = user
      @channels = channels
      @interview_sessions = normalize_sessions(interview_session, interview_sessions)
    end

    def call
      return error("Candidate email not found") unless candidate_email.present?
      return error("No channels provided") if @channels.empty?

      channel_buttons = build_channel_buttons
      return error("No valid channels") if channel_buttons.empty?

      body = render_email(channel_buttons)
      send_email(body)

      { success: true }
    rescue StandardError => e
      Rails.logger.error "❌ [Evaluations::UnifiedInviteService] #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      error(e.message)
    end

    def render_body
      channel_buttons = build_channel_buttons
      return nil if channel_buttons.empty?

      render_email(channel_buttons)
    end

    private

    attr_reader :evaluation_candidate, :user, :interview_sessions

    def build_channel_buttons
      @channels.filter_map { |channel| build_button(channel.to_sym) }
    end

    def build_button(channel)
      config = CHANNEL_CONFIG[channel]
      return unless config

      url = channel_url(channel)
      return unless url

      { url: url, label: config[:label] }
    end

    def channel_url(channel)
      case channel
      when :internal
        evaluation_candidate.get_evaluation_candidate_url
      when :voice, :phone
        interview_sessions[channel]&.public_url
      end
    end

    def normalize_sessions(legacy_session, sessions_hash)
      return sessions_hash if sessions_hash.present?
      return {} unless legacy_session

      key = legacy_session.interview_type&.to_sym || :voice
      { key => legacy_session }
    end

    def decline_url
      base_url = evaluation_candidate.get_evaluation_candidate_url
      return unless base_url
      "#{base_url}?action=decline"
    end

    def render_email(channel_buttons)
      EvaluationMailer.with(
        candidate: evaluation_candidate.candidate,
        evaluation_candidate: evaluation_candidate,
        job: evaluation_candidate.job,
        user: user,
        channels: channel_buttons,
        decline_url: decline_url
      ).unified_invitation.body.to_s
    end

    def send_email(body)
      dispatch = Dispatch.create!(
        account_id: user.account_id,
        user_id: user.id,
        channel_type: "microsoft_mail",
        status: :pending,
        name: "Convite unificado - #{Time.current.strftime('%d/%m/%Y %H:%M')}",
        subject: email_subject,
        body: ""
      )

      pixel_token = SecureRandom.urlsafe_base64(32)
      click_token = SecureRandom.urlsafe_base64(32)
      base_url = Rails.application.credentials.dig(:app, :base_url).presence || ENV.fetch("FRONT_URL", "http://localhost:3000")
      click_base_url = "#{base_url}/v1/tracking/click/#{click_token}"
      pixel_url = "#{base_url}/v1/tracking/pixel/#{pixel_token}.gif"
      tracked_body = Emails::UrlTrackingService.wrap_links(body, click_base_url)
      tracked_body = Emails::TrackingPixelService.inject_pixel(tracked_body, pixel_url)

      message = DispatchMessage.create!(
        account_id: user.account_id,
        dispatch_id: dispatch.id,
        recipient_type: "ExternalEmail",
        recipient_id: compute_numeric_id("#{dispatch.id}:#{candidate_email}"),
        recipient_address: candidate_email,
        status: :pending,
        subject: email_subject,
        body: tracked_body,
        tracking_pixel_token: pixel_token,
        tracking_click_token: click_token
      )

      MsGraphEmailWorker.perform_async(message.id, user.id, { "save_to_sent" => true, "reply_to" => nil })
    end

    def email_subject
      company = user.account&.name || "WeDO Talent"
      job_title = evaluation_candidate.job&.title || "a vaga"
      "#{company} — Convite para triagem sobre #{job_title}"
    end

    def candidate_email
      @candidate_email ||= evaluation_candidate.candidate&.email
    end

    def compute_numeric_id(string)
      Digest::SHA256.hexdigest(string)[0, 16].to_i(16) & ((1 << 63) - 1)
    end

    def error(message)
      { success: false, error: message }
    end
  end
end
