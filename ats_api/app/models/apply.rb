class Apply < ApplicationRecord
  include HasActivityLog
  include Searchable
  include TracksJobAnalytics
  PER_PAGE_KANBAN = 10

  belongs_to :candidate
  belongs_to :job
  belongs_to :selective_process
  belongs_to :account
  has_many :meeting_relationships, dependent: :destroy
  has_many :candidate_feedbacks, dependent: :destroy
  has_many :feedbacks, dependent: :nullify

  before_update :log_selective_process_change
  after_update :trigger_evaluation_if_needed
  after_create_commit :update_cv_match_score, :create_apply_log
  after_commit :enqueue_screening_evaluations_if_needed, on: %i[create update]

  enum evaluation_candidate_status: {
    pending: 0,
    sent: 1,
    answered: 2
  }

  EVALUATION_CANDIDATE_STATUS_LABELS = {
    "pending" => "Não enviado",
    "sent" => "Enviado",
    "answered" => "Respondido"
  }.freeze

  def search_data
    candidate_data = candidate
    selective_process_data = selective_process

    status_key = evaluation_candidate_status.presence
    status_label = status_key && EVALUATION_CANDIDATE_STATUS_LABELS[status_key]
    scores = get_evaluation_candidate_scores
    summaries = get_evaluation_summary

    evaluation_fields = {}

    if job_id.present?
      job_evaluations = Evaluation.where(job_id: job_id)
      job_evaluations.each do |evaluation|
        field_name = normalize_field_name(evaluation.name.split(" ").join("_").downcase + "_#{evaluation.id}")
        score = scores[field_name] || 0.0
        evaluation_fields[field_name.to_sym] = score.to_f
      end
    end

    scores.each do |evaluation_name, score|
      evaluation_fields[evaluation_name.to_sym] = score.to_f
    end

    evaluation_summary_fields = {}
    summaries.each do |evaluation_name, summary|
      summary_field_name = "#{evaluation_name}_summary"
      evaluation_summary_fields[summary_field_name.to_sym] = summary
    end

    {
      **attributes.deep_symbolize_keys.except(:data_raw),
      data_raw: data_raw_for_search_index,
      name: candidate_data&.name&.downcase,
      email: candidate_data&.email&.downcase,
      external_id: candidate_data&.external_id&.to_i,
      role_name: candidate_data&.role_name&.downcase,
      current_company: candidate_data&.current_company&.downcase,
      selective_process_name: selective_process_data&.name&.downcase,
      alerts: alerts,
      alerts_count: alerts&.size || 0,
      phone: candidate_data&.mobile_phone,
      linkedin: candidate_data&.linkedin,
      github: candidate_data&.github,
      portfolio: candidate_data&.portfolio,
      date_birth: candidate_data&.date_birth,
      gender: Candidate::GENDER.find { |g| g[:id] == candidate_data&.gender }&.dig(:name),
      nationality: candidate_data&.nationality,
      cpf: candidate_data&.cpf,
      street: candidate_data&.street,
      number: candidate_data&.number,
      district: candidate_data&.district,
      zip: candidate_data&.zip,
      city: candidate_data&.city,
      state: candidate_data&.state,
      country: candidate_data&.country,
      complement: candidate_data&.complement,
      clt_expectation: candidate_data&.clt_expectation,
      pj_expectation: candidate_data&.pj_expectation,
      freelance_expectation: candidate_data&.freelance_expectation,
      current_salary: candidate_data&.current_salary,
      desired_salary: candidate_data&.desired_salary,
      currency: candidate_data&.currency,
      remote_work: candidate_data&.remote_work,
      mobility: candidate_data&.mobility,
      source: source,
      completed_register: candidate_data&.completed_register,
      accept_terms: candidate_data&.accept_terms,
      is_deleted: is_deleted,
      evaluation_candidate_status: status_key,
      selective_process_status: selective_process_status,
      created_at: created_at,
      updated_at: updated_at,
      evaluation_candidate_scores: scores,
      evaluation_candidate_summaries: summaries,
      pin_user_ids: pin_user_ids,
      confidential_user_ids: confidential_user_ids,
      favorite_user_ids: candidate_data&.favorite_user_ids || [],
      cv_match: cv_match.to_f,
      is_candidate_favorite: is_candidate_favorite,
      candidate_feedback: get_candidate_feedback_type,
      **evaluation_fields,
      **evaluation_summary_fields
    }
  end

  def evaluation_candidate_status_label
    status = evaluation_candidate_status.presence
    return nil unless status
    EVALUATION_CANDIDATE_STATUS_LABELS[status]
  end

  def is_candidate_favorite
    return false unless Current.user
    candidate.favorite_user_ids&.include?(Current.user.id) || false
  end

  def get_evaluation_candidate_scores
    @evaluation_candidate_scores ||= calculate_evaluation_scores
  end

  def evaluation_candidate_scores
    get_evaluation_candidate_scores
  end

  def get_evaluation_summary
    @evaluation_summary ||= begin
      evaluation_candidates = EvaluationCandidate.where(candidate_id: candidate_id, job_id: job_id)
      summaries = {}
      evaluation_candidates.each do |ec|
        evaluation = ec.evaluation
        next unless evaluation
        next if ec.ai_feedback.blank?

        name = normalize_field_name(evaluation.name.split(" ").join("_").downcase + "_#{evaluation.id}")
        summaries[name] = ec.ai_feedback
      end
      summaries
    end
  end

  def evaluation_summary
    get_evaluation_summary
  end

  def evaluation_candidate_summaries
    get_evaluation_summary
  end

  def clear_evaluation_scores_cache
    @evaluation_candidate_scores = nil
    @evaluation_summary = nil
  end

  SELECTIVE_PROCESS_DELEGATED_ATTRS = %i[
    selective_process_name
    color
  ].freeze

  CANDIDATE_DELEGATED_ATTRS = %i[
    name email secondary_phone linkedin github avatar_url curriculum_pdf_url
    portfolio current_company role_name position_level self_introduction
    curriculum_text date_birth gender nationality marital_status cpf street
    number district zip city state country complement clt_expectation
    pj_expectation freelance_expectation current_salary desired_salary
    currency remote_work mobility interests comments completed_register
    accept_terms external_id
  ].freeze

  CANDIDATE_ATTR_MAPPINGS = {
    phone: :mobile_phone
  }.freeze

  def method_missing(method_name, *args, &block)
    return read_attribute(method_name) if has_attribute?(method_name)

    if SELECTIVE_PROCESS_DELEGATED_ATTRS.include?(method_name)
      attr_name = method_name == :selective_process_name ? :name : method_name
      return selective_process&.public_send(attr_name)
    end

    if CANDIDATE_DELEGATED_ATTRS.include?(method_name)
      return candidate&.public_send(method_name)
    end

    if CANDIDATE_ATTR_MAPPINGS.key?(method_name)
      return candidate&.public_send(CANDIDATE_ATTR_MAPPINGS[method_name])
    end

    evaluation_scores = get_evaluation_candidate_scores
    return evaluation_scores[method_name.to_s] if evaluation_scores.key?(method_name.to_s)

    super
  end

  def respond_to_missing?(method_name, include_private = false)
    has_attribute?(method_name) ||
      SELECTIVE_PROCESS_DELEGATED_ATTRS.include?(method_name) ||
      CANDIDATE_DELEGATED_ATTRS.include?(method_name) ||
      CANDIDATE_ATTR_MAPPINGS.key?(method_name) ||
      get_evaluation_candidate_scores.key?(method_name.to_s) ||
      super
  end

  def self.include_base
    joins(:candidate).joins(:selective_process).select('applies.id as id,
      selective_processes.color as color,
      applies.created_at as created_at,
      applies.updated_at as updated_at,
      applies.job_id as job_id,
      applies.pin_user_ids,
      applies.confidential_user_ids,
      applies.selective_process_id as selective_process_id,
      applies.is_deleted as is_deleted,
      applies.evaluation_candidate_status as evaluation_candidate_status,
      applies.selective_process_status as selective_process_status,
      applies.cv_match as cv_match,
      applies.total_score as total_score,
      applies.alerts as alerts,
      applies.sub_status as sub_status,
      applies.is_screening_sent as is_screening_sent,
      selective_processes.name as selective_process_name,
      candidates.id as candidate_id,
      candidates.name as name,
      candidates.email as email,
      candidates.mobile_phone as phone,
      candidates.secondary_phone as secondary_phone,
      candidates.linkedin as linkedin,
      candidates.github as github,
      candidates.avatar_url as avatar_url,
      candidates.curriculum_pdf_url as curriculum_pdf_url,
      candidates.portfolio as portfolio,
      candidates.current_company as current_company,
      candidates.role_name as role_name,
      candidates.position_level as position_level,
      candidates.self_introduction as self_introduction,
      candidates.curriculum_text as curriculum_text,
      candidates.date_birth as date_birth,
      candidates.gender as gender,
      candidates.nationality as nationality,
      candidates.marital_status as marital_status,
      candidates.cpf as cpf,
      candidates.street as street,
      candidates.number as number,
      candidates.district as district,
      candidates.zip as zip,
      candidates.city as city,
      candidates.state as state,
      candidates.country as country,
      candidates.complement as complement,
      candidates.clt_expectation as clt_expectation,
      candidates.pj_expectation as pj_expectation,
      candidates.freelance_expectation as freelance_expectation,
      candidates.current_salary as current_salary,
      candidates.desired_salary as desired_salary,
      candidates.currency as currency,
      candidates.remote_work as remote_work,
      candidates.mobility as mobility,
      candidates.interests as interests,
      candidates.comments as comments,
      applies.source as source,
      candidates.completed_register as completed_register,
      candidates.accept_terms as accept_terms,
      candidates.updated_at as updated_at,
      candidates.account_id as account_id,
      candidates.data_raw as data_raw,
      candidates.external_id as external_id,
      candidates.favorite_user_ids as favorite_user_ids
    ')
  end

  def self.agg_search_array(_params = {})
    {
      selective_process_status: { field: "selective_process_status", limit: 10 },
      candidate_feedback: { field: "candidate_feedback", limit: 3 }
    }
  end

  def get_candidate_feedback_type
    feedback = candidate_feedbacks.active.first
    feedback&.feedback_type
  end

  def data_raw_for_search_index
    raw = attributes["data_raw"] || candidate&.data_raw
    return nil if raw.blank?
    raw.is_a?(Hash) ? raw.to_json : raw.to_s
  end

  def update_cv_match_score
    return unless candidate&.has_embedding? && job.present?

    begin
      Apartment::Tenant.switch!(account.tenant) if account&.tenant.present?

      text = [
        job.title,
        job.description,
        [ job.city, job.state, job.country ].compact.join(", "),
        job.workplace_type
      ].compact.join("\n\n").strip
      return if text.blank?

      job_vector = Embeddings::Encoder.new.call(text)
      return if job_vector.blank?

      sql = <<~SQL
        SELECT 1 - (e.embedding <=> '#{PG::Connection.escape_string(job_vector.to_json)}'::vector)
        FROM embeddings e
        WHERE e.reference_type = 'Candidate' AND e.reference_id = #{candidate.id}
        LIMIT 1
      SQL

      result = ActiveRecord::Base.connection.select_value(sql)
      score = result.to_f.round(5) * 100

      update_column(:cv_match, score)

      update_total_score
    rescue => e
      Rails.logger.error("[Apply] Falha ao calcular cv_match (apply_id=#{id}): #{e.message}")
    end
  end

  def update_total_score
    begin
      scores = get_evaluation_candidate_scores
      total_evaluation_score = scores.values.map(&:to_f).sum
      total_count = scores.values.size + 1 || 1

      total = ((cv_match.to_f.round(5) + total_evaluation_score) / total_count).round(2)
      update_column(:total_score, total)
    rescue => e
      Rails.logger.error("[Apply] Falha ao calcular total_score (apply_id=#{id}): #{e.message}")
    end
  end

  def update_alerts(new_type, action)
    self.alerts ||= []
    return unless alerts.is_a?(Array)

    case action
    when "create"
      create_or_update_alert(new_type)
    when "remove"
      remove_alert(new_type)
    end
  end

  private

  def normalize_field_name(name)
    normalized = name.to_s.unicode_normalize(:nfd).gsub(/[\u0300-\u036f]/, "")
    normalized.downcase.gsub(/[^a-z0-9_]/, "_").squeeze("_").gsub(/^_+|_+$/, "")
  end

  def create_or_update_alert(new_type)
    existing_alert = alerts.find { |a| a.is_a?(Hash) && a["type"] == new_type }

    if existing_alert
      existing_alert["timestamp"] = Time.current.utc.iso8601
    else
      self.alerts << { type: new_type, timestamp: Time.current.utc.iso8601 }
    end

    update_column(:alerts, alerts)
  end

  def remove_alert(new_type)
    self.alerts = alerts.reject { |a| a.is_a?(Hash) && a["type"] == new_type }
    update_column(:alerts, alerts)
  end

  def calculate_evaluation_scores
    evaluation_candidates = EvaluationCandidate.where(candidate_id: candidate_id, job_id: job_id)
    scores = {}

    evaluation_candidates.each do |ec|
      evaluation = ec.evaluation
      next unless evaluation

      total_score = calculate_score_for_evaluation(ec)
      next unless total_score

      field_name = normalize_field_name(evaluation.name.split(" ").join("_").downcase + "_#{evaluation.id}")
      scores[field_name] = total_score
    end

    scores
  end

  def calculate_score_for_evaluation(evaluation_candidate)
    return evaluation_candidate.score * 10 if evaluation_candidate.score.present? && evaluation_candidate.score > 0
    return nil unless evaluation_candidate.answers.any?

    total = evaluation_candidate.answers.sum { |answer| extract_score_from_response(answer.comments_response) }
    average = total / evaluation_candidate.answers.length
    average * 100
  end

  def extract_score_from_response(response)
    return 0 if response.nil?

    match = response.match(/:score=>([\d.]+)/) || response.match(/score:\s*([\d.]+)/)
    match ? match[1].to_f : 0
  end

  def self.set_current_user(user_id)
    return unless user_id

    user = User.find_by(id: user_id)
    Current.user = user if user
  end

  def self.find_existing_apply(candidate_id, job_id)
    Apply.find_by(candidate_id: candidate_id, job_id: job_id, is_deleted: false)
  end

  def self.find_deleted_apply(candidate_id, job_id)
    Apply.find_by(candidate_id: candidate_id, job_id: job_id, is_deleted: true)
  end

  def self.update_and_return(apply, account_id, selective_process_id, selective_process_status, source: nil)
    Rails.logger.info "🔄 [Apply] Apply existente encontrado: Apply##{apply.id}"

    update_attrs = build_update_attributes(account_id, selective_process_id, selective_process_status, source: source)

    if update_attrs.any?
      Rails.logger.info "   Atualizando Apply: #{update_attrs.inspect}"
      apply.update(update_attrs)
    end

    apply
  end

  def self.reactivate_apply(apply, account_id, selective_process_id, selective_process_status, user_id, source: nil)
    Rails.logger.info "♻️  [Apply] Apply deletado encontrado: Apply##{apply.id}"
    Rails.logger.info "   Reativando e atualizando Apply"

    update_attrs = build_update_attributes(account_id, selective_process_id, selective_process_status, user_id, source: source)
    update_attrs[:is_deleted] = false

    Rails.logger.info "   Atualizações: #{update_attrs.inspect}"
    apply.update(update_attrs)

    Rails.logger.info "✅ [Apply] Apply reativado: Apply##{apply.id}"
    apply
  end

  def self.create_new_apply(candidate_id, job_id, account_id, selective_process_id, selective_process_status, user_id, source: nil)
    Rails.logger.info "✨ [Apply] Criando novo Apply"
    Rails.logger.info "   Candidate ID: #{candidate_id}"
    Rails.logger.info "   Job ID: #{job_id}"
    Rails.logger.info "   Status: #{selective_process_status}"

    attrs = {
      candidate_id: candidate_id,
      job_id: job_id,
      account_id: account_id,
      selective_process_id: selective_process_id,
      selective_process_status: selective_process_status,
      is_deleted: false,
      user_id: user_id
    }
    attrs[:source] = source if source.present?

    apply = Apply.create!(attrs)

    Rails.logger.info "✅ [Apply] Apply criado: Apply##{apply.id}"
    apply
  end

  def self.build_update_attributes(account_id, selective_process_id, selective_process_status, user_id = nil, source: nil)
    attrs = {}
    attrs[:account_id] = account_id if account_id.present?
    attrs[:selective_process_id] = selective_process_id if selective_process_id.present?
    attrs[:selective_process_status] = selective_process_status if selective_process_status.present?
    attrs[:user_id] = user_id if user_id.present?
    attrs[:source] = source if source.present?
    attrs
  end

  def resolve_category
    return super if activity_log_category_override.present?

    selective_process_keys = %w[selective_process_id selective_process_status]
    return "selective_processes" if (previous_changes.keys & selective_process_keys).any?

    super
  end

  def enrich_activity_log_changeset(changeset)
    selective_process_keys = %w[selective_process_id selective_process_status]
    return changeset unless (changeset.keys & selective_process_keys).any?

    from_name = nil
    to_name = selective_process&.name

    if previous_changes.key?("selective_process_id")
      old_id = previous_changes["selective_process_id"]&.first
      from_name = SelectiveProcess.find_by(id: old_id)&.name if old_id.present?
    else
      from_name = to_name
    end

    changeset.merge("selective_process_name" => { "from" => from_name, "to" => to_name })
  end

  def log_selective_process_change
    return if selective_process_id.blank?

    change_on_selective_process =
      will_save_change_to_selective_process_id? ||
      will_save_change_to_selective_process_status?

    return unless change_on_selective_process

    status_name = selective_process&.name || "Status não definido"

    current_user_id = Current.user&.id || self.user_id
    return unless current_user_id

    ApplyStatus.create(
      apply_id: id,
      selective_process_id: selective_process_id,
      status_id: nil,
      status_name: status_name,
      comment: "",
      user_id: current_user_id,
      account_id: account_id
    )

    update_alerts("approve", "remove")

    broadcast_pipeline_update(status_name)
  rescue => e
    Rails.logger.error("[Apply] Falha ao criar ApplyStatus (apply_id=#{id}): #{e.message}")
  end

  def broadcast_pipeline_update(stage_name)
    return unless job_id
    return if Thread.current[:skip_pipeline_broadcast]

    ActionCable.server.broadcast(
      "pipeline:#{job_id}",
      {
        type: "stage_change",
        apply_id: id,
        job_id: job_id,
        candidate_id: candidate_id,
        candidate_name: candidate&.name,
        stage: stage_name,
        updated_at: Time.current.iso8601
      }
    )
  rescue => e
    Rails.logger.error("[Apply] Pipeline broadcast failed (apply_id=#{id}): #{e.message}")
  end

  def self.broadcast_bulk_pipeline_update(job_id, results, stage)
    ActionCable.server.broadcast(
      "pipeline:#{job_id}",
      {
        type: "bulk_stage_change",
        job_id: job_id,
        stage: stage.to_s,
        applies: results,
        updated_at: Time.current.iso8601
      }
    )
  rescue => e
    Rails.logger.error("[Apply] Bulk pipeline broadcast failed (job_id=#{job_id}): #{e.message}")
  end

  def self.default_entry_selective_process_id_for_job(job_id)
    return nil if job_id.blank?

    SelectiveProcess
      .where(job_id: job_id, is_deleted: false, status: :web_submission)
      .order(:position)
      .limit(1)
      .pick(:id)
  end

  def self.find_or_create_apply(candidate_id:, job_id:, account_id: nil, selective_process_id: nil, selective_process_status: nil, user_id: nil, source: nil)
    return nil unless candidate_id && job_id

    set_current_user(user_id)

    existing_apply = find_existing_apply(candidate_id, job_id)
    return update_and_return(existing_apply, account_id, selective_process_id, selective_process_status, source: source) if existing_apply

    deleted_apply = find_deleted_apply(candidate_id, job_id)
    return reactivate_apply(deleted_apply, account_id, selective_process_id, selective_process_status, user_id, source: source) if deleted_apply

    resolved_selective_process_id = selective_process_id.presence || default_entry_selective_process_id_for_job(job_id)

    create_new_apply(candidate_id, job_id, account_id, resolved_selective_process_id, selective_process_status, user_id, source: source)
  end

  def create_apply_log
    job = self.job
    ActivityLog.log_change(
      self.candidate,
      user: Current.user,
      action: "create",
      category: "applied",
      changeset: { job: { id: job.id, title: job.title } },
      account: Current.user&.account,
      ip: Current.ip,
    )
  end

  def trigger_evaluation_if_needed
    return unless saved_change_to_selective_process_id?

    evaluation = Evaluation.find_by(
      selective_process_id: selective_process_id,
      is_trigger: true
    )

    return unless evaluation&.whatsapp_chatbot?

    Chatbot::EvaluationStarterJob.perform_later(id, evaluation.id, account_id)
  end

  def enqueue_screening_evaluations_if_needed
    return if Thread.current[:skip_screening_enqueue]
    return unless job_id.present? && account_id.present?
    return unless selective_process&.screening?

    job_record = Job.find_by(id: job_id)
    return unless job_record&.is_screening_active?

    entered_screening = previously_new_record? || previous_changes.key?("selective_process_id")
    return unless entered_screening

    Jobs::SendScreeningEvaluationsJob.perform_async(job_id, account_id)
  end
end
