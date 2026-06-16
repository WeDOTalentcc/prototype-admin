# frozen_string_literal: true

require "digest"

module V1
  module Users
    module Integrations
      module Microsoft
        class EmailsController < V1::Users::ApplicationController
          include MicrosoftLinked

          def create
            email_params = create_email_params
            recipient_addresses = Array(email_params[:recipients]).map(&:to_s).select(&:present?)
            recipient_addresses << email_params[:to] if email_params[:to].present?
            recipient_addresses.uniq!
            return render json: { error: "Informe pelo menos um destinatário" }, status: :unprocessable_entity if recipient_addresses.empty?

            if email_params[:html].blank? && email_params[:text].blank?
              return render json: { error: "Forneça html ou text" }, status: :unprocessable_entity
            end

            dispatch = Dispatch.create!(
              account_id: @current_user.account_id,
              user_id: @current_user.id,
              channel_type: "microsoft_mail",
              status: :pending,
              name: email_params[:name].presence || "Microsoft Email",
              scheduled_for: email_params[:scheduled_for],
              subject: email_params[:subject],
              body: email_params[:html].presence || email_params[:text]
            )

            message_ids = []
            recipient_addresses.each do |address|
              unique_recipient_id = compute_numeric_id("#{dispatch.id}:#{address}")
              message = DispatchMessage.create!(
                account_id: @current_user.account_id,
                dispatch_id: dispatch.id,
                recipient_type: "ExternalEmail",
                recipient_id: unique_recipient_id,
                recipient_address: address,
                status: :pending,
                subject: email_params[:subject],
                body: email_params[:html].presence || email_params[:text]
              )
              message_ids << message.id
            end

            base_schedule_time = parse_time_or_now(email_params[:scheduled_for])
            job_options = {
              "save_to_sent" => ActiveModel::Type::Boolean.new.cast(email_params[:save_to_sent].nil? ? true : email_params[:save_to_sent]),
              "reply_to" => (email_params[:reply_to].presence || nil)
            }
            message_ids.each do |message_id|
              seconds_from_now = (base_schedule_time - Time.current).to_f
              if seconds_from_now > 0.5
                MsGraphEmailWorker.perform_in(seconds_from_now, message_id, @current_user.id, job_options)
              else
                MsGraphEmailWorker.perform_async(message_id, @current_user.id, job_options)
              end
            end


            render json: { ok: true, dispatch_id: dispatch.id, recipients_count: recipient_addresses.size }, status: :accepted
          rescue => error
            Rails.logger.error("MS email create error: #{error.class} #{error.message}")
            Rails.logger.error(error.backtrace&.first(5)&.join("\n"))
            render json: { error: "Falha ao agendar envio" }, status: :unprocessable_entity
          end

          private

          def create_email_params
            raw = params[:email].is_a?(ActionController::Parameters) ? params[:email] : params
            raw.permit(:name, :subject, :html, :text, :reply_to, :save_to_sent, :to, :scheduled_for, recipients: [])
          end

          def parse_time_or_now(value)
            return Time.current if value.blank?
            Time.zone.parse(value.to_s) || Time.current
          rescue
            Time.current
          end

          def compute_numeric_id(string)
            # 63-bit numeric id (fits signed bigint): mask to (2^63 - 1)
            max_signed_63 = (1 << 63) - 1
            Digest::SHA256.hexdigest(string)[0, 16].to_i(16) & max_signed_63
          end
        end
      end
    end
  end
end
