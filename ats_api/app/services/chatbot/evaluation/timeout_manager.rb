# frozen_string_literal: true

module Chatbot
  module Evaluation
    class TimeoutManager
      DEFAULT_SESSION_TIMEOUT = 120
      DEFAULT_MAX_RETRY_ATTEMPTS = 1
      REMINDER_1_AFTER = 30.minutes
      REMINDER_2_AFTER = 1.hour
      RETRY_NEXT_DAY_AFTER = 24.hours

      REMINDER_1_TEXT = "Oi, ainda está aí?"
      REMINDER_2_TEXT = "Posso esperar mais um pouco..."
      TIMEOUT_MESSAGE = "Parece que você está ocupado. Sem problema! Amanhã tento contato novamente."
      RETRY_NEXT_DAY_TEMPLATE = "Oi %<name>s, tudo bem? Ontem paramos no meio. Quer continuar? Faltam %<remaining>d perguntas."
      PROCESS_CLOSED_MESSAGE = "O processo de triagem foi encerrado! Se tiver dúvidas, entre em contato com a empresa."

      def initialize(account_id:)
        @account_id = account_id
      end

      def call
        account = Account.find_by(id: @account_id)
        return log_and_return(:error, "Conta #{@account_id} não encontrada") unless account

        Apartment::Tenant.switch!(account.tenant)

        process_pending_messages
        process_retry_next_day if session_status_column_exists?

      rescue StandardError => e
        Rails.logger.error "❌ [TimeoutManager] Erro: #{e.class} - #{e.message}"
        Rails.logger.error e.backtrace.first(5).join("\n")
        raise
      end

      private

      def process_pending_messages
        messages = pending_messages.to_a
        messages.each do |message|
          process_message(message)
        rescue StandardError => e
          Rails.logger.error "❌ [TimeoutManager] Erro ao processar message #{message.id}: #{e.message}"
        end
      end

      def process_message(message)
        elapsed = Time.current - message.created_at
        metadata = (message.metadata || {}).with_indifferent_access

        evaluation_candidate = find_evaluation_candidate(message)
        unless evaluation_candidate
          return
        end
        if evaluation_candidate.completed?
          return
        end
        unless evaluation_candidate.session_active_or_pending?
          return
        end
        unless evaluation_candidate.evaluation.whatsapp_chatbot?
          return
        end

        timeout_minutes = job_screening_timeout(evaluation_candidate) || DEFAULT_SESSION_TIMEOUT
        if elapsed >= timeout_minutes.minutes
          process_timeout(message, evaluation_candidate, metadata)
        elsif elapsed >= REMINDER_2_AFTER
          unless reminder_2_sent?(metadata)
            send_reminder_2(message, evaluation_candidate, metadata)
          end
        elsif elapsed >= REMINDER_1_AFTER
          unless reminder_1_sent?(metadata)
            send_reminder_1(message, evaluation_candidate, metadata)
          end
        end
      end

      def process_timeout(message, evaluation_candidate, metadata)
        candidate = message.reference
        return unless candidate.is_a?(Candidate)
        return unless candidate.mobile_phone.present?

        message.update!(status: Message::STATUS_ANSWERED)

        question_index = [ metadata[:question_index].to_i, 0 ].max
        max_attempts = job_max_retry_attempts(evaluation_candidate) || DEFAULT_MAX_RETRY_ATTEMPTS
        already_retried = (evaluation_candidate.retry_attempts || 0) >= max_attempts
        new_status = already_retried ? :closed : :timeout

        attrs = {
          session_status: new_status,
          last_timeout_at: Time.current,
          timeout_count: (evaluation_candidate.timeout_count || 0) + 1,
          last_question_index: question_index
        }
        attrs[:completed] = true if already_retried

        evaluation_candidate.update!(attrs)

        if already_retried
          send_whatsapp(candidate.mobile_phone, PROCESS_CLOSED_MESSAGE)
        else
          send_whatsapp(candidate.mobile_phone, TIMEOUT_MESSAGE)
        end
      end

      def send_reminder_1(message, evaluation_candidate, metadata)
        send_reminder(message, evaluation_candidate, REMINDER_1_TEXT, :reminder_1_sent_at, metadata)
      end

      def send_reminder_2(message, evaluation_candidate, metadata)
        send_reminder(message, evaluation_candidate, REMINDER_2_TEXT, :reminder_2_sent_at, metadata)
      end

      def send_reminder(message, evaluation_candidate, text, metadata_key, metadata)
        candidate = message.reference
        return unless candidate.is_a?(Candidate)
        return unless candidate.mobile_phone.present?

        send_whatsapp(candidate.mobile_phone, text)

        message.update!(
          metadata: metadata.merge(metadata_key => Time.current.iso8601)
        )
        evaluation_candidate.update!(last_reminder_at: Time.current)
      end

      def process_retry_next_day
        candidates = EvaluationCandidate.timed_out_pending_retry.to_a
        candidates.each do |evaluation_candidate|
          send_retry_next_day(evaluation_candidate)
        rescue StandardError => e
          Rails.logger.error "❌ [TimeoutManager] Erro retry evaluation_candidate #{evaluation_candidate.id}: #{e.message}"
        end
      end

      def send_retry_next_day(evaluation_candidate)
        candidate = evaluation_candidate.candidate
        evaluation = evaluation_candidate.evaluation
        unless candidate&.mobile_phone.present?
          return
        end
        unless evaluation_candidate.apply_id.present?
          Rails.logger.info "⏭️ [TimeoutManager] Pulando retry ec #{evaluation_candidate.id}: apply_id ausente (obrigatório)"
          return
        end

        remaining = remaining_questions_count(evaluation_candidate)
        name = candidate.name.presence || "candidato"
        text = format(RETRY_NEXT_DAY_TEMPLATE, name: name, remaining: remaining)

        send_whatsapp(candidate.mobile_phone, text)

        question_index = [ evaluation_candidate.last_question_index || 0, 0 ].max
        question = evaluation.questions.where(is_deleted: false).order(position: :asc, id: :asc).offset(question_index).first
        metadata = {
          question_index: question_index,
          question_id: question&.id,
          evaluation_id: evaluation.id,
          apply_id: evaluation_candidate.apply_id,
          retry_sent_at: Time.current.iso8601
        }

        Message.create!(
          account_id: evaluation_candidate.account_id,
          reference: candidate,
          content: text,
          entity: Message::ROLE_SYSTEM,
          status: Message::STATUS_NOT_ANSWERED,
          apply_id: evaluation_candidate.apply_id,
          evaluation_id: evaluation.id,
          metadata: metadata
        )

        evaluation_candidate.update!(
          retry_attempts: (evaluation_candidate.retry_attempts || 0) + 1,
          session_status: :active
        )
      end

      def pending_messages
        sql = Message.sanitize_sql_array([ <<~SQL.squish, Message::ROLE_SYSTEM, Message::STATUS_NOT_ANSWERED, @account_id, 5.days.ago ])
          SELECT id FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY reference_id, evaluation_id ORDER BY created_at DESC) AS rn
            FROM messages
            WHERE reference_type = 'Candidate'
              AND entity = ?
              AND status = ?
              AND evaluation_id IS NOT NULL
              AND account_id = ?
              AND created_at >= ?
          ) sub WHERE rn = 1
        SQL
        ids = Message.connection.select_values(sql)
        return Message.none if ids.empty?

        Message.where(id: ids).order(created_at: :asc)
      end

      def find_evaluation_candidate(message)
        evaluation_id = message.evaluation_id || message.metadata&.dig("evaluation_id")
        candidate_id = message.reference_id
        apply_id = message.apply_id || message.metadata&.dig("apply_id")

        return nil unless evaluation_id && candidate_id

        scope = EvaluationCandidate.where(
          evaluation_id: evaluation_id,
          candidate_id: candidate_id,
          completed: false,
          is_deleted: false
        )
        scope = scope.where(apply_id: apply_id) if apply_id.present?
        scope.first
      end

      def reminder_1_sent?(metadata)
        metadata[:reminder_1_sent_at].present?
      end

      def reminder_2_sent?(metadata)
        metadata[:reminder_2_sent_at].present?
      end

      def remaining_questions_count(evaluation_candidate)
        total = evaluation_candidate.evaluation.questions.where(is_deleted: false).count
        answered = Answer.where(
          evaluation_id: evaluation_candidate.evaluation_id,
          candidate_id: evaluation_candidate.candidate_id
        ).count
        [ total - answered, 0 ].max
      end

      def send_whatsapp(phone, text)
        Meta::WhatsappService.send_text_message(phone, text)
      end

      def log_and_return(level, msg)
        Rails.logger.public_send(level, "⏳ [TimeoutManager] #{msg}")
      end

      def session_status_column_exists?
        ActiveRecord::Base.connection.column_exists?(:evaluation_candidates, :session_status)
      end

      def job_screening_timeout(evaluation_candidate)
        evaluation_candidate.job&.screening_timeout
      end

      def job_max_retry_attempts(evaluation_candidate)
        evaluation_candidate.job&.screening_max_attempts
      end
    end
  end
end
