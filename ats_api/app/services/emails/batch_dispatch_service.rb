# frozen_string_literal: true

module Emails
  class BatchDispatchService
    Result = Data.define(:success, :dispatch, :errors)

    def self.call(recipients:, template:, subject:, sender:, provider: :mailgun, record: {}, options: {})
      new(recipients: recipients, template: template, subject: subject, sender: sender, provider: provider, record: record, options: options).execute
    end

    def execute
      validate_inputs!

      dispatch = create_dispatch!

      Emails::OrchestratorJob.perform_async(
        dispatch.id,
        recipients_payload.to_json,
        record_payload.to_json
      )

      Result.new(success: true, dispatch: dispatch, errors: [])
    rescue ActiveRecord::RecordInvalid => e
      Result.new(success: false, dispatch: nil, errors: [ e.message ])
    end

    private

    attr_reader :recipients, :template, :subject, :sender, :provider, :record, :options

    def initialize(recipients:, template:, subject:, sender:, provider:, record:, options:)
      @recipients = recipients
      @template = template
      @subject = subject
      @sender = sender
      @provider = provider
      @record = record
      @options = options
    end

    def create_dispatch!
      Dispatch.create!(
        status: :pending,
        subject: @subject,
        body: @template,
        provider: @provider.to_s,
        user_id: @sender.id,
        account_id: @sender.account_id,
        target_type: "ids",
        target_payload: {
          record_context: @record.except(:candidate),
          options: @options
        }
      )
    end

    def recipients_payload
      @recipients.map do |recipient|
        {
          email: recipient[:email],
          candidate_id: recipient[:candidate_id],
          name: recipient[:name]
        }
      end
    end

    def record_payload
      @record.transform_values do |value|
        value.is_a?(ActiveRecord::Base) ? { id: value.id, type: value.class.name } : value
      end
    end

    def validate_inputs!
      raise ArgumentError, "recipients cannot be empty" if @recipients.blank?
      raise ArgumentError, "recipients exceeds maximum (50,000)" if @recipients.size > 50_000
      raise ArgumentError, "template cannot be blank" if @template.blank?
    end
  end
end
