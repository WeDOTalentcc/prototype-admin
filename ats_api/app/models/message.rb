class Message < ApplicationRecord
  include Searchable

  belongs_to :account, optional: true
  belongs_to :reference, polymorphic: true
  belongs_to :parent_message, class_name: "Message", optional: true
  has_many   :child_messages, class_name: "Message", foreign_key: :parent_message_id, inverse_of: :parent_message, dependent: :nullify
  belongs_to :evaluation, optional: true
  belongs_to :apply, optional: true
  belongs_to :workspace, optional: true, counter_cache: true

  attr_accessor :no_reply

  STATUS_NOT_ANSWERED = 0
  STATUS_ANSWERED     = 1
  ROLE_SYSTEM         = 0
  ROLE_USER           = 1
  ROLE_CANDIDATE      = 2

  THINKING_STATUSES = %w[planning executing completed error searching finalizing analyzing].freeze

  has_one_attached :audio_file

  AUDIO_MAX_SIZE = 25.megabytes
  AUDIO_CONTENT_TYPES = %w[
    audio/webm audio/ogg audio/mp4 audio/mpeg
    audio/wav audio/x-wav audio/mp3
  ].freeze

  validates :reference_type, :reference_id, presence: true
  validates :content_format, inclusion: { in: %w[plain_text conversation thoughts audio], message: "%{value} is not a valid content_format" }, allow_nil: true
  validate  :parent_reference_consistency
  validate  :audio_file_valid, if: -> { audio_file.attached? }

  before_save :sync_execution_tracking_from_metadata
  before_create :set_conversational_state

  scope :for_reference, ->(type, id) { where(reference_type: type, reference_id: id) }
  scope :roots,         -> { where(parent_message_id: nil) }
  scope :children,      -> { where.not(parent_message_id: nil) }
  scope :ordered,       -> { order(created_at: :asc) }
  scope :thinking,      -> { where(is_thinking: true) }
  scope :executing,     -> { where(is_thinking: true, thinking_status: "executing") }

  EVENT_PUBLISHERS = {
    "User" => :publish_for_user,
    "EvaluationCandidate" => :publish_for_evaluation_candidate,
    "Candidate" => :publish_for_whatsapp_evaluation_candidate
  }.freeze

  after_create_commit :publish_message_event
  after_create_commit :broadcast_system_message
  after_create_commit :forward_to_teams_if_needed
  after_update_commit :broadcast_message_updated

  def content_history(limit_count = 13)
    self.class.for_reference(reference_type, reference_id)
        .where(workspace_id: workspace_id)
        .order(created_at: :desc)
        .limit(limit_count)
        .map do |message|
      {
        "role" => message.entity? ? "IA Responde" : "Usuário pergunta",
        "content" => Nokogiri::HTML.fragment(message.content.to_s).text.truncate(150)
      }
    end
  end

  def question_id
    metadata&.fetch("question_id", nil)
  end

  def audio?
    content_format == "audio"
  end

  def audio_base64
    return nil unless audio_file.attached?
    Base64.strict_encode64(audio_file.download)
  end

  def audio_mime_type
    audio_file.content_type if audio_file.attached?
  end

  def attach_audio_from_base64(base64_data, mime_type: "audio/mp3", filename: nil)
    return false if base64_data.blank?

    decoded = Base64.decode64(base64_data)
    filename ||= "tts_response_#{id}.#{mime_type_to_extension(mime_type)}"

    audio_file.attach(
      io: StringIO.new(decoded),
      filename: filename,
      content_type: mime_type
    )

    audio_file.attached?
  rescue => e
    Rails.logger.error "[Message#attach_audio_from_base64] Failed for message #{id}: #{e.class} - #{e.message}"
    false
  end

  def answer?
    candidate? || user?
  end

  def update_execution_step(step_number, new_status, extra = {})
    tracking = execution_tracking.presence || {}
    plan = tracking["plan"] || []

    step = plan.find { |s| s["step"] == step_number }
    return false unless step

    step["status"] = new_status
    extra.each { |k, v| step[k.to_s] = v }

    update_progress!(tracking, plan)
  end

  def add_tool_executed(tool_name:, success:, duration_ms: nil)
    tracking = execution_tracking.presence || {}
    tracking["tools_executed"] ||= []
    tracking["tools_executed"] << {
      "name" => tool_name,
      "success" => success,
      "duration_ms" => duration_ms,
      "executed_at" => Time.current.iso8601
    }

    budget = tracking["budget"] || {}
    budget["used"] = (budget["used"] || 0) + 1
    tracking["budget"] = budget

    update!(execution_tracking: tracking)
    broadcast_execution_tracking_update
    true
  end

  def complete_thinking!(final_status: "completed")
    update!(
      is_thinking: false,
      thinking_status: final_status
    )
  end

  def start_thinking!(plan: [], budget_limit: 40)
    tracking = {
      "plan" => plan.map.with_index(1) { |task, i|
        { "step" => i, "task" => task, "status" => "pending" }
      },
      "progress" => { "done" => 0, "total" => plan.size, "percentage" => 0 },
      "tools_executed" => [],
      "started_at" => Time.current.iso8601,
      "budget" => { "used" => 0, "limit" => budget_limit }
    }

    update!(
      is_thinking: true,
      thinking_status: "planning",
      execution_tracking: tracking
    )
    broadcast_execution_tracking_update
  end

  private

  def update_progress!(tracking, plan)
    done_count = plan.count { |s| s["status"] == "done" }
    total = plan.size
    tracking["progress"] = {
      "done" => done_count,
      "total" => total,
      "percentage" => total.positive? ? ((done_count.to_f / total) * 100).round : 0
    }

    new_thinking_status = done_count == total ? "completed" : "executing"
    new_is_thinking = done_count < total

    update!(
      execution_tracking: tracking,
      thinking_status: new_thinking_status,
      is_thinking: new_is_thinking
    )
    broadcast_execution_tracking_update
    true
  end

  def broadcast_execution_tracking_update
    return unless reference_type == "User" && reference_id.present?

    payload = {
      type: "execution_tracking_updated",
      id: id,
      workspace_id: workspace_id,
      domain: domain,
      is_thinking: is_thinking,
      thinking_status: thinking_status,
      execution_tracking: execution_tracking,
      updated_at: updated_at
    }

    broadcast_to_general_channel(payload)
    broadcast_to_domain_channel(payload)
  end

  def sync_execution_tracking_from_metadata
    return unless metadata.is_a?(Hash)

    self.is_thinking = metadata.delete("is_thinking") if metadata.key?("is_thinking")
    self.thinking_status = metadata.delete("thinking_status") if metadata.key?("thinking_status")
    self.execution_tracking = metadata.delete("execution_tracking") if metadata.key?("execution_tracking")
  end

  def publish_message_event
    return if respond_to?(:no_reply) && no_reply
    return if entity == ROLE_SYSTEM

    MessagePublishJob.perform_later(id, Apartment::Tenant.current)
  rescue StandardError => e
    Rails.logger.error "[Message#publish_message_event] Failed to enqueue publish for message #{id}: #{e.class} - #{e.message}"
    Rails.logger.error e.backtrace&.first(5)&.join("\n")
  end

  public def execute_publish_event
    return if entity == ROLE_SYSTEM

    if contextual_assistant_message?
      publish_contextual_assistant_request(reference)
      return
    end

    publisher_method = EVENT_PUBLISHERS[reference_type]
    return send(publisher_method) if publisher_method
    Rails.logger.warn "Unsupported reference type for publishing: #{reference_type}"
  rescue StandardError => e
    Rails.logger.error "[Message#execute_publish_event] Failed to publish message #{id}: #{e.class} - #{e.message}"
    Rails.logger.error e.backtrace&.first(5)&.join("\n")
  end

  def contextual_assistant_message?
    # Mensagem é contextual assistant se:
    # 1. metadata tem interaction_type == "contextual_assistant" OU
    # 2. mensagem tem domain definido (chat de domínio específico)
    return true if domain.present?
    metadata.is_a?(Hash) && metadata["interaction_type"] == "contextual_assistant"
  end

  def broadcast_system_message
    return unless entity.to_i == ROLE_SYSTEM
    return unless reference_type == "User" && reference_id.present?

    payload = build_broadcast_payload(event_type: "message_created")

    broadcast_to_general_channel(payload)
    broadcast_to_domain_channel(payload)
  end

  def publish_for_user
    user = reference

    # Se tem domain, é uma mensagem de chat contextual (domínio específico)
    if domain.present?
      publish_contextual_assistant_request(user)
      return
    end

    interaction_type = metadata&.dig("interaction_type")

    case interaction_type
    when "contextual_assistant"
      publish_contextual_assistant_request(user)
    else
      publish_generic_user_message(user)
    end
  end

  def publish_for_evaluation_candidate
    Rails.logger.info "[EVAL_DEBUG] ===== RODOU publish_for_evaluation_candidate ====="
    return if entity == Message::ROLE_SYSTEM

    eval_candidate = reference
    question = Question.find_by(id: metadata&.[]("question_id"))
    job = eval_candidate.job

    payload = {
      account_id: account_id,
      message_id: id,
      evaluation_candidate_id: eval_candidate.id,
      question_id: question&.id,
      question_text: question&.description,
      candidate_answer: content,
      job_description: job&.description
    }

    payload[:expected_response] = question&.expected_response
    payload[:history] = self.class.for_reference("EvaluationCandidate", eval_candidate.id)
                                  .ordered.last(10)
                                  .map { |m| { role: (m.entity == Message::ROLE_USER ? "user" : (m.entity == Message::ROLE_SYSTEM ? "assistant" : "candidate")), content: m.content.to_s } }

    if question
      next_q = Question.where(evaluation_id: eval_candidate.evaluation_id)
                       .where("id > ?", question.id)
                       .order(:id).first
      if next_q
        payload[:next_question_hint] = { id: next_q.id, text: next_q.description.presence || next_q.title }
      end
    end

    payload[:style] = { persona: "cordial e técnico", pt_br: true }

    MessageService::EventPublisher.publish(
      payload,
      exchange_name: "evaluations_exchange",
      routing_key: "evaluation_request"
    )
  end

  def publish_for_whatsapp_evaluation_candidate
    Rails.logger.info "[EVAL_DEBUG] ===== RODOU publish_for_whatsapp_evaluation_candidate ====="
    return if entity == Message::ROLE_SYSTEM

    last_bot_message = Message.where(
      reference_type: "Candidate",
      reference_id: reference_id,
      entity: Message::ROLE_SYSTEM,
      status: Message::STATUS_NOT_ANSWERED
    ).order(created_at: :desc).first

    return unless last_bot_message

    return if last_bot_message.metadata.nil?

    evaluation_candidate = EvaluationCandidate.find_by(
      candidate_id: reference_id,
      evaluation_id: last_bot_message.evaluation_id,
      apply_id: last_bot_message.apply_id,
      completed: false,
      is_deleted: false
    )

    return unless evaluation_candidate

    answered_question_ids = Answer.where(
      evaluation_id: evaluation_candidate.evaluation_id,
      candidate_id: evaluation_candidate.candidate_id
    ).pluck(:question_id)

    question = nil
    if last_bot_message.metadata["question_index"] != -1
      question = Question.where(id: last_bot_message.metadata["question_id"], evaluation_id: evaluation_candidate.evaluation_id).last
    end

    job = evaluation_candidate.job

    payload = {
      account_id: account_id,
      message_id: id,
      evaluation_candidate_id: evaluation_candidate.id,
      question_id: question&.id,
      question_text: question&.description,
      candidate_answer: content,
      job_description: job&.description,
      is_introduction: last_bot_message.metadata["question_index"] == -1,
      checked: true
    }

    payload[:expected_response] = question&.expected_response
    payload[:history] = self.class.for_reference("Candidate", evaluation_candidate.candidate_id)
                                  .ordered.last(10)
                                  .map { |m| { role: (m.entity == Message::ROLE_USER ? "user" : (m.entity == Message::ROLE_SYSTEM ? "assistant" : "candidate")), content: m.content.to_s } }

    if question
      next_q = Question.where(evaluation_id: evaluation_candidate.evaluation_id, is_deleted: false)
                        .where.not(id: question&.id)
                        .where.not(id: answered_question_ids)
                        .order(position: :asc).first


      if next_q
        payload[:next_question_hint] = { id: next_q.id, text: next_q.description.presence || next_q.title }
        payload[:answered_question_ids] = answered_question_ids
        payload[:is_first_question] = false
      end
    elsif last_bot_message.metadata["question_index"] == -1
      first_question = Question.where(evaluation_id: evaluation_candidate.evaluation_id, is_deleted: false)
                               .where.not(id: answered_question_ids)
                               .order(position: :asc)
                               .first
      if first_question
        payload[:next_question_hint] = { id: first_question.id, text: first_question.description.presence || first_question.title }
        payload[:answered_question_ids] = answered_question_ids
        payload[:is_first_question] = true
      end
    end

    payload[:style] = { persona: "cordial e técnico", pt_br: true }

    MessageService::EventPublisher.publish(
      payload,
      exchange_name: "evaluations_exchange",
      routing_key: "evaluation_request"
    )
  end

  def parent_reference_consistency
    return unless parent_message
    if parent_message.reference_type != reference_type || parent_message.reference_id != reference_id
      errors.add(:parent_message_id, "must belong to the same reference entity")
    end
  end

  def publish_contextual_assistant_request(user)
    Rails.logger.info "[EVAL_DEBUG] ===== RODOU publish_contextual_assistant_request ====="
    payload = {
      message_id: id,
      reference_type: reference_type,
      reference_id: reference_id,
      content: content,
      user_name: user.name,
      user_id: reference_id,
      account_id: account_id,
      workspace_id: workspace_id,
      entity: entity,
      status: status,
      metadata: metadata,
      created_at: created_at.iso8601,
      content_format: content_format.to_s,
      audio_base64: audio? ? audio_base64 : nil,
      audio_mime_type: audio? ? audio_mime_type : nil
    }

    if domain.present?
      payload[:domain] = domain
      payload[:domain_reference_id] = workspace&.domain_reference_id
    end

    begin
      Rails.logger.info "🔑 [OTT] Generating OTT for contextual assistant message_id=#{id} account_id=#{account_id} user_id=#{reference_id}"
      payload[:one_time_token] = JsonWebToken.encode_ott(
        account_id: account_id,
        user_id: reference_id
      )
      Rails.logger.info "✅ [OTT] OTT generated successfully for message_id=#{id} token_present=#{payload[:one_time_token].present?} token_length=#{payload[:one_time_token]&.length}"
    rescue => e
      Rails.logger.error "❌ [OTT] Failed to generate OTT for contextual assistant message_id=#{id}: #{e.class} #{e.message}"
      Rails.logger.error "   [OTT] account_id=#{account_id} user_id=#{reference_id} backtrace=#{e.backtrace&.first(3)&.join(' | ')}"
    end

    payload.compact!
    Rails.logger.info "📤 [OTT] Publishing contextual assistant request message_id=#{id} payload_has_ott=#{payload[:one_time_token].present?}"
    MessageService::EventPublisher.publish(payload)

    Rails.logger.info("Published contextual assistant request: message_id=#{id}, entity=#{metadata&.dig('entity_context')}")
  end

  def publish_generic_user_message(user)
    Rails.logger.info "[EVAL_DEBUG] ===== RODOU publish_generic_user_message ====="

    payload = build_generic_message_payload(user)

    sanitized_payload = sanitize_payload(payload)

    Rails.logger.debug "[EVAL_DEBUG] Payload sanitizado: #{sanitized_payload.inspect}"

    MessageService::EventPublisher.publish(sanitized_payload)
  end

  def set_conversational_state
    if entity == ROLE_USER

      last_message = Message.where(
        reference_type: reference_type,
        reference_id: reference_id,
        entity: ROLE_SYSTEM,
        workspace_id: workspace_id
      ).order(created_at: :desc).first

      return unless last_message

      conversational_state = last_message.metadata["conversation_state"] if last_message.metadata.is_a?(Hash)

      self.metadata ||= {}
      self.metadata.merge!(conversation_state: conversational_state) if conversational_state
    end
  end

  def forward_to_teams_if_needed
    return unless entity.to_i == ROLE_SYSTEM
    return unless reference_type == "User" && reference_id.present?
    return if thinking_message?

    unless teams_session?
      return unless processing_message? && teams_workspace?
    end

    teams_origin = find_teams_origin
    return unless teams_origin

    Microsoft::TeamsResponseJob.perform_async(id, Apartment::Tenant.current, teams_origin)
  rescue StandardError => e
    Rails.logger.error "[Message#forward_to_teams] Failed for message #{id}: #{e.message}"
  end

  private

  def teams_session?
    meta = metadata.is_a?(Hash) ? metadata : {}
    meta["source"] == "teams" ||
      meta["teams_chat_id"].present? ||
      meta.fetch("session_id", "").to_s.start_with?("teams_")
  end

  def thinking_message?
    is_thinking? || (metadata.is_a?(Hash) && metadata["is_thinking"] == true)
  end

  def processing_message?
    meta = metadata.is_a?(Hash) ? metadata : {}
    meta["is_processing"] == true
  end

  def teams_workspace?
    return false if workspace_id.blank?

    Workspace.exists?(id: workspace_id, domain: "teams")
  end

  def find_teams_origin
    own_meta = metadata.is_a?(Hash) ? metadata : {}
    if own_meta["teams_chat_id"].present? && own_meta["teams_lia_user_id"].present?
      return { "teams_chat_id" => own_meta["teams_chat_id"], "teams_lia_user_id" => own_meta["teams_lia_user_id"] }
    end

    session_id = own_meta["session_id"]
    scope = self.class
      .where(reference_type: reference_type, reference_id: reference_id, entity: ROLE_USER)
      .where("metadata->>'source' = 'teams'")

    scope = scope.where("metadata->>'session_id' = ?", session_id) if session_id.present?

    origin_meta = scope.order(created_at: :desc).limit(1).pick(:metadata)
    return unless origin_meta.is_a?(Hash)

    chat_id = origin_meta["teams_chat_id"]
    lia_user_id = origin_meta["teams_lia_user_id"]
    return unless chat_id.present? && lia_user_id.present?

    { "teams_chat_id" => chat_id, "teams_lia_user_id" => lia_user_id }
  end

  MIME_EXTENSIONS = {
    "audio/mp3" => "mp3",
    "audio/mpeg" => "mp3",
    "audio/wav" => "wav",
    "audio/x-wav" => "wav",
    "audio/ogg" => "ogg",
    "audio/webm" => "webm",
    "audio/mp4" => "mp4"
  }.freeze

  def mime_type_to_extension(mime_type)
    MIME_EXTENSIONS.fetch(mime_type, "mp3")
  end

  def audio_file_valid
    return unless audio_file.attached?
    unless AUDIO_CONTENT_TYPES.include?(audio_file.content_type)
      errors.add(:audio_file, "formato de áudio não suportado")
    end
    if audio_file.byte_size > AUDIO_MAX_SIZE
      errors.add(:audio_file, "tamanho máximo é #{AUDIO_MAX_SIZE / 1.megabyte}MB")
    end
  end

  def build_generic_message_payload(user)
    payload = {
      "message_id" => id.to_i,
      "reference_type" => reference_type.to_s,
      "reference_id" => reference_id.to_i,
      "content" => content.to_s,
      "user_name" => user.name.to_s,
      "user_id" => reference_id.to_i,
      "data_file_ids" => extract_data_file_ids,
      "account_id" => account_id.to_i,
      "content_history" => sanitize_content_history,
      "metadata" => sanitize_metadata,
      "status" => status.to_i,
      "entity" => entity.to_i,
      "workspace_id" => workspace_id.to_i,
      "created_at" => created_at.iso8601,
      "one_time_token" => generate_one_time_token,
      "user_context" => build_user_context(user),
      "content_format" => content_format.to_s,
      "audio_base64" => audio? ? audio_base64 : nil,
      "audio_mime_type" => audio? ? audio_mime_type : nil
    }

    if domain.present?
      payload["domain"] = domain.to_s
      payload["domain_reference_id"] = workspace&.domain_reference_id.to_i
    end

    meta = sanitize_metadata
    if meta["hub_mode"]
      payload["hub_mode"] = true
      payload["session_id"] = meta["session_id"] if meta["session_id"].present?
    end

    payload.compact
  end

  def build_user_context(user)
    {
      "id" => user.id.to_i,
      "email" => user.email.to_s,
      "name" => user.name.to_s,
      "account_id" => user.account_id.to_i,
      "search" => "",  # Campo vazio para o agente preencher com NLP
      "where" => "",   # Localização vazia
      "city" => ""     # Cidade vazia
    }
  end

  def sanitize_metadata
    return {} unless metadata
    return metadata.deep_stringify_keys if metadata.is_a?(Hash)
    return JSON.parse(metadata) if metadata.is_a?(String)
    {}
  rescue JSON::ParserError
    {}
  end

  def sanitize_content_history
    content_history.map do |msg|
      {
        "role" => msg["role"].to_s,
        "content" => msg["content"].to_s
      }
    end
  end

  def extract_data_file_ids
    return [] unless respond_to?(:data_file_ids)
    data_file_ids.to_a
  end

  def generate_one_time_token
    Rails.logger.info "🔑 [OTT] Generating OTT for generic message message_id=#{id} account_id=#{account_id} user_id=#{reference_id}"
    token = JsonWebToken.encode_ott(
      account_id: account_id,
      user_id: reference_id
    ).to_s
    Rails.logger.info "✅ [OTT] OTT generated for generic message message_id=#{id} token_present=#{token.present?} token_length=#{token.length}"
    token
  rescue => e
    Rails.logger.error "❌ [OTT] Failed to generate OTT for generic message message_id=#{id}: #{e.class} #{e.message}"
    Rails.logger.error "   [OTT] account_id=#{account_id} user_id=#{reference_id} backtrace=#{e.backtrace&.first(3)&.join(' | ')}"
    nil
  end

  def sanitize_payload(payload)
    JSON.parse(payload.to_json)
  end

  def build_broadcast_payload(event_type: nil)
    payload = {
      id: id,
      content: content,
      content_format: respond_to?(:content_format) ? content_format : nil,
      entity: entity,
      status: status,
      metadata: metadata,
      account_id: account_id,
      reference_type: reference_type,
      reference_id: reference_id,
      workspace_id: workspace_id,
      domain: domain,
      is_thinking: is_thinking,
      thinking_status: thinking_status,
      execution_tracking: execution_tracking,
      created_at: created_at,
      updated_at: updated_at
    }

    payload[:type] = event_type if event_type

    if audio_file.attached?
      payload[:audio_response] = {
        audio_base64: audio_base64,
        mime_type: audio_mime_type
      }
      return payload
    end

    return payload unless metadata.is_a?(Hash)

    audio = metadata["audio_response"] || metadata.dig("response", "audio_response")
    payload[:audio_response] = audio if audio.present?
    payload
  end

  def broadcast_message_updated
    return unless reference_type == "User" && reference_id.present?

    payload = build_broadcast_payload(event_type: "message_updated")
    payload[:changed_fields] = previous_changes.keys - %w[updated_at]

    broadcast_to_general_channel(payload)
    broadcast_to_domain_channel(payload)
  end

  def broadcast_to_general_channel(payload)
    ActionCable.server.broadcast("messages_user_#{reference_id}", payload)
  end

  def broadcast_to_domain_channel(payload)
    return unless domain.present? && workspace_id.present?

    ws = workspace
    return unless ws&.domain_reference_id.present?

    DomainMessageChannel.broadcast_message(
      user_id: reference_id,
      domain: domain,
      domain_reference_id: ws.domain_reference_id,
      payload: payload.merge(domain_reference_id: ws.domain_reference_id)
    )
  end

  def search_data
    {
      id: id,
      content: content,
      entity: entity,
      status: status,
      reference_type: reference_type,
      reference_id: reference_id,
      account_id: account_id,
      workspace_id: workspace_id,
      domain_reference_id: workspace&.domain_reference_id,
      domain: domain,
      created_at: created_at,
      updated_at: updated_at
    }
  end
end
