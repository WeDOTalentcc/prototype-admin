module Chatbot
  module Evaluation
    class Starter
      def initialize(apply_id:, evaluation_id:)
        @apply = Apply.find(apply_id)
        @evaluation = ::Evaluation.find(evaluation_id)
        @candidate = @apply.candidate
        @job = @apply.job
      end

      def call
        normalized_phone = normalize_phone(@candidate.mobile_phone)
        unless normalized_phone.present?
          Rails.logger.info("Starter: skip no phone apply=#{@apply.id} candidate=#{@candidate.id}")
          return
        end
        unless @evaluation.respond_to?(:whatsapp_chatbot?) ? @evaluation.whatsapp_chatbot? : @evaluation.is_chatbot?
          Rails.logger.info("Starter: skip evaluation not whatsapp apply=#{@apply.id} evaluation=#{@evaluation.id} channel=#{@evaluation.try(:chatbot_channel)} is_chatbot=#{@evaluation.is_chatbot?}")
          return
        end

        register_phone_to_tenant_mapping(normalized_phone)

        response = send_initial_message!(normalized_phone)
        if success_response?(response)
          create_bot_message_log!(normalized_phone, provider_message_id(response))
        else
          Rails.logger.warn("Starter: initial send failed apply=#{@apply.id} evaluation=#{@evaluation.id} candidate=#{@candidate.id}")
        end
      end

      private

      def send_initial_message!(phone)
        Meta::WhatsappService.send_message_by_template(
          phone,
          template_name,
          "pt_BR",
          build_components
        )
      end

      def create_bot_message_log!(phone, provider_id)
        Message.create!(
          account_id: @apply.account_id,
          reference: @candidate,
          apply_id: @apply.id,
          evaluation_id: @evaluation.id,
          content: initial_message_content,
          entity: Message::ROLE_SYSTEM,
          status: Message::STATUS_NOT_ANSWERED,
          metadata: {
            apply_id: @apply.id,
            evaluation_id: @evaluation.id,
            question_index: -1,
            phone: phone,
            provider_message_id: provider_id
          }
        )
      end

      def template_name
        "evaluations"
      end

      def build_components
        parameters = if template_name == "evaluations"
                       privacy_suffix = "Gostaríamos de confirmar seu interesse e seguir com algumas perguntas conduzidas pela LIA, nossa assistente de recrutamento com inteligência artificial. Ao continuar, voce concorda com nossa Politica de Privacidade em #{privacy_policy_url}. Responda 'NÃO' se não deseja participar."
                       [
                         { type: "text", text: @candidate.name.split.first },
                         { type: "text", text: @job.title },
                         { type: "text", text: privacy_suffix }
                       ]
        else
                       [ { type: "text", text: @job.title } ]
        end
        [ { type: "body", parameters: parameters } ]
      end

      def privacy_policy_url
        Rails.env.production? ? "https://wedotalent.cc/terms/" : "http://localhost:3000/terms/"
      end

      def initial_message_content
        first_name = @candidate.name.to_s.split.first
        message = "Olá #{first_name}, tudo bem?\n" \
                  "Estamos fazendo uma triagem inicial para a vaga de #{@job.title}.\n" \
                  "Gostaríamos de confirmar seu interesse e seguir com algumas perguntas através do nosso assistente virtual. " \
                  "Você pode responder agora???\n\n"

        message += "Ao continuar, você concorda com nossa Politica de Privacidade em #{privacy_policy_url}. Responda 'NAO' se não deseja participar."

        message
      end

      def normalize_phone(phone)
        return if phone.blank?
        digits = phone.gsub(/\D/, "")
        if digits.length == 11 && !digits.start_with?("55")
          "55#{digits}"
        else
          digits
        end
      end

      def success_response?(response)
        response.respond_to?(:success?) ? response.success? : true
      rescue => e
        Rails.logger.error("Starter success_response? error: #{e.class} #{e.message}")
        false
      end

      def provider_message_id(response)
        response.respond_to?(:body) ? response.body.dig("messages", 0, "id") : nil rescue nil
      end

      def register_phone_to_tenant_mapping(phone)
        WhatsappTenantMapping.upsert_mapping(
          phone_number: phone,
          account_id: @apply.account_id
        )
        Rails.logger.info("Starter: Registered phone mapping for #{phone} to account #{@apply.account_id}")
      rescue => e
        Rails.logger.error("Starter: Failed to register phone mapping for #{phone}: #{e.message}")
      end
    end
  end
end
