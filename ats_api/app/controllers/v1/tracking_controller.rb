module V1
  class TrackingController < ApplicationController
    skip_before_action :authorize_request, raise: false

    GIF_1x1 = "\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x3C\x00\x3B".freeze

    def pixel
      dispatch_message = find_message_across_tenants(:tracking_pixel_token, params[:token])
      return head :not_found unless dispatch_message

      unless dispatch_message.opened_at
        dispatch_message.update_columns(opened_at: Time.current)
      end

      create_tracking_event(dispatch_message, :open)

      send_data(GIF_1x1, type: "image/gif", disposition: "inline")
    end

    def click
      dispatch_message = find_message_across_tenants(:tracking_click_token, params[:token])
      return redirect_to(root_path) unless dispatch_message

      target_url = params[:url] || root_path

      unless dispatch_message.clicked_at
        dispatch_message.update_columns(clicked_at: Time.current, clicked_url: target_url)
      end

      create_tracking_event(dispatch_message, :click, url_clicked: target_url)

      redirect_to(target_url, allow_other_host: true)
    end

    private

    def find_message_across_tenants(field, token)
      return nil if token.blank?

      Account.where.not(tenant: [ nil, "" ]).find_each do |account|
        msg = Apartment::Tenant.switch(account.tenant) { DispatchMessage.find_by(field => token) }
        if msg
          Apartment::Tenant.switch!(account.tenant)
          return msg
        end
      end
      nil
    end

    def create_tracking_event(message, event_type, url_clicked: nil)
      attrs = {
        dispatch_message_id: message.id,
        event_type: event_type,
        occurred_at: Time.current,
        user_agent: request.user_agent,
        ip_address: request.remote_ip,
        metadata: { referer: request.referer }
      }
      attrs[:url_clicked] = url_clicked if url_clicked

      if EmailTrackingEvent.column_names.include?("account_id")
        attrs[:account_id] = message.account_id
      end

      EmailTrackingEvent.create!(attrs)
    rescue => e
      Rails.logger.warn "[Tracking] Failed to create event: #{e.message}"
    end
  end
end
