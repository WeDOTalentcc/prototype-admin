# app/workers/evaluation_result_worker.rb
require "sneakers"

class EvaluationResultWorker
  HELP_KEYWORDS_MESSAGE = "Se houver qualquer problema, você pode digitar palavras-chave (ex: \"AJUDA\", \"#PROBLEMA\") e receberá retorno em até 24 horas.".freeze
  ISSUE_REPORT_RESPONSE_MESSAGE = "Desculpe pelo imprevisto! Nosso time foi notificado e entrará em contato em até 24 horas.".freeze
  include Sneakers::Worker

  from_queue "evaluation_responses",
             exchange: "evaluations_exchange",
             routing_key: "evaluation_response",
             ack: true,
             durable: true,
             exchange_type: :direct

  def work(raw_payload)
    puts "✅ [EvaluationResultWorker] Resposta recebida do Python!"

    data = JSON.parse(raw_payload).deep_symbolize_keys
    original_payload = data[:original_payload]
    ai_response = normalize_ai_response(data[:ai_response])

    account_id = original_payload[:account_id]
    account = Account.find_by(id: account_id)
    Apartment::Tenant.switch!(account.tenant)

    unless account
      puts "❌ Erro crítico: Conta com ID #{account_id} não encontrada. Descartando."
      return ack!
    end

    begin
      evaluation_candidate = EvaluationCandidate.find(original_payload[:evaluation_candidate_id])

      evaluation = evaluation_candidate.evaluation

      candidate = evaluation_candidate.candidate

      question = Question.find(original_payload[:question_id]) if original_payload[:question_id]

      avoid_answer = ai_response[:avoid_answer] || false

      custom_end_message = nil

      payload_for_frontend = {}

      if avoid_answer
        if evaluation.internal_chatbot?
          ActionCable.server.broadcast(
            EvaluationChannel.stream_name(account.uid, evaluation_candidate.uid),
            { question_id: original_payload[:question_id], avoid_answer: true }
          )
        end
        return ack!
      end

      if issue_report?(ai_response)
        handle_issue_report(account, evaluation_candidate, candidate, evaluation, original_payload, ai_response)
        return ack!
      end

      if !original_payload[:question_id] && evaluation.whatsapp_chatbot?
        if ai_response[:interested_job] == false && ai_response[:interested_job_msg].present?
          custom_end_message = ai_response[:interested_job_msg]
        end
        question = evaluation.questions.order(position: :asc).first
        content = ""
        content += "#{ai_response[:chat_ack]}" if ai_response[:chat_ack].present?
        content += "#{ai_response[:response_to_candidate]}\n\n" if ai_response[:response_to_candidate].present?

        send_first_question(question, candidate, evaluation_candidate, custom_end_message, content)
        return ack!
      end

      message = Message.find(original_payload[:message_id])
      if message.metadata&.dig("retry_sent_at").present? && evaluation.whatsapp_chatbot?
        handle_retry_ack(message, candidate, evaluation_candidate, original_payload, ai_response)
        return ack!
      end

      if ai_response[:changed_subject] == true && ai_response[:followup_needed] == false && ai_response[:response_to_candidate].present?
        puts "🟡 [EvaluationResultWorker] Changed subject detected — enviando apenas mensagem explicativa."

        Meta::WhatsappService.send_text_message(
          candidate.mobile_phone,
          ai_response[:response_to_candidate]
        )

        # cria a mensagem no histórico, mas não salva Answer
        Message.create!(
          account_id: account.id,
          reference: candidate,
          parent_message: Message.find(original_payload[:message_id]),
          content: ai_response[:response_to_candidate],
          entity: Message::ROLE_SYSTEM,
          status: Message::STATUS_NOT_ANSWERED,
          apply_id: evaluation_candidate.apply_id,
          evaluation_id: evaluation_candidate.evaluation_id,
          metadata: {
            question_index: Message.find(original_payload[:message_id]).metadata["question_index"],
            question_id: original_payload[:question_id],
            phone: candidate.mobile_phone,
            ai_response: ai_response
          }
        )

        return ack!
      end

      answer = Answer.find_or_initialize_by(
        evaluation_id: evaluation_candidate.evaluation_id,
        candidate_id: evaluation_candidate.candidate_id,
        question_id: original_payload[:question_id]
      )

      choices = answer.choices || []
      choices = [] unless choices.is_a?(Array)

      choices << {
        question: question.title,
        answer: original_payload[:candidate_answer],
        is_satisfactory: ai_response[:is_answer_satisfactory],
        followup_question: ai_response[:followup_question],
        response_to_candidate: ai_response[:response_to_candidate]
      }

      answer.update!(
        description: original_payload[:candidate_answer],
        title: question&.title,
        detail: question&.details,
        choices: choices,
        comments_response: ai_response,
        job_id: evaluation_candidate.job_id,
        apply_id: evaluation_candidate.apply_id,
        account_id: evaluation_candidate.account_id,
        user_id: evaluation_candidate.user_id,
        source: Answer.source_from_message(message)
      )

      if question.present?
        process_answer_scoring(answer, evaluation_candidate)
      else
        Rails.logger.info "⏭️  [EvaluationResultWorker] Pulando scoring - question ausente (question_id: #{original_payload[:question_id].inspect})"
      end

      message.update!(status: Message::STATUS_ANSWERED)

      if !ai_response[:is_answer_satisfactory] && ai_response[:followup_needed]
        content = ""
        content += ai_response[:response_to_candidate].to_s + "\n\n" if ai_response[:response_to_candidate].present?
        content += ai_response[:followup_question] if ai_response[:followup_question].present?
        payload_for_frontend = {
          followup_question: ai_response[:followup_question],
          response_to_candidate: ai_response[:response_to_candidate],
          content: content,
          question_id: original_payload[:question_id]
        }
      end

      if ai_response[:is_answer_satisfactory]
        answered_question_ids = Answer.where(
          evaluation_id: evaluation_candidate.evaluation_id,
          candidate_id: evaluation_candidate.candidate_id
        ).pluck(:question_id)
        questions = Question.where(evaluation_id: evaluation_candidate.evaluation_id, is_deleted: false)
                            .where.not(id: answered_question_ids)
                            .order(position: :asc)
                            .limit(1)
        next_question = questions.last

        chat_ack = ai_response[:chat_ack]
        chat_ack_is_none = chat_ack.to_s.strip.downcase == "none"
        chat_ack = nil if chat_ack_is_none

        content = ""

        if next_question
          content += chat_ack if chat_ack.present?
          question_text = [ next_question.title, next_question.description ].compact.join("\n").strip
          content += "\n\n" if content.present?
          content += question_text
        else
          content = "Muito obrigada pelas suas respostas! Foi um prazer conversar com você. Desejo muito sucesso no processo seletivo! 😊"
        end

        payload_for_frontend = {
          content: content,
          question_id: original_payload[:question_id],
          next_question: next_question,
          finished: next_question.nil?
        }
      end

      if !ai_response[:is_answer_satisfactory] && !ai_response[:interested_job]
        payload_for_frontend = {
          interested_job: false,
          content: ai_response[:interested_job_msg] || "Entendemos. Obrigado pelo seu tempo.",
          question_id: original_payload[:question_id],
          finished: true
        }
        custom_end_message = ai_response[:interested_job_msg] if ai_response[:interested_job_msg].present?
      end

      puts "------Payload for frontend: #{!ai_response[:is_answer_satisfactory] && !ai_response[:followup_needed] && ai_response[:next_question].present? && ai_response[:interested_job]}"

      if !ai_response[:is_answer_satisfactory] && !ai_response[:followup_needed] && ai_response[:next_question].present? && ai_response[:interested_job]
        db_answered_ids = Answer.where(
          evaluation_id: evaluation_candidate.evaluation_id,
          candidate_id: evaluation_candidate.candidate_id
        ).pluck(:question_id)
        db_next = Question.where(evaluation_id: evaluation_candidate.evaluation_id, is_deleted: false)
                          .where.not(id: db_answered_ids)
                          .order(position: :asc)
                          .first

        if db_next
          content = ""
          content += "#{ai_response[:chat_ack]}" if ai_response[:chat_ack].present?
          question_text = [ db_next.title, db_next.description ].compact.join("\n").strip
          content += "\n\n" if content.present?
          content += question_text

          payload_for_frontend = {
            content: content,
            question_id: original_payload[:question_id],
            next_question: db_next,
            finished: false
          }
        else
          payload_for_frontend = {
            content: "Muito obrigada pelas suas respostas! Foi um prazer conversar com você. Desejo muito sucesso no processo seletivo! 😊",
            question_id: original_payload[:question_id],
            next_question: nil,
            finished: true
          }
        end
      end

      if evaluation.internal_chatbot?
        ActionCable.server.broadcast(
          EvaluationChannel.stream_name(account.uid, evaluation_candidate.uid),
          payload_for_frontend
        )
        if payload_for_frontend[:finished]
          apply = evaluation_candidate.apply
          if apply.respond_to?(:evaluation_candidate_status)
            apply.update_columns(
              evaluation_candidate_status: Message::STATUS_ANSWERED,
              updated_at: Time.current
            )
          end

          if evaluation_candidate
            evaluation_candidate.update!(completed: true)
            evaluation_candidate.send_completion_notifications
            apply.update_alerts("approve", "create")
            evaluation_candidate.create_finish_evaluation_candidate_log

            if evaluation_candidate.completed? && evaluation_candidate.account_id
              Evaluations::PerCandidateNotificationJob.perform_later(evaluation_candidate.id, evaluation_candidate.account_id)
            end
          end
        end
      end

      if evaluation.whatsapp_chatbot?
        if payload_for_frontend[:finished]
          end_conversation(candidate, message, evaluation_candidate, custom_end_message)
          return ack!
        end
        Message.create!(
          account_id: account.id,
          reference: candidate,
          parent_message: message,
          content: payload_for_frontend[:content],
          entity: Message::ROLE_SYSTEM,
          status: Message::STATUS_NOT_ANSWERED,
          apply_id: evaluation_candidate.apply_id,
          evaluation_id: evaluation_candidate.evaluation_id,
          metadata: {
            question_index: (message.metadata&.dig("question_index") || 0).to_i + 1,
            question_id: (
              payload_for_frontend[:next_question].is_a?(Hash) ?
              payload_for_frontend[:next_question][:id] :
              payload_for_frontend[:next_question]&.id
            ) || original_payload[:question_id],
            phone: candidate.mobile_phone
          }
        )
        Meta::WhatsappService.send_text_message(
          candidate.mobile_phone,
          payload_for_frontend[:content]
        ) if payload_for_frontend[:content].present? && candidate&.mobile_phone.present?
      end

      puts "✅ Resposta processada e enviada para o frontend no tenant '#{account.tenant}'."
      ack!

    rescue => e
      puts "❌ Erro ao processar mensagem no tenant '#{account.tenant}': #{e.class.name} - #{e.message}"
      puts e.backtrace.first(5).join("\n")
      reject!
    end
  end

  def normalize_ai_response(ai_response)
    return {} if ai_response.blank?
    return ai_response.deep_symbolize_keys if ai_response.is_a?(Hash)
    parsed = JSON.parse(ai_response.to_s)
    parsed.is_a?(Hash) ? parsed.deep_symbolize_keys : {}
  rescue StandardError
    {}
  end

  def issue_report?(ai_response)
    val = ai_response[:is_issue_report] || ai_response["is_issue_report"]
    val == true || val == "true" || val.to_s.casecmp("true").zero? || val == 1
  end

  def handle_issue_report(account, evaluation_candidate, candidate, evaluation, original_payload, ai_response)
    Rails.logger.info "🔄 [EvaluationResultWorker] is_issue_report detectado — criando Issue e encerrando avaliação"

    message = Message.find(original_payload[:message_id])
    issue_text = original_payload[:candidate_answer].to_s.presence || ai_response[:issue_description].to_s.presence || "Problema reportado pelo candidato"

    Issue.create!(
      text: issue_text,
      type: Issue.types[:screening],
      status: Issue.statuses[:received],
      account_id: evaluation_candidate.account_id,
      candidate_id: candidate.id,
      evaluation_id: evaluation_candidate.evaluation_id,
      evaluation_candidate_id: evaluation_candidate.id,
      question_id: original_payload[:question_id],
      job_id: evaluation_candidate.job_id,
      reference_type: "Message",
      reference_id: message.id
    )

    evaluation_candidate.update!(completed: true)
    message.update!(status: Message::STATUS_ANSWERED, metadata: message.metadata.to_h.merge(finished_at: Time.current))

    apply = evaluation_candidate.apply
    if apply&.respond_to?(:evaluation_candidate_status)
      apply.update_columns(evaluation_candidate_status: Message::STATUS_ANSWERED, updated_at: Time.current)
    end

    if evaluation.whatsapp_chatbot? && candidate.mobile_phone.present?
      Meta::WhatsappService.send_text_message(candidate.mobile_phone, ISSUE_REPORT_RESPONSE_MESSAGE)
    end

    if evaluation.internal_chatbot?
      ActionCable.server.broadcast(
        EvaluationChannel.stream_name(account.uid, evaluation_candidate.uid),
        { finished: true, content: ISSUE_REPORT_RESPONSE_MESSAGE }
      )
    end

    Rails.logger.info "✅ [EvaluationResultWorker] Issue criado e mensagem enviada ao candidato"
  rescue StandardError => e
    Rails.logger.error "❌ [EvaluationResultWorker] Erro ao processar issue report: #{e.class} - #{e.message}"
    Rails.logger.error e.backtrace.first(5).join("\n")
    raise
  end

  def end_conversation(candidate, message, evaluation_candidate, custom_message = nil)
    final_msg = "Muito obrigado! Recebemos todas as respostas. Um recrutador entrará em contato em breve."
    final_msg = custom_message if custom_message.present?
    Meta::WhatsappService.send_text_message(candidate.mobile_phone, final_msg)
    message.update!(status: Message::STATUS_ANSWERED, metadata: message.metadata.merge(finished_at: Time.current))

    Message.where(
      reference_type: "Candidate",
      reference_id: candidate.id,
      evaluation_id: evaluation_candidate.evaluation_id,
      entity: Message::ROLE_SYSTEM,
      status: Message::STATUS_NOT_ANSWERED
    ).update_all(status: Message::STATUS_ANSWERED)

    apply = evaluation_candidate.apply

    if apply.respond_to?(:evaluation_candidate_status)
      apply.update_columns(
        evaluation_candidate_status: Message::STATUS_ANSWERED,
        updated_at: Time.current
      )
    end

    if evaluation_candidate
      evaluation_candidate.update!(completed: true)
      evaluation_candidate.send_completion_notifications
      apply.update_alerts("approve", "create")
      evaluation_candidate.create_finish_evaluation_candidate_log

      if evaluation_candidate.completed? && evaluation_candidate.account_id
        Evaluations::PerCandidateNotificationJob.perform_later(evaluation_candidate.id, evaluation_candidate.account_id)
      end
    end
  end

  def process_answer_scoring(answer, evaluation_candidate)
    score_result = Evaluations::ScoreCalculatorService.call(answer: answer)
    answer.reload
    aggregate_result = Evaluations::EvaluationAggregateService.call(evaluation_candidate: evaluation_candidate)
  rescue StandardError => e
    Rails.logger.warn("[EvaluationResultWorker] Failed to process scoring for answer #{answer.id}: #{e.message}")
    Rails.logger.warn(e.backtrace.first(5).join("\n"))
  end

  def handle_retry_ack(message, candidate, evaluation_candidate, original_payload, ai_response)
    retry_bot_message = message.parent_message
    retry_bot_message.update!(status: Message::STATUS_ANSWERED)
    message.update!(status: Message::STATUS_ANSWERED)

    question_index = retry_bot_message.metadata["question_index"].to_i
    question = evaluation_candidate.evaluation.questions
      .where(is_deleted: false)
      .order(position: :asc, id: :asc)
      .offset(question_index)
      .first

    return unless question

    chat_ack = ai_response[:chat_ack].presence || "Perfeito, vamos continuar!"
    question_text = [ question.title, question.description ].compact.join("\n").strip
    content = "#{chat_ack}\n\n#{question_text}"

    Meta::WhatsappService.send_text_message(candidate.mobile_phone, content)

    Message.create!(
      account_id: evaluation_candidate.account_id,
      reference: candidate,
      parent_message: message,
      content: content,
      entity: Message::ROLE_SYSTEM,
      status: Message::STATUS_NOT_ANSWERED,
      apply_id: evaluation_candidate.apply_id,
      evaluation_id: evaluation_candidate.evaluation_id,
      metadata: {
        question_index: question_index,
        question_id: question.id,
        phone: candidate.mobile_phone,
        ai_response: ai_response
      }
    )
  end

  def send_first_question(question, candidate, evaluation_candidate, custom_end_message = nil, response_to_candidate = nil)
    evaluation = evaluation_candidate.evaluation

    if evaluation.introduction_details.present? && candidate.mobile_phone.present?
      job = evaluation_candidate.job
      account = evaluation_candidate.account
      entities = { candidate: candidate, job: job, account: account }.compact
      introduction_content = Dispatch.replace_tags(evaluation.introduction_details, entities)

      Meta::WhatsappService.send_text_message(candidate.mobile_phone, introduction_content)
      Message.create!(
        account_id: evaluation_candidate.account_id,
        reference: candidate,
        content: introduction_content,
        entity: Message::ROLE_SYSTEM,
        status: Message::STATUS_NOT_ANSWERED,
        metadata: { question_index: -1, introduction_details: true },
        apply_id: evaluation_candidate.apply_id,
        evaluation_id: evaluation_candidate.evaluation_id,
      )
    end

    if custom_end_message.present?
      Meta::WhatsappService.send_text_message(candidate.mobile_phone, custom_end_message)
      Message.create!(
        account_id: evaluation_candidate.account_id,
        reference: candidate,
        content: custom_end_message,
        entity: Message::ROLE_SYSTEM,
        status: Message::STATUS_NOT_ANSWERED,
        metadata: { question_index: 0, question_id: question.id, finished_at: Time.current },
        apply_id: evaluation_candidate.apply_id,
        evaluation_id: evaluation_candidate.evaluation_id,
      )
      apply = evaluation_candidate.apply

      if apply.respond_to?(:evaluation_candidate_status)
        apply.update_columns(
          evaluation_candidate_status: Message::STATUS_ANSWERED,
          updated_at: Time.current
        )
      end

      if evaluation_candidate
        evaluation_candidate.update!(completed: true)
        # evaluation_candidate.send_completion_notifications
      end
      return
    end
    message_content = ""
    unless response_to_candidate.to_s.include?(HELP_KEYWORDS_MESSAGE)
      message_content += "#{HELP_KEYWORDS_MESSAGE}\n\n"
    end
    message_content += response_to_candidate.to_s + "\n\n" if response_to_candidate.present?
    question_text = [ question.title, question.description ].compact.join("\n").strip
    description_already_in_content = question.description.present? &&
      response_to_candidate.to_s.include?(question.description.to_s.strip)

    if description_already_in_content
      message_content = message_content.strip
      Meta::WhatsappService.send_text_message(candidate.mobile_phone, message_content)
      Message.create!(
        account_id: evaluation_candidate.account_id,
        reference: candidate,
        content: message_content,
        entity: Message::ROLE_SYSTEM,
        status: Message::STATUS_NOT_ANSWERED,
        apply_id: evaluation_candidate.apply_id,
        evaluation_id: evaluation_candidate.evaluation_id,
        metadata: { question_index: 0, question_id: question.id, welcome: true },
      )
    else
      Meta::WhatsappService.send_text_message(candidate.mobile_phone, message_content)
      Message.create!(
        account_id: evaluation_candidate.account_id,
        reference: candidate,
        content: message_content,
        entity: Message::ROLE_SYSTEM,
        status: Message::STATUS_ANSWERED,
        apply_id: evaluation_candidate.apply_id,
        evaluation_id: evaluation_candidate.evaluation_id,
        metadata: { question_index: -1, welcome: true },
      )
      Meta::WhatsappService.send_text_message(candidate.mobile_phone, question_text)
      Message.create!(
        account_id: evaluation_candidate.account_id,
        reference: candidate,
        content: question_text,
        entity: Message::ROLE_SYSTEM,
        status: Message::STATUS_NOT_ANSWERED,
        metadata: { question_index: 0, question_id: question.id },
        apply_id: evaluation_candidate.apply_id,
        evaluation_id: evaluation_candidate.evaluation_id,
      )
    end
  end
end
