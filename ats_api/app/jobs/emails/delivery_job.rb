# frozen_string_literal: true

require "nokogiri"

module Emails
  class DeliveryJob
    include Sidekiq::Job
    sidekiq_options queue: :email_delivery, retry: 5

    sidekiq_retry_in do |count, exception|
      case exception
      when Emails::RateLimitHit then 60 * (count + 1)
      when Emails::ProviderUnavailable then 300 * (count + 1)
      else (count ** 4) + 15
      end
    end

    def perform(dispatch_message_id, record_json)
      message = DispatchMessage.includes(:dispatch).find(dispatch_message_id)
      dispatch = message.dispatch

      Apartment::Tenant.switch(message.account.tenant) do
        record = JSON.parse(record_json, symbolize_names: true)

        Emails::CircuitBreaker.check!(provider: dispatch.provider, account_id: dispatch.account_id)
        Emails::RateLimiter.check!(provider: dispatch.provider, account_id: dispatch.account_id)

        rendered_body = render_template(dispatch.body, message, record)
        rendered_subject = render_template(dispatch.subject, message, record)

        message.update!(status: :processing)

        result = Emails::Delivery::StrategyResolver.deliver_with_fallback(
          dispatch: dispatch,
          to: message.recipient_address,
          subject: rendered_subject,
          body: rendered_body,
          message: message
        )

        message.update!(
          status: :sent,
          sent_at: Time.current,
          provider_response: result
        )

        Emails::RateLimiter.record_send!(provider: dispatch.provider, account_id: dispatch.account_id)
        Emails::CircuitBreaker.record_success!(provider: dispatch.provider, account_id: dispatch.account_id)
      end
    rescue Emails::RateLimitHit, Emails::CircuitOpen => e
      message&.update!(status: :pending)
      raise
    rescue => e
      message&.update!(status: :failed, provider_response: { error: { class: e.class.name, message: e.message } })
      Emails::CircuitBreaker.record_failure!(provider: dispatch.provider, account_id: dispatch.account_id)
      raise
    end

    private

    def render_template(template, message, base_record)
      record = base_record.merge(
        candidate: load_candidate(message.recipient_id),
        dispatch_message: message
      ).compact

      message.ensure_unsubscribe_record! if message.recipient_id.present?

      rendered = TagReplacer::Service.call(
        template,
        record: record,
        recruiter_id: message.dispatch.user_id
      )

      return rendered unless message.dispatch.channel_type == "email"

      inject_tracking(rendered, message)
    end

    def inject_tracking(html_content, message)
      return html_content if html_content.blank?

      doc = Nokogiri::HTML::DocumentFragment.parse(html_content)

      if message.tracking_click_base_url.present?
        doc.css("a[href]").each do |link|
          next if Emails::UrlTrackingService.skip_tracking?(link["href"])
          link["href"] = "#{message.tracking_click_base_url}?url=#{CGI.escape(link['href'])}"
        end
      end

      result = doc.to_html
      Emails::TrackingPixelService.inject_pixel(result, message.tracking_pixel_url)
    end

    def load_candidate(candidate_id)
      return nil unless candidate_id
      Candidate.find_by(id: candidate_id)
    end
  end
end
