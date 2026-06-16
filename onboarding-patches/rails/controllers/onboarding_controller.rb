# frozen_string_literal: true

module V1
  module Users
    class OnboardingController < ApplicationController
      before_action :authorize_request
      before_action :set_user, only: [:status, :progress]

      # POST /v1/users/invite
      # Admin invites a new recruiter — triggers onboarding flow
      def invite
        authorize_admin!

        user = User.find_or_initialize_by(email: invite_params[:email])

        if user.new_record?
          # Create new user with invited state
          temp_password = SecureRandom.hex(16)
          user.assign_attributes(
            email: invite_params[:email],
            name: invite_params[:name],
            phone: invite_params[:phone],
            password: temp_password,
            password_confirmation: temp_password,
            account_id: @current_user.account_id,
            activation_state: "invited",
            invited_at: Time.current,
            invited_by_user_id: @current_user.id,
            role: invite_params[:role] || "recruiter",
            onboarding_lia_override: invite_params[:onboarding_lia_enabled]
          )
          user.save!
        elsif user.activation_state == "active"
          render json: { error: "User already active" }, status: :unprocessable_entity
          return
        end

        # Generate magic link
        result = MagicLinkService.generate(user: user, purpose: "onboarding")

        # Create onboarding session
        session = OnboardingSession.create!(
          user: user,
          account_id: @current_user.account_id,
          phase: "pending",
          whatsapp_phone: user.phone
        )

        # Send welcome email
        if user.onboarding_lia_enabled?
          OnboardingMailer.welcome_email(
            user: user,
            magic_link_url: result[:url],
            admin_name: @current_user.name || @current_user.email,
            whatsapp_number: ENV["LIA_WHATSAPP_NUMBER"]
          ).deliver_later

          session.update!(email_sent_at: Time.current)
        end

        # Publish event to RabbitMQ for FastAPI OnboardingOrchestrator
        publish_onboarding_event("user_invited", {
          user_id: user.id,
          account_id: @current_user.account_id,
          name: user.name,
          email: user.email,
          phone: user.phone,
          magic_link_url: result[:url],
          onboarding_lia_enabled: user.onboarding_lia_enabled?,
          session_id: session.id,
          invited_by: @current_user.name || @current_user.email
        })

        render json: {
          user_id: user.id,
          onboarding_session_id: session.id,
          magic_link_url: result[:url],
          onboarding_lia_enabled: user.onboarding_lia_enabled?
        }, status: :created

      rescue MagicLinkService::RateLimitExceeded => e
        render json: { error: e.message }, status: :too_many_requests
      end

      # GET /v1/onboarding/status
      # Get current user's onboarding status
      def status
        session = OnboardingSession.for_user(@target_user.id).active.first

        render json: {
          activation_state: @target_user.activation_state,
          onboarding_completed: @target_user.onboarding_complete?,
          first_login: @target_user.first_login_at.present?,
          session: session ? {
            id: session.id,
            phase: session.phase,
            progress_steps: session.progress_steps,
            onboarding_data: session.onboarding_data,
            duration_seconds: session.duration_seconds
          } : nil
        }
      end

      # PATCH /v1/onboarding/progress
      # Update onboarding step completion
      def progress
        session = OnboardingSession.for_user(@current_user.id).active.first
        return render json: { error: "No active session" }, status: :not_found unless session

        if params[:step_id]
          session.mark_step_completed!(params[:step_id])
        end

        if params[:phase]
          session.advance_to!(params[:phase])
        end

        if params[:phase] == "complete"
          session.update!(completed_at: Time.current)
          @current_user.complete_onboarding!
        end

        render json: { phase: session.phase, progress_steps: session.progress_steps }
      end

      # GET /v1/onboarding/settings
      # Get company onboarding settings
      def settings
        if request.get?
          render json: {
            onboarding_lia_enabled: @current_user.account&.onboarding_lia_enabled || false
          }
        elsif request.patch?
          authorize_admin!
          @current_user.account&.update!(
            onboarding_lia_enabled: params[:onboarding_lia_enabled]
          )
          render json: { onboarding_lia_enabled: @current_user.account.onboarding_lia_enabled }
        end
      end

      # POST /v1/onboarding/consent
      # Record LGPD consent during onboarding
      def consent
        ConsentRecord.create!(
          candidate_id: nil, # Not a candidate — a user
          company_id: @current_user.account_id,
          consent_type: "onboarding_data_processing",
          status: "given",
          given_at: Time.current,
          ip_address: request.remote_ip,
          user_agent: request.user_agent,
          source: params[:channel] || "web",
          metadata: { user_id: @current_user.id, onboarding: true }
        )

        @current_user.update!(
          lgpd_consent_at: Time.current,
          lgpd_consent_channel: params[:channel] || "web"
        )

        render json: { consented: true }
      end

      private

      def invite_params
        params.require(:invite).permit(:email, :name, :phone, :role, :onboarding_lia_enabled)
      end

      def set_user
        @target_user = @current_user
      end

      def authorize_admin!
        unless @current_user.role.in?(%w[admin owner])
          render json: { error: "Admin access required" }, status: :forbidden
        end
      end

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
