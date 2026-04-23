class Job < ApplicationRecord
  include HasActivityLog
  include Searchable
  include RemunerableAttributes

  enable_autocomplete :title

  has_many :selective_processes, dependent: :destroy
  has_many :applies, dependent: :destroy
  has_many :evaluations, dependent: :destroy
  has_many :job_journeys, dependent: :destroy
  has_many :candidate_feedbacks, dependent: :nullify
  has_many :interview_sessions, dependent: :destroy
  has_many :sourcings, dependent: :nullify
  has_many :background_agents, dependent: :destroy

  accepts_nested_attributes_for :selective_processes, allow_destroy: true
  has_many :skill_relationships, as: :reference, dependent: :destroy
  has_many :skills, through: :skill_relationships
  has_many :benefit_relationships, as: :reference, dependent: :destroy
  has_many :benefits, through: :benefit_relationships
  has_many :remuneration_relationships, as: :reference, dependent: :destroy
  has_many :remunerations, through: :remuneration_relationships
  has_many :language_relationships, as: :reference, dependent: :destroy
  has_many :languages, through: :language_relationships
  has_many :behavioral_skill_relationships, as: :reference, dependent: :destroy
  has_many :behavioral_skills, through: :behavioral_skill_relationships
  has_many :list_relationships, as: :reference, dependent: :destroy

  belongs_to :user, optional: true
  belongs_to :account, optional: true
  belongs_to :company, optional: true
  belongs_to :job_status, optional: true
  belongs_to :workflow_template, optional: true
  belongs_to :department, optional: true
  belongs_to :team, optional: true
  belongs_to :reports_to_position, class_name: "OrganizationalPosition", optional: true
  belongs_to :hiring_manager, class_name: "User", optional: true

  has_one :embedding_record, class_name: "Embedding", as: :reference, dependent: :destroy
  has_one :analytics_snapshot, class_name: "JobAnalyticsSnapshot", dependent: :destroy

  def vector_embedding
    embedding_record&.embedding
  end

  def has_embedding?
    embedding_record.present?
  end

  has_many :dispatches, as: :reference, dependent: :nullify

  VALID_NOTIFICATION_CHANNELS = %w[internal voice phone whatsapp].freeze

  validates :external_id, uniqueness: { scope: :account_id, allow_nil: true }
  validate :at_least_one_field_present
  validate :validate_notification_channels

  after_create :ensure_uid
  after_create :ensure_slug
  after_create :set_default_status, if: -> { account_id.present? }
  after_create :copy_saturation_from_account, if: -> { account_id.present? }
  after_create :copy_field_requirements_from_template, if: -> { account_id.present? }
  after_create :create_job_journeys_from_template, if: -> { account_id.present? && !Rails.env.test? }
  after_commit :sync_vector_after_commit, on: %i[create update], unless: -> { Rails.env.test? }
  after_commit :sync_remuneration_attributes_safely, on: %i[create update], if: -> { persisted? }
  after_commit :update_missing_fields_column_safely, on: %i[create update], if: -> { persisted? && !Rails.env.test? }
  after_save :sync_wsi_suggested_seniority_after_lia_enrichment
  after_update :record_seniority_override_if_needed

  SENIORITY = [
    "Júnior",
    "Pleno",
    "Sênior",
    "Especialista",
    "Estágio",
    "Lead",
    "Gerente",
    "Diretor"
  ]

  EMPLOYMENT_TYPES = [
    "CLT",
    "PJ",
    "Estágio",
    "Temporário",
    "Freelancer",
    "Aprendiz"
  ]

  WORKPLACE_TYPES = [
    { "name" => "Não informado", "id" => nil },
    { "name" => "Remoto", "id" => 1 },
    { "name" => "Híbrido", "id" => 2 },
    { "name" => "Presencial", "id" => 3 }
  ]

  def workplace_type_text
    WORKPLACE_TYPES.find { |w| w["id"].to_s == workplace_type.to_s || w["name"] == workplace_type }&.dig("name") || "Não informado"
  end

  def salary_from
    return remuneration_relationships_data[:salary_from] unless instance_variable_defined?(:@salary_from)
    @salary_from
  end

  def salary_to
    return remuneration_relationships_data[:salary_to] unless instance_variable_defined?(:@salary_to)
    @salary_to
  end

  PRIORITY = [
    { "name" => "Não informado", "id" => nil },
    { "name" => "Alta", "id" => 1 },
    { "name" => "Média", "id" => 2 },
    { "name" => "Baixa", "id" => 3 }
  ]

  URGENCY_LEVEL = [
    { "name" => "Não informado", "id" => nil },
    { "name" => "Baixa", "id" => 1 },
    { "name" => "Moderada", "id" => 2 },
    { "name" => "Média", "id" => 3 },
    { "name" => "Alta", "id" => 4 },
    { "name" => "Crítica", "id" => 5 }
  ]

  PCD_CATEGORIES = [
    { "name" => "Não informado", "id" => nil },
    { "name" => "Gênero", "id" => 1 },
    { "name" => "Raça/Etnia", "id" => 2 },
    { "name" => "PCD", "id" => 3 },
    { "name" => "LGBTQIA+", "id" => 4 },
    { "name" => "50+", "id" => 5 },
    { "name" => "Refugiado", "id" => 6 },
    { "name" => "Indígena", "id" => 7 },
    { "name" => "Outro", "id" => 8 }
  ].freeze

  CONFIDENTIAL_TYPES = [
    { "name" => "Não informado", "id" => nil },
    { "name" => "Pública", "id" => 1 },
    { "name" => "Interna", "id" => 2 },
    { "name" => "Confidencial", "id" => 3 }
  ].freeze

  def organizational_structure
    composition = resolved_team_composition
    {
      department_id: department_id,
      department: self[:department_name] || department&.name,
      team_id: team_id,
      team: self[:team_name] || team&.name,
      team_composition: composition,
      reports_to: self[:reports_to_position_title] || reports_to_position&.title,
      hiring_manager: self[:hiring_manager_name] || hiring_manager&.name,
      team_size: resolved_team_size(composition)
    }
  end

  def at_least_one_field_present
    if title.blank? && description.blank?
      errors.add(:base, "Title ou Description deve estar presente")
    end
  end

  def validate_notification_channels
    return if notification_channels.blank?

    invalid = Array(notification_channels) - VALID_NOTIFICATION_CHANNELS
    return if invalid.empty?

    errors.add(:notification_channels, "contains invalid channels: #{invalid.join(', ')}. Valid: #{VALID_NOTIFICATION_CHANNELS.join(', ')}")
  end

  def sync_vector_after_commit
    return unless Rails.env.development? || Rails.env.production?

    if saved_change_to_attribute?(:is_deleted)
      return Jobs::EmbeddingDeleteJob.perform_later(id, account_id) if is_deleted?
      return Jobs::EmbeddingDeleteJob.perform_later(id, account_id) unless indexable?
      return Jobs::EmbeddingSyncJob.perform_later(id, updated_at.to_i, account_id)
    end

    return unless embedding_fields_changed?

    return Jobs::EmbeddingDeleteJob.perform_later(id, account_id) unless indexable?
    Jobs::EmbeddingSyncJob.perform_later(id, updated_at.to_i, account_id)
  end

  def embedding_fields_changed?
    saved_change_to_title? ||
    saved_change_to_description? ||
    saved_change_to_city? ||
    saved_change_to_state? ||
    saved_change_to_country? ||
    saved_change_to_workplace_type?
  end

  after_commit(on: :destroy) do
    if Rails.env.development? || Rails.env.production?
      Jobs::EmbeddingDeleteJob.perform_later(id, account_id)
    end
  end

  def indexable?
    title.present? || description.present?
  end

  def self.preload_process_counts(jobs)
    job_ids = jobs.map(&:id)
    return if job_ids.empty?

    rows = SelectiveProcess
      .where(job_id: job_ids, is_deleted: false)
      .left_joins(:applies)
      .group(:job_id, :id, :name, :status, :color, :position)
      .order(:position)
      .select(
        "selective_processes.job_id",
        "selective_processes.id",
        "selective_processes.name",
        "selective_processes.status",
        "selective_processes.color",
        "selective_processes.position",
        "COUNT(CASE WHEN COALESCE(applies.is_deleted, true) = false THEN applies.id END) as applies_count",
        "SUM(COUNT(CASE WHEN COALESCE(applies.is_deleted, true) = false THEN applies.id END)) OVER (PARTITION BY selective_processes.job_id) as total_participants"
      )

    grouped = rows.group_by(&:job_id)
    jobs.each { |job| job.instance_variable_set(:@preloaded_process_counts, grouped[job.id] || []) }
  end

  DISPLAY_ASSOCIATIONS = %i[company department user hiring_manager team reports_to_position job_status].freeze

  def self.preload_display_associations(jobs)
    return if jobs.blank?

    ActiveRecord::Associations::Preloader.new(
      records: jobs,
      associations: DISPLAY_ASSOCIATIONS
    ).call
  end

  def self.preload_field_requirement_data(jobs)
    job_ids = jobs.map(&:id)
    return if job_ids.empty?

    skills_by_job = SkillRelationship
      .select("skill_relationships.reference_id, skills.name, skill_relationships.priority")
      .joins(:skill)
      .where(reference_type: "Job", reference_id: job_ids, is_deleted: false)
      .order(priority: :desc)
      .group_by(&:reference_id)

    benefits_by_job = BenefitRelationship
      .select(
        "benefit_relationships.reference_id",
        "benefits.name",
        "benefit_relationships.types",
        "benefit_relationships.description",
        "benefit_relationships.details",
        "benefit_relationships.value",
        "benefit_relationships.is_per_day"
      )
      .joins(:benefit)
      .where(reference_type: "Job", reference_id: job_ids, is_deleted: false)
      .group_by(&:reference_id)

    remunerations_by_job = RemunerationRelationship
      .select("remuneration_relationships.reference_id, remunerations.name, remuneration_relationships.value, remuneration_relationships.currency, remuneration_relationships.period, remuneration_relationships.contract_type")
      .joins(:remuneration)
      .where(reference_type: "Job", reference_id: job_ids, is_deleted: false)
      .group_by(&:reference_id)

    language_counts = LanguageRelationship
      .where(reference_type: "Job", reference_id: job_ids)
      .group(:reference_id)
      .count

    jobs.each do |job|
      job.instance_variable_set(:@preloaded_skills, skills_by_job[job.id] || [])
      job.instance_variable_set(:@preloaded_benefits, benefits_by_job[job.id] || [])
      job.instance_variable_set(:@preloaded_remunerations, remunerations_by_job[job.id] || [])
      job.instance_variable_set(:@preloaded_language_count, language_counts[job.id] || 0)
    end
  end

  def total_applies_count
    @total_applies_count ||= self[:cached_applies_count] || applies.where(is_deleted: false).count
  end

  def make_missing_fields
    Jobs::FieldRequirementChecker.new(self).missing_fields
  end

  def completeness_percentage
    checker = Jobs::FieldRequirementChecker.new(self)
    return 100.0 unless checker.requirements_present?

    required_fields = checker.required_fields_count
    return 100.0 if required_fields.zero?

  missing_fields = checker.missing_fields
  missing_count = missing_fields.count
    completed_fields = required_fields - missing_count

    ((completed_fields.to_f / required_fields) * 100).round(2)
  end

  def is_ready_for_publication?
    critical_missing = make_missing_fields.select { |f| f[:category] == "critical" }
    critical_missing.empty?
  end

  def is_confidential_set
    confidential_user_ids != nil
  end

  def has_hiring_manager
    hiring_manager.present?
  end

  def has_team_composition
    team_composition.present?
  end

  def sync_department_from_name(department_name, account_id)
    department = Department.find_by(name: department_name, account_id: account_id)
    department = Department.create!(name: department_name, account_id: account_id) if department.blank?
    update_column(:department_id, department.id) if department.present?
    self.class.searchkick_index.store(self)
  rescue StandardError => e
    Rails.logger.error "Erro ao sincronizar departamento: #{e.message}"
    nil
  end

  private

  def sync_wsi_suggested_seniority_after_lia_enrichment
    return unless saved_change_to_lia_job_description?

    lia = lia_job_description
    return unless lia.is_a?(Hash) && lia["enriched_jd"].present?
    return unless %w[pending_review approved].include?(lia["status"].to_s)

    result = Wsi::SeniorityResolverService.call(job: self)
    return unless result.success?
    return if result.suggested_seniority.blank?

    update_column(:wsi_suggested_seniority_key, result.suggested_seniority)
  rescue StandardError => e
    Rails.logger.warn("[Job##{id}] sync_wsi_suggested_seniority_after_lia_enrichment: #{e.class} #{e.message}")
  end

  def record_seniority_override_if_needed
    return unless saved_change_to_seniority?
    return if wsi_suggested_seniority_key.blank?

    new_key = Wsi::Constants.seniority_key(self)
    return if new_key.blank?
    return if new_key == wsi_suggested_seniority_key

    entry = {
      "from" => wsi_suggested_seniority_key,
      "to" => new_key,
      "user_id" => Current.user&.id,
      "at" => Time.current.iso8601
    }
    list = normalized_seniority_override_entries
    update_column(:seniority_override_log, list + [ entry ])
  end

  def normalized_seniority_override_entries
    raw = seniority_override_log
    return [] if raw.blank?
    return raw if raw.is_a?(Array)
    return raw["events"] if raw.is_a?(Hash) && raw["events"].is_a?(Array)

    []
  end

  def copy_field_requirements_from_template
    return if field_requirements.present? && field_requirements.any?

    template = JobFieldTemplate.default_for_account(account_id)

    unless template
      Rails.logger.warn "Nenhum JobFieldTemplate padrão encontrado para a conta #{account_id}"
      # Cria template padrão automaticamente
      template = JobFieldTemplate.create_default_template(account)
    end

    update_column(:field_requirements, template.fields)
  rescue => e
    Rails.logger.error "Erro ao copiar field_requirements do template: #{e.message}"
  end

  def mark_languages_field_as_checked(checked = true)
    return if field_requirements.blank?

    updated_requirements = field_requirements.map do |field_req|
      if field_req["field_name"] == "languages"
        field_req.merge("checked" => checked)
      else
        field_req
      end
    end

    update_column(:field_requirements, updated_requirements) if field_requirements != updated_requirements
  end

  public

  def update_missing_fields_column_safely
    update_missing_fields_column
  end

  def update_missing_fields_column
    return if destroyed? || !persisted?
    return if @updating_missing_fields

    @updating_missing_fields = true
    new_missing_fields = make_missing_fields
    if missing_fields != new_missing_fields
      update_column(:missing_fields, new_missing_fields)
    end
  ensure
    @updating_missing_fields = false
  end

  def search_data
    job_data = Job.select(<<~SQL.squish)
      jobs.*,
      users.name AS user_name,
      users.email AS user_email,
      companies.name AS company_name,
      companies.linkedin_url AS company_linkedin,
      job_statuses.name AS job_status_name,
      job_statuses.color AS job_status_color,
      workflow_templates.name AS workflow_template_name,
      COUNT(DISTINCT applies.id) FILTER (WHERE applies.is_deleted = false) AS total_applies,
      COUNT(DISTINCT applies.id) FILTER (WHERE applies.is_deleted = false AND applies.evaluation_candidate_status = 2) AS total_approved,
      COUNT(DISTINCT applies.id) FILTER (WHERE applies.is_deleted = false AND applies.evaluation_candidate_status = 1) AS total_pending,
      COUNT(DISTINCT evaluations.id) FILTER (WHERE evaluations.is_deleted = false) AS total_evaluations
    SQL
      .left_joins(:user, :company, :job_status, :workflow_template, :applies, :evaluations)
      .where(id: id)
      .group("jobs.id", "users.id", "companies.id", "job_statuses.id", "workflow_templates.id")
      .first

    return base_search_data unless job_data

    skills_data = skill_relationships_data
    benefits_data = benefit_relationships_data
    remuneration_data = remuneration_relationships_data

    salary_from = remuneration_data[:salary_from]
    salary_to = remuneration_data[:salary_to]

    seniority_text = Job::SENIORITY[seniority] if seniority.present?

    if city.present? || state.present? || country.present?
      location = [ city, state, country ].compact.join(", ").downcase
    else
      address = AddressRelationship.where(reference_type: "Job", reference_id: id, is_deleted: false).last&.address
      location = ""
      if address.present?
        location = address.street.downcase if address&.street.present?
        location += address.number.present? ? ", " + address.number.downcase : ""
        location += address.district.present? ? ", " + address.district.downcase : ""
        location += address.city_id.present? ? ", " + address.city.name.downcase : ""
        location += address.state_id.present? ? ", " + address.state.name.downcase : ""
        location += address.country_id.present? ? ", " + address.country.name.downcase : ""
        location = location.strip
      end
    end

    employment_type_text = Job::EMPLOYMENT_TYPES[employment_type] if employment_type.present?

    language_relationships = LanguageRelationship.where(reference_type: "Job", reference_id: id)
    languages = language_relationships.map do |lr|
      lang = Language.find_by(id: lr.language_id)
      lang.name.downcase if lang
    end.compact

    if languages.blank?
      languages = nil
    end

    {
      id: id,
      uid: uid,
      slug: slug,
      is_published: is_published,
      title: title&.downcase,
      description: description&.downcase,
      provider: provider,
      provider_job_id: provider_job_id,
      external_id: external_id,
      created_at: created_at,
      updated_at: updated_at,
      published_date: published_date,
      application_deadline: application_deadline,
      has_deadline: application_deadline.present?,
      is_deadline_expired: application_deadline.present? && application_deadline < Time.current,
      days_until_deadline: application_deadline.present? ? ((application_deadline - Time.current) / 1.day).to_i : nil,
      is_remote: is_remote,
      is_remote_text: is_remote ? "Remoto" : "Presencial",
      city: city&.downcase,
      state: state&.downcase,
      country: country&.downcase,
      workplace_type: workplace_type,
      workplace_type_text: WORKPLACE_TYPES.find { |w| w["id"].to_s == workplace_type.to_s || w["name"] == workplace_type }&.dig("name") || "Não informado",
      location_full: [ city, state, country ].compact.join(", ").downcase,
      job_url: job_url,
      career_page_id: career_page_id,
      career_page_name: career_page_name,
      career_page_url: career_page_url,
      career_page_logo: career_page_logo,
      friendly_badge: friendly_badge,
      friendly_badge_text: friendly_badge ? "Empresa amigável" : nil,
      disabilities_text: disabilities ? "Vaga PCD" : "Vaga Regular",
      is_pcd: disabilities,
      is_deleted: is_deleted,
      is_deleted_text: is_deleted ? "Deletado" : "Ativo",
      is_archived: is_archived,
      is_archived_text: is_archived ? "Arquivado" : "Ativo",
      is_active: is_active,
      reason_for_pause: reason_for_pause,
      source_job_id: source_job_id,
      has_source: source_job_id.present?,
      user_id: user_id,
      user_name: job_data.user_name&.downcase,
      user_email: job_data.user_email&.downcase,
      company_id: company_id,
      company_name: job_data.company_name&.downcase,
      company_linkedin: job_data.company_linkedin,
      job_status_id: job_status_id,
      job_status_name: job_data.job_status_name,
      job_status_color: job_data.job_status_color,
      workflow_template_id: workflow_template_id,
      workflow_template_name: job_data.workflow_template_name,
      total_applies: job_data.total_applies || 0,
      total_approved: job_data.total_approved || 0,
      total_pending: job_data.total_pending || 0,
      total_evaluations: job_data.total_evaluations || 0,
      pin_user_ids: pin_user_ids || [],
      confidential_user_ids: confidential_user_ids || nil,
      is_pinned: (pin_user_ids || []).any?,
      is_confidential: confidential_user_ids ? (confidential_user_ids || []).any? : nil,
      is_confidential_set: is_confidential_set,
      is_urgent: is_urgent,
      closing_deadline: closing_deadline,
      has_hiring_manager: has_hiring_manager,
      has_team_composition: has_team_composition,
      account_id: account_id,
      seniority: seniority,
      seniority_text: seniority_text,
      salary_from: salary_from,
      salary_to: salary_to,
      location: location,
      employment_type: employment_type,
      employment_type_text: employment_type_text,
      languages: languages,
      skills_a: skills_data[:skills_text],
      benefits_data: benefit_relationships_data,
      priority: priority,
      urgency_level: urgency_level,
      priority_text: PRIORITY.find { |p| p["value"] == priority }&.dig("name") || "Não informado",
      urgency_level_text: URGENCY_LEVEL.find { |u| u["value"] == urgency_level }&.dig("name") || "Não informado",
      is_screening_active: is_screening_active,
      department_id: department_id,
      department_name: department&.name,
      main_pcd_category: main_pcd_category,
      secondary_pcd_category: secondary_pcd_category,
      pcd_description: pcd_description,
      pcd_files_description: pcd_files_description,
      required_pcd_files: required_pcd_files,
      sector: sector,
      segment: segment,
      target_audience: target_audience,
      has_linkedin_post: has_linkedin_post,
      has_website_post: has_website_post,
      has_indeed_post: has_indeed_post,
      confidential_type: confidential_type,
      confidential_company_name: confidential_company_name,
      hiring_manager_id: hiring_manager_id,
      hiring_manager_name: hiring_manager_name,
      hiring_manager_email: hiring_manager_email,
      use_whatsapp_channel: use_whatsapp_channel,
      use_webchat_channel: use_webchat_channel,
      use_voice_channel: use_voice_channel,
      use_call_channel: use_call_channel,
      notification_channels: notification_channels,
      minimum_screening_score: minimum_screening_score,
      screening_timeout: screening_timeout,
      screening_max_attempts: screening_max_attempts,
      screening_approve_limit: screening_approve_limit,
      interview_minimum_score: interview_minimum_score,
      has_automatic_interview: has_automatic_interview,
      interview_calendar_type: interview_calendar_type,
      interview_hours_range: interview_hours_range,
      interview_duration: interview_duration,
      responsibilities: responsibilities || [],
      jd_quality_score: jd_quality_score.presence || {},
      lia_job_description_status: lia_job_description&.dig("status"),
      wsi_jd_big_five_profile: wsi_jd_big_five_profile.presence || {},
      wsi_jd_trait_ranking: wsi_jd_trait_ranking.presence || {},
      wsi_suggested_seniority_key: wsi_suggested_seniority_key
    }.merge(skills_data)
     .merge(remuneration_data)
     .merge(applies_count)
     .merge(applies_by_status_count_for_search)
     .merge(last_activity_at_for_search)
  end


  def base_search_data
    {
      id: id,
      uid: uid,
      slug: slug,
      is_published: is_published,
      external_id: external_id,
      title: title&.downcase,
      description: description&.downcase,
      is_deleted: is_deleted,
      is_archived: is_archived,
      account_id: account_id,
      use_whatsapp_channel: use_whatsapp_channel,
      use_webchat_channel: use_webchat_channel,
      use_voice_channel: use_voice_channel,
      use_call_channel: use_call_channel,
      notification_channels: notification_channels,
      minimum_screening_score: minimum_screening_score,
      screening_timeout: screening_timeout,
      screening_max_attempts: screening_max_attempts,
      screening_approve_limit: screening_approve_limit,
      interview_minimum_score: interview_minimum_score,
      has_automatic_interview: has_automatic_interview,
      interview_calendar_type: interview_calendar_type,
      interview_hours_range: interview_hours_range,
      interview_duration: interview_duration,
      responsibilities: responsibilities || []
    }
  end

  def skill_relationships_data
    skills = if instance_variable_defined?(:@preloaded_skills)
      @preloaded_skills
    else
      SkillRelationship
        .select("skills.name, skill_relationships.priority")
        .joins(:skill)
        .where(reference_type: "Job", reference_id: id, is_deleted: false)
        .order(priority: :desc)
        .to_a
    end

    skills_names = skills.map { |s| s.name&.downcase }.compact

    {
      skills: skills_names,
      skills_text: skills_names.join(" "),
      skills_priority: skills.map(&:priority).compact,
      skills_with_priority: skills.map { |s| { name: s.name&.downcase, priority: s.priority } if s.name }.compact
    }
  end

  def language_relationships_data
    language_rels = language_relationships.includes(:language).order(priority: :desc).to_a

    language_names = language_rels.map { |lr| lr.language&.name&.downcase }.compact

    {
      languages: language_names,
      languages_text: language_names.join(" "),
      languages_with_level: language_rels.map { |lr| { name: lr.language&.name_ptbr&.downcase, level: lr.level, is_required: lr.is_required } if lr.language }.compact
    }
  end

  def behavioral_skills_data
    bsr_rels = behavioral_skill_relationships
      .includes(:behavioral_skill)
      .where(is_deleted: false)
      .order(priority: :desc)
      .to_a

    behavioral_skill_names = bsr_rels.map { |bsr| bsr.behavioral_skill&.name&.downcase }.compact

    {
      behavioral_skills: behavioral_skill_names,
      behavioral_skills_text: behavioral_skill_names.join(" "),
      behavioral_skills_with_priority: bsr_rels.map { |bsr| { name: bsr.behavioral_skill&.name&.downcase, priority: bsr.priority, level_skill: bsr.level_skill, experience_time: bsr.experience_time } if bsr.behavioral_skill }.compact
    }
  end

  def benefit_relationships_data
    benefits = if instance_variable_defined?(:@preloaded_benefits)
      @preloaded_benefits
    else
      BenefitRelationship
        .select("benefits.name,
        benefit_relationships.types,
        benefit_relationships.description,
        benefit_relationships.details,
        benefit_relationships.value,
        benefit_relationships.is_per_day")
        .joins(:benefit)
        .where(reference_type: "Job", reference_id: id, is_deleted: false)
        .to_a
    end

    benefit_names = benefits.map { |b| b.name&.downcase }.compact

    {
      benefits: benefit_names,
      benefits_text: benefit_names.join(" "),
      benefit_types: benefits.flat_map(&:types).compact.uniq,
      benefits_with_values: benefits.map { |b| {
        name: b.name&.downcase, description: b.description, details: b.details,
        value: b.value, is_per_day: b.is_per_day
      }}.compact
    }
  end

  def remuneration_relationships_data
    remunerations = if instance_variable_defined?(:@preloaded_remunerations)
      @preloaded_remunerations
    else
      RemunerationRelationship
        .select("remunerations.name, remuneration_relationships.value, remuneration_relationships.currency, remuneration_relationships.period, remuneration_relationships.contract_type")
        .joins(:remuneration)
        .where(reference_type: "Job", reference_id: id, is_deleted: false)
        .to_a
    end

    salary = remunerations.first
    remuneration_names = remunerations.map { |r| r.name&.downcase }.compact

    range_start = nil
    range_end = nil
    salary_range = if salary&.value.present? && salary.value.to_f > 0
      value = salary.value.to_f
      range_start = (value / 1000).floor * 1000
      range_end = range_start + 1000
      "#{range_start}-#{range_end}"
    else
      "Não informado"
    end

    period_for_index = salary&.period
    period_for_index = nil if period_for_index.is_a?(String)

    {
      remunerations: remuneration_names,
      has_remuneration: remunerations.any?,
      salary_from: range_start,
      salary_to: range_end,
      salary_value: salary&.value,
      salary_currency: salary&.currency || "BRL",
      salary_period: period_for_index,
      salary_text: salary && salary.currency && salary.value ? "#{salary.currency} #{salary.value}" : nil,
      salary_range: salary_range,
      contract_types: remunerations.map(&:contract_type).compact.uniq
    }
  end

  def applies_count
    { applies_count: Apply.where(job_id: id, is_deleted: false).count }
  end

  def last_activity_at_for_search
    latest = Apply.where(job_id: id, is_deleted: false).maximum(:updated_at) || updated_at
    { last_activity_at: latest }
  end

  def applies_by_status_count_for_search
    processes_with_counts = selective_processes
      .left_joins(:applies)
      .where(applies: { is_deleted: [ false, nil ] })
      .or(SelectiveProcess.where(job_id: id))
      .group("selective_processes.id", "selective_processes.name", "selective_processes.status", "selective_processes.position")
      .order("selective_processes.position ASC")
      .select(
        "selective_processes.name",
        "selective_processes.status",
        "selective_processes.position",
        "COUNT(CASE WHEN applies.is_deleted = false THEN applies.id END) as applies_count"
      )

    status_counts = {}
    in_process = 0

    processes_with_counts.each do |process|
      count = process.applies_count.to_i
      status_counts[process.name] = count
      in_process += count if process.status == "interview" || process.status == "screening"
    end

    {
      in_process: in_process,
      applies_by_status_count: status_counts
    }
  end

  def applies_by_status_count
    processes = @preloaded_process_counts || fetch_process_counts

    status_counts = {}
    in_process = 0

    processes.each do |process|
      count = process.applies_count.to_i
      hex_color = process.color.presence || SelectiveProcess::STATUS_COLORS[process.status.to_sym] || "#E5E7EB"

      status_counts[process.name] = {
        process.name => {
          count: count,
          color: hex_color
        }
      }

      in_process += count if process.status == "interview" || process.status == "screening"
    end

    {
      in_process: in_process,
      applies_by_status_count: status_counts
    }
  end

  def hex_to_rgb(hex)
    hex = hex.delete("#")

    r = hex[0..1].to_i(16)
    g = hex[2..3].to_i(16)
    b = hex[4..5].to_i(16)

    "#{r}, #{g}, #{b}"
  end

  def fetch_process_counts
    SelectiveProcess
      .where(job_id: id, is_deleted: false)
      .left_joins(:applies)
      .group(:id, :name, :status, :color, :position)
      .order(:position)
      .select(
        "selective_processes.id",
        "selective_processes.name",
        "selective_processes.status",
        "selective_processes.color",
        "selective_processes.position",
        "COUNT(CASE WHEN COALESCE(applies.is_deleted, true) = false THEN applies.id END) as applies_count",
        "SUM(COUNT(CASE WHEN COALESCE(applies.is_deleted, true) = false THEN applies.id END)) OVER () as total_participants"
      ).to_a
  end

  def job_status_attributes
    return {} unless job_status
    {
      job_status: {
        id: job_status.id,
        name: job_status.name,
        color: job_status.color,
        is_main: job_status.is_main
      }
    }
  end


  def self.include_base
    select(<<~SQL)
      jobs.id,
      jobs.uid,
      jobs.slug,
      jobs.is_published,
      jobs.title,
      jobs.description,
      jobs.user_id,
      jobs.account_id,
      jobs.job_status_id,
      jobs.created_at,
      jobs.updated_at,
      jobs.provider,
      jobs.provider_job_id,
      jobs.published_date,
      jobs.application_deadline,
      jobs.is_remote,
      jobs.city,
      jobs.state,
      jobs.country,
      jobs.job_url,
      jobs.career_page_id,
      jobs.career_page_name,
      jobs.career_page_url,
      jobs.career_page_logo,
      jobs.friendly_badge,
      jobs.disabilities,
      jobs.workplace_type,
      jobs.company_id,
      jobs.pin_user_ids,
      jobs.confidential_user_ids,
      jobs.external_id,
      jobs.is_deleted,
      jobs.is_urgent,
      jobs.source_job_id,
      jobs.workflow_template_id,
      jobs.missing_fields,
      jobs.seniority,
      jobs.field_requirements,
      jobs.employment_type,
      jobs.team_id,
      jobs.department_id,
      jobs.reports_to_position_id,
      jobs.hiring_manager_id,
      jobs.team_composition,
      jobs.screening_deadline,
      jobs.shortlist_deadline,
      jobs.closing_deadline,
      jobs.is_archived,
      jobs.is_active,
      jobs.reason_for_pause,
      jobs.priority,
      jobs.urgency_level,
      jobs.is_screening_active,
      jobs.main_pcd_category,
      jobs.secondary_pcd_category,
      jobs.pcd_description,
      jobs.pcd_files_description,
      jobs.required_pcd_files,
      jobs.sector,
      jobs.segment,
      jobs.target_audience,
      jobs.has_linkedin_post,
      jobs.has_website_post,
      jobs.has_indeed_post,
      jobs.confidential_type,
      jobs.confidential_company_name,
      jobs.hiring_manager_id,
      jobs.use_whatsapp_channel,
      jobs.use_webchat_channel,
      jobs.use_voice_channel,
      jobs.use_call_channel,
      jobs.notification_channels,
      jobs.minimum_screening_score,
      jobs.screening_timeout,
      jobs.screening_max_attempts,
      jobs.screening_approve_limit,
      jobs.interview_minimum_score,
      jobs.has_automatic_interview,
      jobs.interview_calendar_type,
      jobs.interview_hours_range,
      jobs.interview_duration,
      jobs.responsibilities,
      jobs.web_saturation_amount,
      jobs.sourcing_saturation_amount,
      jobs.saturation_amount_increase,
      jobs.saturation_release_hours,
      jobs.allowed_screenings_limit_date,
      jobs.agent_search_criteria,
      hiring_manager.name AS hiring_manager_name,
      hiring_manager.email AS hiring_manager_email,
      jobs.jd_quality_score,
      jobs.lia_job_description,
      jobs.wsi_jd_big_five_profile,
      jobs.wsi_jd_trait_ranking,
      jobs.wsi_suggested_seniority_key,
      jobs.hiring_manager_name,
      jobs.hiring_manager_email,
      CASE
        WHEN jobs.workplace_type IN ('1', '2', '3') THEN
          CASE jobs.workplace_type
            WHEN '1' THEN 'Remoto'
            WHEN '2' THEN 'Híbrido'
            WHEN '3' THEN 'Presencial'
            ELSE 'Não informado'
          END
        WHEN jobs.workplace_type IN ('Remoto', 'Híbrido', 'Presencial') THEN jobs.workplace_type
        ELSE 'Não informado'
      END AS workplace_type_text,
      users.name   AS user_name,
      users.email  AS user_email,
      companies.name AS company_name,
      job_statuses.name AS job_status,
      job_statuses.color AS job_status_color,
      MAX(CASE WHEN rem.name = 'Salário (De)' THEN rr.value END) AS salary_from,
      MAX(CASE WHEN rem.name = 'Salário (Até)' THEN rr.value END) AS salary_to,
      MAX(CASE WHEN rem.name IN ('Salário', 'Salário (De)', 'Salário (Até)') THEN rr.currency END) AS salary_currency,
      MAX(CASE WHEN rem.name IN ('Salário', 'Salário (De)', 'Salário (Até)') THEN rr.period END) AS salary_period,
      MAX(CASE WHEN rem.name IN ('Salário', 'Salário (De)', 'Salário (Até)') THEN rr.contract_type END) AS salary_contract_type,
      MAX(CASE WHEN rem.name = 'Comissão (De)' THEN rr.value END) AS commission_from,
      MAX(CASE WHEN rem.name = 'Comissão (Até)' THEN rr.value END) AS commission_to,
      MAX(CASE WHEN rem.name IN ('Comissão', 'Comissão (De)', 'Comissão (Até)') THEN rr.currency END) AS commission_currency,
      MAX(CASE WHEN rem.name IN ('Comissão', 'Comissão (De)', 'Comissão (Até)') THEN rr.period END) AS commission_period,
      MAX(CASE WHEN rem.name = 'Pacote de Bônus (De)' THEN rr.value END) AS bonus_from,
      MAX(CASE WHEN rem.name = 'Pacote de Bônus (Até)' THEN rr.value END) AS bonus_to,
      MAX(CASE WHEN rem.name IN ('Pacote de Bônus', 'Pacote de Bônus (De)', 'Pacote de Bônus (Até)') THEN rr.currency END) AS bonus_currency,
      MAX(CASE WHEN rem.name IN ('Pacote de Bônus', 'Pacote de Bônus (De)', 'Pacote de Bônus (Até)') THEN rr.period END) AS bonus_period,
      users.whatsapp AS user_whatsapp,
      departments.name AS department_name,
      teams.name AS team_name,
      teams.member_count AS team_member_count,
      organizational_positions.title AS reports_to_position_title,
      accounts.slug AS account_slug,
      (SELECT COUNT(*) FROM applies WHERE applies.job_id = jobs.id AND applies.is_deleted = false) AS cached_applies_count
    SQL
    .joins("LEFT JOIN users ON users.id = jobs.user_id")
    .joins("LEFT JOIN users hiring_manager ON hiring_manager.id = jobs.hiring_manager_id")
    .joins("LEFT JOIN companies ON companies.id = jobs.company_id")
    .joins("LEFT JOIN job_statuses ON job_statuses.id = jobs.job_status_id")
    .joins("LEFT JOIN departments ON departments.id = jobs.department_id")
    .joins("LEFT JOIN teams ON teams.id = jobs.team_id")
    .joins("LEFT JOIN organizational_positions ON organizational_positions.id = jobs.reports_to_position_id")
    .joins("LEFT JOIN accounts ON accounts.id = jobs.account_id")
    .joins("LEFT JOIN remuneration_relationships rr ON rr.reference_type = 'Job' AND rr.reference_id = jobs.id AND rr.is_deleted = false")
    .joins("LEFT JOIN remunerations rem ON rem.id = rr.remuneration_id")
    .group("jobs.id", "users.id", "companies.id", "job_statuses.id", "hiring_manager.id", "departments.id", "teams.id", "organizational_positions.id", "accounts.id")
  end

  def self.agg_search_array(_params = {})
    {
      job_status_id: { field: "job_status_id", limit: 10 },
      job_status_name: { field: "job_status_name", limit: 10 },
      workflow_template_id: { field: "workflow_template_id", limit: 15 },
      workflow_template_name: { field: "workflow_template_name", limit: 15 },
      company_name: { field: "company_name", limit: 20 },
      is_remote: { field: "is_remote", limit: 5 },
      city: { field: "city", limit: 25 },
      state: { field: "state", limit: 30 },
      country: { field: "country", limit: 15 },
      workplace_type: { field: "workplace_type", limit: 10 },
      provider: { field: "provider", limit: 10 },
      is_remote_text: { field: "is_remote_text", limit: 5 },
      career_page_id: { field: "career_page_id", limit: 15 },
      career_page_name: { field: "career_page_name", limit: 15 },
      friendly_badge: { field: "friendly_badge", limit: 5 },
      disabilities_text: { field: "disabilities_text", limit: 5 },
      is_pcd: { field: "is_pcd", limit: 5 },
      user_id: { field: "user_id", limit: 25 },
      user_name: { field: "user_name", limit: 25 },
      is_deleted_text: { field: "is_deleted_text", limit: 5 },
      has_deadline: { field: "has_deadline", limit: 5 },
      is_deadline_expired: { field: "is_deadline_expired", limit: 5 },
      is_pinned: { field: "is_pinned", limit: 5 },
      is_confidential: { field: "is_confidential", limit: 5 },
      skills: { field: "skills", limit: 30 },
      benefits: { field: "benefits", limit: 20 },
      benefit_types: { field: "benefit_types", limit: 15 },
      remunerations: { field: "remunerations", limit: 10 },
      has_remuneration: { field: "has_remuneration", limit: 5 },
      salary_range: { field: "salary_range", limit: 50 },
      contract_types: { field: "contract_types", limit: 10 },
      is_urgent: { field: "is_urgent", limit: 5 },
      seniority_text: { field: "seniority_text", limit: 10 },
      employment_type_text: { field: "employment_type_text", limit: 10 },
      department_name: { field: "department_name", limit: 20 },
      hiring_manager_name: { field: "hiring_manager_name", limit: 20 },
      priority_text: { field: "priority_text", limit: 5 },
      urgency_level_text: { field: "urgency_level_text", limit: 10 }
    }
  end

  def selection_process_summary
    processes = @preloaded_process_counts || fetch_process_counts

    total_participants = processes.first&.total_participants.to_i
    total_participants = total_applies_count if total_participants.zero? && processes.any?

    {
      total_participants: total_participants,
      processes: processes.map do |process|
        participants_count = process.applies_count.to_i
        {
          id: process.id,
          name: process.name,
          position: process.position,
          status: process.status,
          participants_count: participants_count,
          percentage: total_participants > 0 ? ((participants_count.to_f / total_participants) * 100).round(2) : 0
        }
      end
    }
  end

  def sync_benefits_from_array(benefits_array)
    return unless benefits_array.is_a?(Array) && benefits_array.present?

    benefit_names = []
    benefits_array.each do |item|
      next if item.blank?
      names = item.to_s.split(",").map(&:strip).reject(&:blank?)
      benefit_names.concat(names)
    end

    return if benefit_names.empty?

    benefit_relationships.where(is_deleted: false).update_all(is_deleted: true)

    benefit_names.uniq.each do |name|
      benefit = Benefit.find_or_create_by(name: name) { |b| b.days_of_month = 0 }

      rel = benefit_relationships.find_or_initialize_by(
        benefit_id: benefit.id,
        reference_type: "Job",
        reference_id: id
      )

      rel.name = name
      rel.is_deleted = false
      rel.days_of_month ||= 0
      rel.save if rel.changed?
    end
  rescue => e
    Rails.logger.error "Failed to sync benefits for Job #{id}: #{e.message}"
  end

  def sync_skills_from_data(skills_data)
    return if skills_data.blank?

    skill_names = []
    if skills_data.is_a?(Array)
      skills_data.each do |item|
        next if item.blank?
        names = item.to_s.split(",").map(&:strip).reject(&:blank?)
        skill_names.concat(names)
      end
    else
      skill_names = skills_data.to_s.split(",").map(&:strip).reject(&:blank?)
    end

    return if skill_names.empty?

    skill_relationships.where(is_deleted: false).update_all(is_deleted: true)

    skill_names.uniq.each do |name|
      skill = Skill.find_or_create_by(name: name, account_id: account_id)

      rel = skill_relationships.find_or_initialize_by(
        skill_id: skill.id,
        reference_type: "Job",
        reference_id: id,
        account_id: account_id
      )

      rel.is_deleted = false
      rel.priority ||= 0
      rel.save if rel.changed?
    end
  rescue => e
    Rails.logger.error "Failed to sync skills for Job #{id}: #{e.message}"
  end

  def sync_languages_from_data(languages_data)
    mark_languages_field_as_checked(true)
    return if languages_data.blank?
    language_relationships.destroy_all
    if languages_data.is_a?(Array)
      languages_data.each do |item|
        next if item.blank?
        is_hash_like = item.is_a?(Hash) ||
                       item.is_a?(ActionController::Parameters) ||
                       (item.respond_to?(:[]) && item.respond_to?(:keys) && !item.is_a?(String))

        if is_hash_like
          language_id = item[:language_id] || item["language_id"]
          language_name = item[:language_name] || item["language_name"]
          language_acronym = item[:language_acronym] || item["language_acronym"]
          level = item[:level] || item["level"]
          min_value = item[:min_value] || item["min_value"]
          max_value = item[:max_value] || item["max_value"]
          priority = item[:priority] || item["priority"] || 0

          language = nil
          if language_id.present?
            language = Language.find_by(id: language_id)
          elsif language_acronym.present? && language.blank?
            language = Language.find_by("UPPER(acronym) = ?", language_acronym.upcase)
          elsif language_name.present? && language.blank?
            language = Language.find_by("LOWER(name) = ?", language_name.downcase)
          elsif language.blank?
            language = Language.find_by(name_ptbr: language_name)
          end

          next unless language

          language_relationships.create!(
            language_id: language.id,
            reference_type: "Job",
            reference_id: id,
            level: level&.strip.downcase,
            min_value: min_value&.to_i,
            max_value: max_value&.to_i,
            priority: priority
          )
        else
          language_name = item.to_s.strip
          next if language_name.blank?

          language = Language.find_by("LOWER(name) = ?", language_name.downcase) ||
                     Language.find_by("UPPER(acronym) = ?", language_name.upcase)

          next unless language

          language_relationships.create!(
            language_id: language.id,
            reference_type: "Job",
            reference_id: id,
            priority: 0
          )
        end
      end
    else
      language_name = languages_data.to_s.strip
      return if language_name.blank?

      language = Language.find_by("LOWER(name) = ?", language_name.downcase) ||
                 Language.find_by("UPPER(acronym) = ?", language_name.upcase)

      if language
        language_relationships.create!(
          language_id: language.id,
          reference_type: "Job",
          reference_id: id,
          priority: 0
        )
      end
    end
    self.class.searchkick_index.store(self)
  rescue => e
    Rails.logger.error "Failed to sync languages for Job #{id}: #{e.message}"
    Rails.logger.error e.backtrace.join("\n")
  end

  def create_default_selective_processes
    return unless account_id.present?
    return if selective_processes.any?

    if workflow_template_id.nil?
      workflow_template = WorkflowTemplate.find_or_create_by(
        name: "#{account.name} Workflow Template",
        account: account,
        is_main: true
      )
      self.workflow_template_id = workflow_template.id
    end

    @account_id = account_id || Current&.user&.account_id

    workflow_processes = SelectiveProcess.where(
      workflow_template_id: workflow_template_id,
      account_id: @account_id,
      job_id: nil
    ).order(:position)

    if workflow_processes.exists?
      workflow_processes.each do |process|
        new_selective_process = selective_processes.create!(
          name: process.name,
          position: process.position,
          status: process.status,
          account_id: @account_id,
          job_id: id,
          workflow_template_id: workflow_template_id,
          sub_status: process.sub_status,
          childrens: process.childrens,
          position_x: process.position_x,
          position_y: process.position_y
        )

        create_feedbacks(process, new_selective_process)
      end
      web_submission_sp = nil
      screening_sp = nil
      interview_sp = nil
      rejected_sp = nil
      SelectiveProcess.where(job_id: id).each do |sp|
        web_submission_sp = sp if sp.web_submission?
        screening_sp = sp if sp.screening?
        interview_sp = sp if sp.interview?
        rejected_sp = sp if sp.rejected?
      end

      if web_submission_sp.present? && screening_sp.present? && interview_sp.present? && rejected_sp.present?
        web_submission_sp.update(approved_process_id: screening_sp.id, rejected_process_id: rejected_sp.id)
        screening_sp.update(approved_process_id: interview_sp.id, rejected_process_id: rejected_sp.id)
        interview_sp.update(approved_process_id: nil, rejected_process_id: rejected_sp.id)
        rejected_sp.update(approved_process_id: nil, rejected_process_id: nil)
      end
    else
      SelectiveProcess.default_process.each do |attrs|
        selective_processes.create!(
          name: attrs[:name],
          position: attrs[:position],
          status: attrs[:status],
          account_id: @account_id,
          job_id: id,
          workflow_template_id: workflow_template_id,
          sub_status: attrs[:sub_status],
          childrens: [ attrs[:position] + 1 ]
        )
      end

      web_submission_sp = nil
      screening_sp = nil
      interview_sp = nil
      rejected_sp = nil

      SelectiveProcess.where(job_id: id).each do |sp|
        web_submission_sp = sp if sp.web_submission?
        screening_sp = sp if sp.screening?
        interview_sp = sp if sp.interview?
        rejected_sp = sp if sp.rejected?
      end

      if web_submission_sp.present? && screening_sp.present? && interview_sp.present? && rejected_sp.present?
        web_submission_sp.update(approved_process_id: screening_sp.id, rejected_process_id: rejected_sp.id)
        screening_sp.update(approved_process_id: interview_sp.id, rejected_process_id: rejected_sp.id)
        interview_sp.update(approved_process_id: nil, rejected_process_id: rejected_sp.id)
        rejected_sp.update(approved_process_id: nil, rejected_process_id: nil)
      end
    end
  end

  def sync_remuneration_attributes_safely
    sync_remuneration_attributes
  end

  def sync_remuneration_attributes
    return if @syncing_remuneration

    @syncing_remuneration = true
    JobService::RemunerationSync.new(self).call
  ensure
    @syncing_remuneration = false
  end

  def resolved_team_composition
    team&.current_composition.presence || team_composition || []
  end

  def resolved_team_size(composition)
    cached = self[:team_member_count]
    return cached if cached
    return team.member_count if team&.member_count

    composition.sum do |item|
      if item.respond_to?(:[])
        value = item[:count] || item["count"]
        value ? value.to_i : 1
      else
        1
      end
    end
  end

  SATURATION_FIELDS = %i[web_saturation_amount sourcing_saturation_amount saturation_amount_increase saturation_release_hours].freeze

  scope :within_screening_send_window, -> {
    where("allowed_screenings_limit_date IS NULL OR allowed_screenings_limit_date >= ?", Time.current)
  }

  def can_send_screenings?
    allowed_screenings_limit_date.nil? || Time.current <= allowed_screenings_limit_date
  end

  def saturation_overridden_by_limit_date?
    allowed_screenings_limit_date.present? && Time.current <= allowed_screenings_limit_date
  end

  def saturation_limit_for_source(source)
    case source.to_s
    when "web_response", "web" then web_saturation_amount.to_i
    when "sourcing" then sourcing_saturation_amount.to_i
    else sourcing_saturation_amount.to_i
    end
  end

  def effective_saturation_limit_for_source(source, first_sent_at: nil)
    base = saturation_limit_for_source(source)
    return base if saturation_amount_increase.to_i <= 0 || saturation_release_hours.to_i <= 0
    return base if first_sent_at.blank?

    hours_elapsed = (Time.current - first_sent_at) / 3600.0
    periods = (hours_elapsed / saturation_release_hours).floor
    base + (periods * saturation_amount_increase.to_i)
  end

  def default_user_id_for_screening(evaluation: nil)
    evaluation&.user_id ||
      user_id ||
      account&.users&.find_by(is_admin: true)&.id ||
      account&.users&.first&.id
  end

  private

  def create_job_journeys_from_template
    return unless account_id.present?
    return if job_journeys.any?

    template_journeys = JobJourney.where(account_id: account_id, job_id: nil).ordered

    if template_journeys.exists?
      template_journeys.each do |template|
        job_journeys.create!(
          name: template.name,
          description: template.description,
          position: template.position,
          active: template.active,
          required: template.required,
          account_id: account_id
        )
      end
      Rails.logger.info "✅ Criados #{template_journeys.count} job_journeys para Job ##{id}"
    else
      Rails.logger.warn "⚠️ Nenhum job_journey template encontrado para a conta ##{account_id}"
    end
  rescue StandardError => e
    Rails.logger.error "Erro ao criar job_journeys para Job ##{id}: #{e.message}"
    # Não propaga o erro para não abortar a criação do Job
  end

  def create_feedbacks(process, target_selective_process)
    feedbacks = Feedback.where(selective_process_id: process.id, account_id: @account_id, job_id: nil, is_deleted: false)
    feedbacks.each do |feedback|
      begin
        new_feedback = Feedback.create!(
          name: feedback.name,
          description: feedback.description,
          account_id: @account_id,
          job_id: id,
          title: feedback.title,
          additional_text: feedback.additional_text,
          selective_process_id: target_selective_process.id,
          is_deleted: false
        )
      rescue ActiveRecord::RecordInvalid => e
        Rails.logger.error "Failed to create feedback: #{e.message}"
      end
    end
  end

  def ensure_uid
    return if uid.present?

    loop do
      new_uid = SecureRandom.uuid
      unless Job.exists?(uid: new_uid)
        update_column(:uid, new_uid)
        break
      end
    end
  end

  def ensure_slug
    return if slug.present?

    base = (title.presence || "vaga").to_s.parameterize
    base = "vaga" if base.blank?
    suffix = uid.present? ? uid.gsub("-", "")[0..5] : SecureRandom.hex(3)
    update_column(:slug, "#{base}-#{suffix}")
  end

  def set_default_status
    return if job_status_id.present?
    return unless account_id.present?

    status = JobStatus.find_by(account_id: account_id, is_main: true, name: "Aberta") ||
             JobStatus.find_by(account_id: account_id, is_main: true)

    return unless status

    update_column(:job_status_id, status.id)
  rescue StandardError => e
    Rails.logger.warn("Não foi possível definir status padrão para Job ##{id}: #{e.message}")
  end

  def copy_saturation_from_account
    return unless account_id.present?
    return unless respond_to?(:web_saturation_amount)

    acct = Account.find_by(id: account_id)
    return unless acct

    updates = SATURATION_FIELDS.each_with_object({}) do |attr, hash|
      next if read_attribute(attr).present? && read_attribute(attr) != 0

      val = acct.read_attribute(attr)
      hash[attr] = val if val.present? || val == 0
    end
    update_columns(updates) if updates.any?
  rescue StandardError => e
    Rails.logger.warn("Não foi possível copiar saturation do account para Job ##{id}: #{e.message}")
  end
end
