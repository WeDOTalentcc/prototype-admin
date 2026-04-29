# frozen_string_literal: true

module Emails
  class OrchestratorJob
    include Sidekiq::Job
    sidekiq_options queue: :email_delivery, retry: 3

    BATCH_SIZE = 1_000

    def perform(dispatch_id, recipients_json, record_json)
      dispatch = Dispatch.find(dispatch_id)

      Apartment::Tenant.switch(dispatch.account.tenant) do
        dispatch.update!(status: :processing)

        recipients = JSON.parse(recipients_json, symbolize_names: true)
        record = JSON.parse(record_json, symbolize_names: true)

        create_messages_in_batches(dispatch, recipients)
        schedule_deliveries(dispatch, record)
      end
    rescue => e
      dispatch&.update!(status: :failed, target_payload: dispatch.target_payload.merge(error: e.message))
      raise
    end

    private

    def create_messages_in_batches(dispatch, recipients)
      now = Time.current

      recipients.each_slice(BATCH_SIZE) do |batch|
        rows = batch.map do |recipient|
          {
            dispatch_id: dispatch.id,
            account_id: dispatch.account_id,
            recipient_address: recipient[:email],
            recipient_type: "Candidate",
            recipient_id: recipient[:candidate_id],
            status: DispatchMessage.statuses[:pending],
            subject: dispatch.subject,
            body: dispatch.body,
            created_at: now,
            updated_at: now
          }
        end

        DispatchMessage.insert_all(rows)
      end
    end

    def schedule_deliveries(dispatch, record)
      rate = delivery_rate_for(dispatch.provider)

      dispatch.dispatch_messages.pending.find_each.with_index do |message, index|
        delay = (index / rate.to_f) * 60

        Emails::DeliveryJob.set(wait: delay.seconds).perform_later(
          message.id,
          record.to_json
        )
      end
    end

    def delivery_rate_for(provider)
      case provider
      when "mailgun" then ENV.fetch("EMAIL_RATE_MAILGUN_PER_MINUTE", "5").to_i
      when "ms_graph" then ENV.fetch("EMAIL_RATE_MSGRAPH_PER_MINUTE", "25").to_i
      else 10
      end
    end
  end
end
