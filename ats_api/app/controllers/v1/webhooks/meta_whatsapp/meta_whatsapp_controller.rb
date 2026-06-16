module V1
  module Webhooks
    module MetaWhatsapp
      class MetaWhatsappController < ApplicationController
        include PhoneNormalizable
        def show
          mode = params["hub.mode"]
          token = params["hub.verify_token"]
          challenge = params["hub.challenge"]

          if mode == "subscribe" && token == ENV["META_WHATSAPP_VERIFY_TOKEN"]
            return render plain: challenge, status: :ok
          end
          head :forbidden
        end

        def create
          # === LOG COMPLETO DA REQUEST DO META ===
          log_msg = [ "=" * 80,
                     "🌐 [META WEBHOOK] NOVA REQUEST RECEBIDA",
                     "📅 Timestamp: #{Time.current}",
                     "🔧 Environment: #{Rails.env}",
                     "📦 Request Headers:" ]

          request.headers.each do |key, value|
            log_msg << "  #{key}: #{value}" if key.start_with?("HTTP_", "CONTENT_")
          end

          log_msg << "📋 PARAMS COMPLETOS DO META:"
          log_msg << JSON.pretty_generate(params.to_unsafe_h)
          log_msg << "=" * 80

          log_msg.each { |line| Rails.logger.info line }
          STDOUT.flush

          message_data = params.dig(:entry, 0, :changes, 0, :value, :messages, 0)
          unless message_data
            Rails.logger.info "⚠️  [WhatsApp Webhook] No message_data found in request, returning ok"
            STDOUT.flush
            return head :ok
          end

          sender_phone = normalize_phone(message_data[:from])
          message_text = message_data.dig(:text, :body)

          Rails.logger.info "📱 [WhatsApp Webhook] Received message from: #{sender_phone}"
          Rails.logger.info "📝 [WhatsApp Webhook] Message text: #{message_text}"
          STDOUT.flush

          if message_text.blank?
            Rails.logger.info "⚠️  [WhatsApp Webhook] Message text is blank, returning ok"
            STDOUT.flush
            return head :ok
          end

          Rails.logger.info "🔍 [WhatsApp Webhook] Checking redirect config for phone: #{sender_phone}, env: #{Rails.env}, type: 'webhook'"
          redirect_config = WhatsappConfiguration.find_config(sender_phone, Rails.env, "webhook")

          Rails.logger.info "🎯 [WhatsApp Webhook] Redirect config found: #{redirect_config.present?}"
          if redirect_config
            Rails.logger.info "📋 [WhatsApp Webhook] Config details - ID: #{redirect_config.id}, redirect_url: #{redirect_config.redirect_url.inspect}, active: #{redirect_config.active.inspect}"
          else
            Rails.logger.info "ℹ️  [WhatsApp Webhook] No redirect config found in database for this phone/environment"
          end
          STDOUT.flush

          if redirect_config&.redirect_url.present?
            Rails.logger.info "🔀 [WhatsApp Webhook] ===== REDIRECIONANDO ====="
            Rails.logger.info "🔀 [WhatsApp Webhook] FROM: #{sender_phone}"
            Rails.logger.info "🔀 [WhatsApp Webhook] TO: #{redirect_config.redirect_url}"
            Rails.logger.info "🔀 [WhatsApp Webhook] Config ID: #{redirect_config.id}"
            Rails.logger.info "🔀 [WhatsApp Webhook] ================================"
            STDOUT.flush
            redirect_to_external_webhook(redirect_config.redirect_url, params.to_unsafe_h)
            Rails.logger.info "✅ [WhatsApp Webhook] Redirect completed, returning ok to Meta"
            STDOUT.flush
            return head :ok
          else
            Rails.logger.info "⏩ [WhatsApp Webhook] ===== PROCESSANDO LOCALMENTE ====="
            Rails.logger.info "⏩ [WhatsApp Webhook] No redirect configured, will process in this application"
            Rails.logger.info "⏩ [WhatsApp Webhook] ================================"
            STDOUT.flush
          end

          mapping = find_tenant_mapping(sender_phone)
          unless mapping && mapping.account
            Rails.logger.warn "⚠️  [WhatsApp Webhook] No tenant mapping found for phone: #{sender_phone}"
            STDOUT.flush
            return head :ok
          end

          target_tenant = mapping.account.tenant
          target_account_id = mapping.account_id

          Rails.logger.info "🏢 [WhatsApp Webhook] Tenant mapping found - Tenant: #{target_tenant}, Account ID: #{target_account_id}"
          STDOUT.flush

          begin
            Apartment::Tenant.switch!(target_tenant)
            Rails.logger.info "🔄 [WhatsApp Webhook] Switched to tenant: #{target_tenant}"
            STDOUT.flush

            candidate = find_candidate_for_message(sender_phone)
            unless candidate
              Rails.logger.warn "WhatsApp Webhook: Candidate not found for phone #{sender_phone} in tenant #{target_tenant}"
              STDOUT.flush
              return head :ok
            end

            unless candidate.account_id == target_account_id
              Rails.logger.error "WhatsApp Webhook: MISMATCH! Mapping account #{target_account_id}, Candidate account #{candidate.account_id} in tenant #{target_tenant}."
              STDOUT.flush
              return head :ok
            end

            last_bot_message = Message.where(reference: candidate, entity: Message::ROLE_SYSTEM, status: Message::STATUS_NOT_ANSWERED).order(created_at: :desc).first

            Rails.logger.info "=== WEBHOOK DEBUG ==="
            Rails.logger.info "last_bot_message: #{last_bot_message&.id}"
            Rails.logger.info "last_bot_message.metadata: #{last_bot_message&.metadata&.inspect}"
            Rails.logger.info "last_bot_message.parent_message_id: #{last_bot_message&.parent_message_id}"
            Rails.logger.info "====================="
            STDOUT.flush

            unless last_bot_message
              Rails.logger.warn "WhatsApp Webhook: No pending system message found for candidate #{candidate.id} in tenant #{target_tenant}"
              STDOUT.flush
              return head :ok
            end

            recent_duplicate = Message.where(reference: candidate, entity: Message::ROLE_CANDIDATE)
                                      .where("created_at > ?", 2.minutes.ago)
                                      .where(content: message_text).exists?
            if recent_duplicate
              Rails.logger.info "⚠️  [WhatsApp Webhook] Duplicate message detected, skipping"
              STDOUT.flush
              return head :ok
            end

            metadata = last_bot_message&.metadata || {}
            metadata[:source] = "whatsapp"

            message = Message.create!(
              account_id: candidate.account_id,
              reference: candidate,
              parent_message: last_bot_message,
              content: message_text,
              entity:  Message::ROLE_CANDIDATE,
              status: Message::STATUS_NOT_ANSWERED,
              metadata: last_bot_message&.metadata || {},
              apply_id: last_bot_message&.apply_id,
              evaluation_id: last_bot_message&.evaluation_id
            )

            Rails.logger.info "WhatsApp Webhook: Message created successfully (id: #{message.id}, apply_id: #{message.apply_id}, evaluation_id: #{message.evaluation_id}) for candidate #{candidate.id} in tenant #{target_tenant}"

            # Enfileirar job para processar a resposta do candidato
            # Chatbot::ReplyProcessorJob.perform_later(message.id, candidate.account_id)
            Rails.logger.info "WhatsApp Webhook: Enqueued ReplyProcessorJob for message #{message.id}"
            Rails.logger.info "🏁 [WhatsApp Webhook] ===== PROCESSAMENTO CONCLUÍDO ====="
            STDOUT.flush

            head :ok
          rescue => e
            Rails.logger.error "❌ WhatsApp Webhook Error in tenant #{target_tenant rescue 'unknown'}: #{e.class} - #{e.message}\n#{e.backtrace.first(5).join("\n")}"
            STDOUT.flush
            head :ok
          ensure
            Apartment::Tenant.reset
            Rails.logger.info "🔄 [WhatsApp Webhook] Tenant reset complete"
            STDOUT.flush
          end
        end

        private

        def find_tenant_mapping(sender_phone)
          normalized_phone = normalize_phone(sender_phone)
          return nil if normalized_phone.blank?
          WhatsappTenantMapping.find_tenant_for_phone(normalized_phone)
        rescue => e
          Rails.logger.error "WhatsApp Webhook: Error finding tenant mapping for #{normalized_phone}: #{e.message}"
          nil
        end

        def find_candidate_for_message(sender_phone)
          normalized = normalize_phone(sender_phone)
          return if normalized.blank?

          variants = phone_variants(normalized)
          return if variants.empty?

          prioritized_candidate = Candidate
                                    .left_outer_joins(:evaluation_candidates)
                                    .where(is_deleted: false)
                                    .where("regexp_replace(candidates.mobile_phone, '\\D', '', 'g') IN (?)", variants)
                                    .where("evaluation_candidates.is_deleted IS NOT TRUE OR evaluation_candidates.id IS NULL")
                                    .order(Arel.sql("evaluation_candidates.updated_at DESC NULLS LAST"))
                                    .order(updated_at: :desc)
                                    .first

          return prioritized_candidate if prioritized_candidate

          Candidate
            .where(is_deleted: false)
            .where("regexp_replace(candidates.mobile_phone, '\\D', '', 'g') IN (?)", variants)
            .order(updated_at: :desc)
            .first
        end

        def phone_variants(phone)
          digits = phone.to_s.gsub(/\D/, "")
          variants = [ digits ]
          if digits.start_with?("55")
            trimmed = digits[2..]
            variants << trimmed if trimmed.present?
          end
          variants.uniq
        end

        def redirect_to_external_webhook(url, webhook_params)
          require "net/http"
          require "uri"

          Rails.logger.info "🚀 [REDIRECT] Iniciando redirecionamento..."
          Rails.logger.info "🚀 [REDIRECT] Target URL: #{url}"
          Rails.logger.info "🚀 [REDIRECT] Payload size: #{webhook_params.to_json.bytesize} bytes"
          STDOUT.flush

          uri = URI.parse(url)
          http = Net::HTTP.new(uri.host, uri.port)
          http.use_ssl = (uri.scheme == "https")
          http.open_timeout = 5
          http.read_timeout = 10

          request = Net::HTTP::Post.new(uri.path)
          request["Content-Type"] = "application/json"
          request.body = webhook_params.to_json

          Rails.logger.info "🚀 [REDIRECT] Sending POST request..."
          STDOUT.flush
          response = http.request(request)
          Rails.logger.info "✅ [REDIRECT] Response received:"
          Rails.logger.info "✅ [REDIRECT] Status: #{response.code}"
          Rails.logger.info "✅ [REDIRECT] Body: #{response.body[0..500]}"
          Rails.logger.info "✅ [REDIRECT] Headers: #{response.to_hash.inspect}"
          STDOUT.flush
        rescue => e
          Rails.logger.error "❌ [REDIRECT] ERRO ao redirecionar webhook!"
          Rails.logger.error "❌ [REDIRECT] Error class: #{e.class}"
          Rails.logger.error "❌ [REDIRECT] Error message: #{e.message}"
          Rails.logger.error "❌ [REDIRECT] Backtrace: #{e.backtrace.first(10).join("\n")}"
          STDOUT.flush
        end
      end
    end
  end
end
