module V1
  module Webhooks
    class MailgunController < ApplicationController
      skip_before_action :authorize_request, only: [ :tracking ], raise: false
      skip_before_action :verify_authenticity_token, only: [ :tracking ], raise: false

      def self.mailgun_signing_key
        @mailgun_signing_key ||= Rails.application.credentials.dig(:mailgun, :webhook_signing_key)
      end

      def tracking
        return head :unauthorized unless verify_signature

        event_data = params[:'event-data'] || params["event-data"]
        return head :ok unless event_data

        event_type = event_data["event"]
        message_id = event_data.dig("message", "id") || event_data.dig("message", "headers", "message-id")

        dispatch_message = DispatchMessage.find_by(provider_message_id: message_id)
        return head :not_found unless dispatch_message

        Apartment::Tenant.switch!(dispatch_message.account.tenant) do
          process_event(dispatch_message, event_type, event_data)
        end

        head :ok
      end

      private

      def verify_signature
        return true if Rails.env.test? || Rails.env.development?

        token = params[:signature][:token]
        timestamp = params[:signature][:timestamp]
        signature = params[:signature][:signature]

        return false if token.blank? || timestamp.blank? || signature.blank?

        expected_signature = OpenSSL::HMAC.hexdigest(
          OpenSSL::Digest::SHA256.new,
          self.class.mailgun_signing_key,
          "#{timestamp}#{token}"
        )

        ActiveSupport::SecurityUtils.secure_compare(signature, expected_signature)
      end

      def process_event(dispatch_message, event_type, event_data)
        case event_type
        when "opened"
          dispatch_message.update!(opened_at: Time.current) unless dispatch_message.opened_at
          nil
        when "clicked"
          handle_click(dispatch_message, event_data)
        when "delivered"
          dispatch_message.update!(status: :delivered)
        when "failed", "bounced", "rejected"
          handle_bounce(dispatch_message, event_data)
        end
      end

      def handle_click(dispatch_message, event_data)
        EmailTrackingEvent.create!(
          dispatch_message: dispatch_message,
          account: dispatch_message.account,
          event_type: :click,
          occurred_at: Time.at(event_data["timestamp"].to_i),
          url_clicked: event_data["url"],
          metadata: event_data
        )
      end

      def handle_bounce(dispatch_message, event_data)
        dispatch_message.update!(
          status: :failed,
          bounced_at: Time.current,
          bounce_reason: event_data.dig("reason", "description") || event_data["reason"]
        )

        EmailTrackingEvent.create!(
          dispatch_message: dispatch_message,
          account: dispatch_message.account,
          event_type: :bounce,
          occurred_at: Time.at(event_data["timestamp"].to_i),
          metadata: event_data
        )

        EmailFollowupStatus
          .for_candidate(dispatch_message.recipient_id)
          .pending
          .find_each { |fs| fs.complete!("bounced") }
      end
    end
  end
end
