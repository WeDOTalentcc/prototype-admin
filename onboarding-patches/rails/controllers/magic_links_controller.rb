# frozen_string_literal: true

module V1
  module Auth
    class MagicLinksController < ApplicationController
      # No auth required — magic link IS the auth
      protect_from_forgery with: :null_session

      # GET /v1/auth/magic-link/verify?token=X&uid=Y
      # Validates magic link and returns JWT
      def verify
        result = MagicLinkService.verify(
          token: params[:token],
          user_id: params[:uid],
          ip: request.remote_ip,
          user_agent: request.user_agent
        )

        # Update onboarding session
        session = OnboardingSession.for_user(result[:user][:id]).active.first
        if session
          session.update!(magic_link_clicked_at: Time.current)
          session.advance_to!("first_login") if session.phase.in?(%w[pending welcome whatsapp_intro whatsapp_learn awaiting_login])
        end

        # Publish event for FastAPI
        publish_onboarding_event("magic_link_used", {
          user_id: result[:user][:id],
          first_login: result[:first_login],
          session_id: session&.id
        })

        render json: result, status: :ok

      rescue MagicLinkService::InvalidToken => e
        render json: { error: "Link invalido ou expirado" }, status: :unauthorized
      rescue MagicLinkService::ExpiredToken => e
        render json: { error: "Link expirado. Solicite um novo." }, status: :gone
      rescue MagicLinkService::AlreadyUsed => e
        render json: { error: "Link ja foi utilizado." }, status: :conflict
      end

      private

      def publish_onboarding_event(event_type, payload)
        MessageService::EventPublisher.publish({
          event_type: event_type,
          payload: payload,
          timestamp: Time.current.iso8601
        })
      rescue StandardError => e
        Rails.logger.warn "Failed to publish onboarding event: #{e.message}"
      end
    end
  end
end
