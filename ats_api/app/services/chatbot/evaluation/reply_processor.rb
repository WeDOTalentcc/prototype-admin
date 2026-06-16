module Chatbot
  module Evaluation
    class ReplyProcessor
      def initialize(candidate_message_id, account_id = nil)
        if account_id.nil?
          account_id = Account.where(tenant: "public").first.id
        end

        Apartment::Tenant.switch!(Account.where(id: account_id).first.tenant)

        @candidate_message = Message.find(candidate_message_id)
        @bot_message = @candidate_message.parent_message
        @metadata = @bot_message.metadata.with_indifferent_access
        @apply = Apply.find(@metadata[:apply_id]) if @metadata[:apply_id]
        @apply ||= Apply.find_by(id: @bot_message[:apply_id])
        @evaluation = ::Evaluation.find(@metadata[:evaluation_id]) if @metadata[:evaluation_id]
        @evaluation ||= ::Evaluation.find(@bot_message[:evaluation_id])
        @candidate = @apply.candidate
        @job = @apply.job
        @ai_response = @metadata[:ai_response].presence || {}
        @evaluation_candidate = EvaluationCandidate.find_by(
          evaluation_id: @evaluation.id,
          candidate_id: @candidate.id
        )
      end

      def call
        Rails.logger.info "=== REPLY PROCESSOR START ==="
        Rails.logger.info "candidate_message.id: #{@candidate_message.id}"
        Rails.logger.info "bot_message.id: #{@bot_message.id}"
        Rails.logger.info "metadata: #{@metadata.inspect}"
        Rails.logger.info "already_processed?: #{already_processed?}"

        return if already_processed?

        # Prompt injection guard — block malicious candidate input
        guard_result = Security::PromptInjectionGuard.safe_process(@candidate_message.content)
        unless guard_result[:safe]
          Rails.logger.warn "[ReplyProcessor] Prompt injection blocked: pattern=#{guard_result[:detected_pattern]}, message_id=#{@candidate_message.id}"
          @candidate_message.update!(
            status: Message::STATUS_ANSWERED,
            metadata: (@candidate_message.metadata || {}).merge(blocked: true, blocked_reason: "prompt_injection", detected_pattern: guard_result[:detected_pattern])
          )
          return
        end

        current_question = find_question_by_index(@metadata[:question_index])
        Rails.logger.info "current_question: #{current_question&.id} - #{current_question&.title&.truncate(50)}"

        process_and_save_answer(current_question)

        next_question_index = @metadata[:question_index] + 1
        next_question = find_question_by_index(next_question_index)
        total_questions = @evaluation.questions.count

        Rails.logger.info "📊 [ReplyProcessor] Progresso: #{next_question_index}/#{total_questions} perguntas"
        Rails.logger.info "next_question_index: #{next_question_index}"
        Rails.logger.info "next_question: #{next_question&.id} - #{next_question&.title&.truncate(50) rescue 'nil'}"

        if next_question
          send_next_question(next_question, next_question_index)
        else
          Rails.logger.info "🎯 [ReplyProcessor] Não há mais perguntas - finalizando avaliação"
          Rails.logger.info "🎯 [ReplyProcessor] Total de perguntas respondidas: #{total_questions}"
          end_conversation
        end
        @bot_message.update!(status: Message::STATUS_ANSWERED)
        @candidate_message.update!(status: Message::STATUS_ANSWERED)
        Rails.logger.info "=== REPLY PROCESSOR END ==="
      end

      private

      def process_and_save_answer(question)
        return unless question
        Answer.create!(
          question: question,
          evaluation: @evaluation,
          candidate: @candidate,
          job: @job,
          apply: @apply,
          account_id: @apply.account_id,
          choices: { raw: @candidate_message.content },
          source: Answer.source_from_message(@candidate_message)
        )
      end

      def send_next_question(question, next_index)
        chat_ack = @ai_response[:chat_ack].presence || "Perfeito, vamos continuar!"
        response_to_candidate = @ai_response[:response_to_candidate].presence
        followup_question = @ai_response[:followup_question].presence

        parts = []
        parts << chat_ack if chat_ack.present?
        parts << response_to_candidate if response_to_candidate.present?
        parts << followup_question if followup_question.present?

        if followup_question.blank?
          question_text = [ question.title, question.description ].compact.join("\n").strip
          parts << question_text
        end

        message_content = parts.join("\n\n").strip

        if @candidate&.mobile_phone.present?
          Meta::WhatsappService.send_text_message(@candidate.mobile_phone, message_content)
        end

        # Debug
        Rails.logger.info "=== DEBUG send_next_question ==="
        Rails.logger.info "Chat ACK: #{chat_ack.inspect}"
        Rails.logger.info "Response to candidate: #{response_to_candidate.inspect}"
        Rails.logger.info "Followup: #{followup_question.inspect}"
        Rails.logger.info "================================"

        # Cria a mensagem no histórico
        Message.create!(
          account_id: @apply.account_id,
          reference: @candidate,
          parent_message: @candidate_message,
          content: message_content,
          entity: Message::ROLE_SYSTEM,
          status: Message::STATUS_NOT_ANSWERED,
          metadata: @metadata.merge(
            question_index: next_index,
            question_id: question.id,
            apply_id: @apply.id,
            evaluation_id: @evaluation.id,
            ai_response: @ai_response
          )
        )
      end

      def end_conversation
        Rails.logger.info "🏁 [ReplyProcessor] Finalizando avaliação"
        Rails.logger.info "🏁 [ReplyProcessor] Candidate: #{@candidate.id} - #{@candidate.name}"
        Rails.logger.info "🏁 [ReplyProcessor] Evaluation: #{@evaluation.id} - #{@evaluation.name}"
        Rails.logger.info "🏁 [ReplyProcessor] EvaluationCandidate ID: #{@evaluation_candidate&.id}"
        Rails.logger.info "🏁 [ReplyProcessor] EvaluationCandidate completed BEFORE: #{@evaluation_candidate&.completed}"

        final_msg = "Muito obrigado! Recebemos todas as respostas. Um recrutador entrará em contato em breve."
        Meta::WhatsappService.send_text_message(@candidate.mobile_phone, final_msg)

        @bot_message.update!(
          status: Message::STATUS_ANSWERED,
          metadata: @bot_message.metadata.merge(finished_at: Time.current)
        )

        if @evaluation_candidate
          @evaluation_candidate.update!(completed: true)
          Rails.logger.info "✅ [ReplyProcessor] EvaluationCandidate #{@evaluation_candidate.id} marcado como completed!"
          Rails.logger.info "✅ [ReplyProcessor] Isso deve disparar o callback get_ai_feedback"
        else
          Rails.logger.warn "⚠️ [ReplyProcessor] EvaluationCandidate não encontrado! Evaluation: #{@evaluation.id}, Candidate: #{@candidate.id}"
        end

        @apply.update!(evaluation_candidate_status: :answered) if @apply.respond_to?(:evaluation_candidate_status)

        Rails.logger.info "🏁 [ReplyProcessor] Finalização completa"
      end

      def find_question_by_index(index)
        return nil if index < 0
        @evaluation.questions.order(position: :asc, id: :asc).offset(index).first
      end

      def already_processed?
        @candidate_message.status == Message::STATUS_ANSWERED
      end
    end
  end
end
