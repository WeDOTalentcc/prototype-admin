# frozen_string_literal: true

require "digest"

module V1
  module Users
    module Integrations
      module Microsoft
        class BulkEmailsController < V1::Users::ApplicationController
          include MicrosoftLinked

          def create
            params_for_bulk = bulk_email_params
            recipient_addresses = Array(params_for_bulk[:recipients]).map(&:to_s).select(&:present?).uniq
            return render json: { error: "Informe pelo menos um destinatário" }, status: :unprocessable_entity if recipient_addresses.empty?

            if params_for_bulk[:html].blank? && params_for_bulk[:text].blank?
              return render json: { error: "Forneça html ou text" }, status: :unprocessable_entity
            end

            base_schedule_time = parse_time_or_now(params_for_bulk[:start_at])
            # Default pacing is 3 minutes between emails unless explicitly provided
            delay_seconds = if params_for_bulk[:delay_seconds].present?
                              params_for_bulk[:delay_seconds].to_i
            else
                              180
            end
            delay_seconds = 0 if delay_seconds.negative?

            dispatch = Dispatch.create!(
              account_id: @current_user.account_id,
              user_id: @current_user.id,
              channel_type: "microsoft_mail",
              status: :pending,
              name: params_for_bulk[:name].presence || "Microsoft Bulk Email",
              scheduled_for: base_schedule_time,
              subject: params_for_bulk[:subject],
              body: params_for_bulk[:html].presence || params_for_bulk[:text]
            )

            message_ids = []
            recipient_addresses.each do |email_address|
              unique_recipient_id = compute_numeric_id("#{dispatch.id}:#{email_address}")
              message = DispatchMessage.create!(
                account_id: @current_user.account_id,
                dispatch_id: dispatch.id,
                recipient_type: "ExternalEmail",
                recipient_id: unique_recipient_id,
                recipient_address: email_address,
                status: :pending,
                subject: params_for_bulk[:subject],
                body: params_for_bulk[:html].presence || params_for_bulk[:text]
              )
              message_ids << message.id
            end

            message_ids.each_with_index do |message_id, index|
              seconds_from_now = [ base_schedule_time - Time.current, 0 ].max + (delay_seconds * index)
              job_options = {
                "save_to_sent" => ActiveModel::Type::Boolean.new.cast(params_for_bulk[:save_to_sent].nil? ? true : params_for_bulk[:save_to_sent]),
                "reply_to" => (params_for_bulk[:reply_to].presence || nil)
              }
              MsGraphEmailWorker.perform_in(seconds_from_now, message_id, @current_user.id, job_options)
            end

            render json: {
              ok: true,
              dispatch_id: dispatch.id,
              messages_count: message_ids.size,
              scheduled_start_at: base_schedule_time,
              delay_seconds: delay_seconds
            }, status: :accepted
          rescue => error
            Rails.logger.error("Bulk email create error: #{error.class} #{error.message}")
            Rails.logger.error(error.backtrace&.first(5)&.join("\n"))
            render json: { error: "Falha ao agendar envio em massa" }, status: :unprocessable_entity
          end

          private

          def bulk_email_params
            raw = params[:email].is_a?(ActionController::Parameters) ? params[:email] : params
            raw.permit(:name, :subject, :html, :text, :reply_to, :save_to_sent, :start_at, :delay_seconds, recipients: [])
          end

          def parse_time_or_now(value)
            return Time.current if value.blank?
            Time.zone.parse(value.to_s) || Time.current
          rescue
            Time.current
          end

          def compute_numeric_id(string)
            max_signed_63 = (1 << 63) - 1
            Digest::SHA256.hexdigest(string)[0, 16].to_i(16) & max_signed_63
          end
        end
      end
    end
  end
end
