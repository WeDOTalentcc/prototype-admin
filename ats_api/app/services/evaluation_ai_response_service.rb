# frozen_string_literal: true

# Service to process AI Evaluation response
# Replaces EvaluationResultWorker allowing the Agent
# to make a direct HTTP call instead of using RabbitMQ
class EvaluationAiResponseService
  class IssueReportDetected < StandardError; end
  Result = Struct.new(:success?, :data, :error, keyword_init: true) do
    def self.success(data:)
      new(success?: true, data: data, error: nil)
    end

    def self.failure(error:)
      new(success?: false, data: nil, error: error)
    end
  end

  def initialize(original_payload:, ai_response:, chatbot_channel: nil)
    @original_payload = original_payload.to_h.deep_symbolize_keys
    @ai_response = parse_ai_response(ai_response)
    @chatbot_channel = chatbot_channel || determine_channel
  end

  def call
    setup_tenant!
    load_entities!

    return handle_avoid_answer if @ai_response[:avoid_answer]
    if is_issue_report?
      Rails.logger.info("[EvaluationAIResponseService] is_issue_report detectado, encerrando avaliação e criando Issue")
      return handle_issue_report
    end
    return handle_first_question if first_question_scenario?
    return handle_changed_subject if changed_subject_scenario?

    process_answer!
    determine_next_action!
    send_to_frontend!

    Result.success(data: build_response_data)
  rescue IssueReportDetected
    handle_issue_report
  rescue ActiveRecord::RecordNotFound => e
    Rails.logger.error("[EvaluationAIResponseService] Record not found: #{e.message}")
    Result.failure(error: e.message)
  rescue StandardError => e
    Rails.logger.error("[EvaluationAIResponseService] Error: #{e.class.name} - #{e.message}")
    Rails.logger.error(e.backtrace.first(10).join("\n"))
    Result.failure(error: e.message)
  end

  private

  # ============================================================
  # SETUP & LOADING
  # ============================================================

  def setup_tenant!
    @account = Account.find(@original_payload[:account_id])
    Apartment::Tenant.switch!(@account.tenant)
    Rails.logger.info("[EvaluationAIResponseService] Switched to tenant: #{@account.tenant}")
  end

  def load_entities!
    @evaluation_candidate = EvaluationCandidate.find(@original_payload[:evaluation_candidate_id])
    @evaluation = @evaluation_candidate.evaluation
    @candidate = @evaluation_candidate.candidate
    @question = Question.find_by(id: @original_payload[:question_id]) if @original_payload[:question_id]
    @message = Message.find(@original_payload[:message_id]) if @original_payload[:message_id]
  end

  def determine_channel
    return "whatsapp" if @evaluation&.whatsapp_chatbot?
    return "internal" if @evaluation&.internal_chatbot?
    @original_payload[:chatbot_channel] || "internal"
  end

  # ============================================================
  # SCENARIO CHECKS
  # ============================================================

  def first_question_scenario?
    @original_payload[:question_id].nil? && whatsapp_channel?
  end

  def changed_subject_scenario?
    return false unless @ai_response[:changed_subject] == true
    return false if @ai_response[:followup_needed] == true
    @ai_response[:response_to_candidate].present?
  end

  def whatsapp_channel?
    @evaluation&.whatsapp_chatbot? || @chatbot_channel == "whatsapp"
  end

  def parse_ai_response(ai_response)
    return {} if ai_response.blank?
    h = ai_response.is_a?(String) ? JSON.parse(ai_response) : ai_response.to_h
    h.deep_symbolize_keys
  rescue StandardError => e
    Rails.logger.warn("[EvaluationAIResponseService] Failed to parse ai_response: #{e.message}")
    {}
  end

  def is_issue_report?
    val = @ai_response[:is_issue_report] || @ai_response["is_issue_report"]
    truthy?(val)
  end

  def truthy?(val)
    return false if val.nil?
    return true if val == true
    return true if val == "true" || val.to_s.casecmp("true").zero?
    return true if val == 1 || val.to_s == "1"
    false
  end

  def internal_channel?
    @evaluation&.internal_chatbot? || @chatbot_channel == "internal"
  end

  # ============================================================
  # HANDLERS PARA CENÁRIOS ESPECIAIS
  # ============================================================

  def handle_avoid_answer
    Rails.logger.info("[EvaluationAIResponseService] Handling avoid_answer scenario")

    if internal_channel?
      ActionCable.server.broadcast(
        EvaluationChannel.stream_name(@account.uid, @evaluation_candidate.uid),
        { question_id: @original_payload[:question_id], avoid_answer: true }
      )
    end

    Result.success(data: {
      evaluation_candidate_id: @evaluation_candidate.id,
      avoided: true,
      finished: false
    })
  end

  HELP_KEYWORDS_MESSAGE = "Se houver qualquer problema, você pode digitar palavras-chave (ex: \"AJUDA\", \"#PROBLEMA\") e receberá retorno em até 24 horas.".freeze
  ISSUE_REPORT_RESPONSE_MESSAGE = "Desculpe pelo imprevisto! Nosso time foi notificado e entrará em contato em até 24 horas.".freeze

  def handle_issue_report
    Rails.logger.info("[EvaluationAIResponseService] Handling is_issue_report scenario")

    issue_text = @original_payload[:candidate_answer].to_s.presence ||
                 @ai_response[:issue_description].to_s.presence ||
                 "Problema reportado pelo candidato"

    Issue.create!(
      text: issue_text,
      type: Issue.types[:screening],
      status: Issue.statuses[:received],
      account_id: @evaluation_candidate.account_id,
      candidate_id: @candidate.id,
      evaluation_id: @evaluation_candidate.evaluation_id,
      evaluation_candidate_id: @evaluation_candidate.id,
      question_id: @original_payload[:question_id],
      job_id: @evaluation_candidate.job_id,
      reference_type: "Message",
      reference_id: @message&.id.to_i
    )

    @evaluation_candidate.update!(completed: true)

    @message&.update!(
      status: Message::STATUS_ANSWERED,
      metadata: (@message.metadata || {}).merge(finished_at: Time.current)
    )

    apply = @evaluation_candidate.apply
    if apply&.respond_to?(:evaluation_candidate_status)
      apply.update_columns(
        evaluation_candidate_status: Message::STATUS_ANSWERED,
        updated_at: Time.current
      )
    end

    if whatsapp_channel? && @candidate.mobile_phone.present?
      Meta::WhatsappService.send_text_message(@candidate.mobile_phone, ISSUE_REPORT_RESPONSE_MESSAGE)
    end

    if internal_channel?
      ActionCable.server.broadcast(
        EvaluationChannel.stream_name(@account.uid, @evaluation_candidate.uid),
        { finished: true, content: ISSUE_REPORT_RESPONSE_MESSAGE }
      )
    end

    Rails.logger.info("[EvaluationAIResponseService] Issue criado e mensagem enviada ao candidato")

    Result.success(data: {
      evaluation_candidate_id: @evaluation_candidate.id,
      issue_report_handled: true,
      finished: true
    })
  rescue StandardError => e
    Rails.logger.error("[EvaluationAIResponseService] Erro ao processar issue report: #{e.class} - #{e.message}")
    raise
  end

  def handle_first_question
    Rails.logger.info("[EvaluationAIResponseService] Handling first question scenario (WhatsApp)")

    custom_end_message = nil
    if @ai_response[:interested_job] == false && @ai_response[:interested_job_msg].present?
      custom_end_message = @ai_response[:interested_job_msg]
    end

    question = @evaluation.questions.order(position: :asc).first
    content = ""
    content += @ai_response[:chat_ack].to_s if @ai_response[:chat_ack].present?
    content += "#{@ai_response[:response_to_candidate]}\n\n" if @ai_response[:response_to_candidate].present?

    send_first_question(question, custom_end_message, content)

    Result.success(data: {
      evaluation_candidate_id: @evaluation_candidate.id,
      first_question_sent: true,
      finished: custom_end_message.present?
    })
  end

  def handle_changed_subject
    Rails.logger.info("[EvaluationAIResponseService] Handling changed_subject scenario")

    # Envia mensagem explicativa via WhatsApp
    Meta::WhatsappService.send_text_message(
      @candidate.mobile_phone,
      @ai_response[:response_to_candidate]
    )

    # Cria mensagem no histórico, mas não salva Answer
    Message.create!(
      account_id: @account.id,
      reference: @candidate,
      parent_message: @message,
      content: @ai_response[:response_to_candidate],
      entity: Message::ROLE_SYSTEM,
      status: Message::STATUS_NOT_ANSWERED,
      apply_id: @evaluation_candidate.apply_id,
      evaluation_id: @evaluation_candidate.evaluation_id,
      metadata: {
        question_index: @message&.metadata&.[]("question_index"),
        question_id: @original_payload[:question_id],
        phone: @candidate.mobile_phone,
        ai_response: @ai_response
      }
    )

    Result.success(data: {
      evaluation_candidate_id: @evaluation_candidate.id,
      changed_subject_handled: true,
      finished: false
    })
  end

  # ============================================================
  # PROCESSAMENTO PRINCIPAL
  # ============================================================

  def process_answer!
    raise IssueReportDetected if is_issue_report?

    Rails.logger.info("[EvaluationAIResponseService] Processing answer for question_id: #{@question&.id}")

    @answer = Answer.find_or_initialize_by(
      evaluation_id: @evaluation_candidate.evaluation_id,
      candidate_id: @evaluation_candidate.candidate_id,
      question_id: @original_payload[:question_id]
    )

    choices = @answer.choices || []
    choices = [] unless choices.is_a?(Array)

    choices << {
      question: @question&.title,
      answer: @original_payload[:candidate_answer],
      is_satisfactory: @ai_response[:is_answer_satisfactory],
      followup_question: @ai_response[:followup_question],
      response_to_candidate: @ai_response[:response_to_candidate]
    }

    @answer.update!(
      description: @original_payload[:candidate_answer],
      title: @question&.title,
      detail: @question&.details,
      choices: choices,
      comments_response: @ai_response,
      job_id: @evaluation_candidate.job_id,
      apply_id: @evaluation_candidate.apply_id,
      account_id: @evaluation_candidate.account_id,
      user_id: @evaluation_candidate.user_id,
      source: Answer.source_from_message(@message)
    )

    calculate_scores_for_answer!

    # Atualiza status da mensagem original
    @message&.update!(status: Message::STATUS_ANSWERED)
  end

  def calculate_scores_for_answer!
    score_result = Evaluations::ScoreCalculatorService.call(answer: @answer)
    unless score_result.success?
      Rails.logger.warn("[EvaluationAIResponseService] ScoreCalculatorService failed for answer #{@answer.id}: #{score_result.error}")
      return
    end

    aggregate_result = Evaluations::EvaluationAggregateService.call(evaluation_candidate: @evaluation_candidate)
    return if aggregate_result.success?

    Rails.logger.warn("[EvaluationAIResponseService] EvaluationAggregateService failed for evaluation_candidate #{@evaluation_candidate.id}: #{aggregate_result.error}")
  end

  def determine_next_action!
    @payload_for_frontend = {}
    @custom_end_message = nil
    @finished = false

    if followup_needed?
      handle_followup_action
    elsif answer_satisfactory?
      handle_satisfactory_action
    elsif not_interested?
      handle_not_interested_action
    elsif next_question_available?
      handle_next_question_action
    end
  end

  # ============================================================
  # ACTION HANDLERS
  # ============================================================

  def followup_needed?
    !@ai_response[:is_answer_satisfactory] && @ai_response[:followup_needed]
  end

  def handle_followup_action
    Rails.logger.info("[EvaluationAIResponseService] Followup needed")

    content = ""
    content += @ai_response[:response_to_candidate].to_s + "\n\n" if @ai_response[:response_to_candidate].present?
    content += @ai_response[:followup_question].to_s if @ai_response[:followup_question].present?

    @payload_for_frontend = {
      followup_question: @ai_response[:followup_question],
      response_to_candidate: @ai_response[:response_to_candidate],
      content: content,
      question_id: @original_payload[:question_id]
    }
  end

  def answer_satisfactory?
    @ai_response[:is_answer_satisfactory]
  end

  def handle_satisfactory_action
    Rails.logger.info("[EvaluationAIResponseService] Answer satisfactory, finding next question")

    answered_question_ids = Answer.where(
      evaluation_id: @evaluation_candidate.evaluation_id,
      candidate_id: @evaluation_candidate.candidate_id
    ).pluck(:question_id)

    next_question = Question.where(evaluation_id: @evaluation_candidate.evaluation_id, is_deleted: false)
                            .where.not(id: answered_question_ids)
                            .order(position: :asc)
                            .first

    content = ""
    content += @ai_response[:chat_ack].to_s if @ai_response[:chat_ack].present?

    @payload_for_frontend = {
      content: content,
      question_id: @original_payload[:question_id],
      next_question: next_question,
      finished: next_question.nil?
    }

    @finished = next_question.nil?
  end

  def not_interested?
    !@ai_response[:is_answer_satisfactory] && !@ai_response[:interested_job]
  end

  def handle_not_interested_action
    Rails.logger.info("[EvaluationAIResponseService] Candidate not interested")

    @payload_for_frontend = {
      interested_job: false,
      content: @ai_response[:interested_job_msg] || "Entendemos. Obrigado pelo seu tempo.",
      question_id: @original_payload[:question_id],
      finished: true
    }
    @custom_end_message = @ai_response[:interested_job_msg] if @ai_response[:interested_job_msg].present?
    @finished = true
  end

  def next_question_available?
    !@ai_response[:is_answer_satisfactory] &&
    !@ai_response[:followup_needed] &&
    @ai_response[:next_question].present? &&
    @ai_response[:interested_job]
  end

  def handle_next_question_action
    Rails.logger.info("[EvaluationAIResponseService] Moving to next question from AI")

    content = ""
    content += @ai_response[:chat_ack].to_s if @ai_response[:chat_ack].present?

    @payload_for_frontend = {
      content: content,
      question_id: @original_payload[:question_id],
      next_question: @ai_response[:next_question],
      finished: false
    }
  end

  # ============================================================
  # ENVIO PARA FRONTEND
  # ============================================================

  def send_to_frontend!
    if internal_channel?
      send_to_internal_chatbot!
    elsif whatsapp_channel?
      send_to_whatsapp!
    end
  end

  def send_to_internal_chatbot!
    Rails.logger.info("[EvaluationAIResponseService] Broadcasting to internal chatbot")

    ActionCable.server.broadcast(
      EvaluationChannel.stream_name(@account.uid, @evaluation_candidate.uid),
      @payload_for_frontend
    )

    finalize_evaluation! if @finished
  end

  def send_to_whatsapp!
    Rails.logger.info("[EvaluationAIResponseService] Sending to WhatsApp")

    if @finished
      end_conversation(@custom_end_message)
      return
    end

    # Cria nova mensagem com próxima pergunta
    Message.create!(
      account_id: @account.id,
      reference: @candidate,
      parent_message: @message,
      content: @payload_for_frontend[:content],
      entity: Message::ROLE_SYSTEM,
      status: Message::STATUS_NOT_ANSWERED,
      apply_id: @evaluation_candidate.apply_id,
      evaluation_id: @evaluation_candidate.evaluation_id,
      metadata: {
        question_index: (@message&.metadata&.[]("question_index") || 0) + 1,
        question_id: extract_next_question_id,
        phone: @candidate.mobile_phone
      }
    )

    # Envia via WhatsApp
    if @payload_for_frontend[:content].present? && @candidate&.mobile_phone.present?
      Meta::WhatsappService.send_text_message(
        @candidate.mobile_phone,
        @payload_for_frontend[:content]
      )
    end
  end

  def extract_next_question_id
    next_q = @payload_for_frontend[:next_question]
    return next_q[:id] if next_q.is_a?(Hash)
    return next_q.id if next_q.respond_to?(:id)
    @original_payload[:question_id]
  end

  # ============================================================
  # FINALIZAÇÃO
  # ============================================================

  def finalize_evaluation!
    Rails.logger.info("[EvaluationAIResponseService] Finalizing evaluation")

    apply = @evaluation_candidate.apply

    if apply.respond_to?(:evaluation_candidate_status)
      apply.update_columns(
        evaluation_candidate_status: Message::STATUS_ANSWERED,
        updated_at: Time.current
      )
    end

    @evaluation_candidate.update!(completed: true)
    @evaluation_candidate.send_completion_notifications
    apply.update_alerts("approve", "create")
    @evaluation_candidate.create_finish_evaluation_candidate_log
    auto_approve_if_eligible!
  end

  def end_conversation(custom_message = nil)
    Rails.logger.info("[EvaluationAIResponseService] Ending WhatsApp conversation")

    final_msg = custom_message || "Muito obrigado! Recebemos todas as respostas. Um recrutador entrará em contato em breve."
    Meta::WhatsappService.send_text_message(@candidate.mobile_phone, final_msg)

    @message&.update!(
      status: Message::STATUS_ANSWERED,
      metadata: (@message.metadata || {}).merge(finished_at: Time.current)
    )

    finalize_evaluation!
  end

  def send_first_question(question, custom_end_message = nil, response_to_candidate = nil)
    if custom_end_message.present?
      Meta::WhatsappService.send_text_message(@candidate.mobile_phone, custom_end_message)

      Message.create!(
        account_id: @evaluation_candidate.account_id,
        reference: @candidate,
        content: custom_end_message,
        entity: Message::ROLE_SYSTEM,
        status: Message::STATUS_NOT_ANSWERED,
        metadata: { question_index: 0, question_id: question&.id, finished_at: Time.current },
        apply_id: @evaluation_candidate.apply_id,
        evaluation_id: @evaluation_candidate.evaluation_id
      )

      apply = @evaluation_candidate.apply
      if apply.respond_to?(:evaluation_candidate_status)
        apply.update_columns(
          evaluation_candidate_status: Message::STATUS_ANSWERED,
          updated_at: Time.current
        )
      end

      @evaluation_candidate.update!(completed: true)
      return
    end

    message_content = ""
    unless response_to_candidate.to_s.include?(HELP_KEYWORDS_MESSAGE)
      message_content += "#{HELP_KEYWORDS_MESSAGE}\n\n"
    end
    message_content += response_to_candidate.to_s + "\n\n" if response_to_candidate.present?
    question_text = [ question&.title, question&.description ].compact.join("\n").strip
    message_content += question_text if question_text.present?
    Meta::WhatsappService.send_text_message(@candidate.mobile_phone, message_content) if message_content.present?

    Message.create!(
      account_id: @evaluation_candidate.account_id,
      reference: @candidate,
      content: message_content,
      entity: Message::ROLE_SYSTEM,
      status: Message::STATUS_NOT_ANSWERED,
      metadata: { question_index: 0, question_id: question&.id },
      apply_id: @evaluation_candidate.apply_id,
      evaluation_id: @evaluation_candidate.evaluation_id
    )
  end

  # ============================================================
  # RESPONSE DATA
  # ============================================================

  def auto_approve_if_eligible!
    job = @evaluation_candidate.job
    return unless job
    return unless job.respond_to?(:screening_approve_limit) && job.screening_approve_limit.present?
    return unless @evaluation_candidate.score.present?
    return unless @evaluation_candidate.score >= job.screening_approve_limit

    apply = @evaluation_candidate.apply
    return unless apply

    next_process = SelectiveProcess.where(job_id: job.id)
                                    .where("position > ?", apply.selective_process&.position || 0)
                                    .order(position: :asc)
                                    .first
    return unless next_process

    apply.update(selective_process_id: next_process.id)
    Rails.logger.info("[EvaluationAIResponseService] Auto-approved candidate #{@candidate.id} (score: #{@evaluation_candidate.score} >= limit: #{job.screening_approve_limit})")
  rescue StandardError => e
    Rails.logger.error("[EvaluationAIResponseService] Auto-approve failed: #{e.message}")
  end

  def build_response_data
    {
      evaluation_candidate_id: @evaluation_candidate.id,
      answer_id: @answer&.id,
      finished: @finished,
      next_question_sent: @payload_for_frontend[:next_question].present? || @payload_for_frontend[:followup_question].present?
    }
  end
end
