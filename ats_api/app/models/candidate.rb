require_relative "../validators/linkedin_url_validator"

class Candidate < ApplicationRecord
  include HasActivityLog
  include Searchable

  enable_autocomplete :name

  attr_accessor :score

  belongs_to :account

  has_many :applies, dependent: :destroy
  has_many :meeting_relationships, as: :reference, dependent: :destroy
  has_many :evaluation_candidates, dependent: :destroy
  has_many :evaluations, through: :evaluation_candidates
  has_many :jobs, through: :applies
  has_many :educations, dependent: :destroy
  has_many :experiences, dependent: :destroy
  has_many :skill_relationships, as: :reference, dependent: :destroy
  has_many :skills, through: :skill_relationships
  has_many :language_relationships, as: :reference, dependent: :destroy
  has_many :languages, through: :language_relationships
  has_many :behavioral_skill_relationships, as: :reference, dependent: :destroy
  has_many :behavioral_skills, through: :behavioral_skill_relationships
  has_many :dispatch_messages, as: :recipient, dependent: :destroy
  has_many :sourced_profile
  has_many :sector_relationships, as: :reference, dependent: :destroy
  has_many :sectors, through: :sector_relationships
  has_many :candidate_feedbacks, dependent: :destroy
  has_many :interview_sessions, dependent: :destroy

  has_one_attached :avatar
  has_one_attached :curriculum_pdf

  has_one :embedding_record, class_name: "Embedding", as: :reference, dependent: :destroy

  def vector_embedding
    embedding_record&.embedding
  end

  def has_embedding?
    embedding_record.present?
  end

  validates :name, presence: true
  validates :cpf, uniqueness: true, allow_blank: true

  enum ethnicity: {
    white: 0, black: 1, brown: 2, yellow: 3, indigenous: 4, undeclared: 5
  }, _prefix: :ethnicity

  belongs_to :twin_source, class_name: "Candidate", optional: true
  has_many   :twin_copies, class_name: "Candidate", foreign_key: :twin_source_id, inverse_of: :twin_source, dependent: :nullify

  scope :visible, -> { where(is_hidden: false) }
  scope :hidden,  -> { where(is_hidden: true) }
  scope :lgpd_active, -> { where("lgpd_expires_at IS NULL OR lgpd_expires_at > ?", Time.current) }
  scope :pcd,            -> { where(pcd: true) }
  scope :lgbtqia,        -> { where(lgbtqia: true) }
  scope :neurodivergent, -> { where(neurodivergent: true) }

  # Callbacks
  after_commit :sync_vector_after_commit,
               unless: -> { Rails.env.test? || skip_vector_sync }

  after_commit :enqueue_linkedin_enrichment,
               on: [ :create, :update ],
               if: :should_enrich_from_linkedin?

  after_commit :reindex_applies_on_favorite_change,
               on: [ :create, :update ],
               if: :saved_change_to_favorite_user_ids?


  GENDER = [
    { id: 1, name: "Homem Cisgênero" },
    { id: 2, name: "Mulher Cisgênero" },
    { id: 3, name: "Homem Transgênero" },
    { id: 4, name: "Mulher Transgênero" },
    { id: 5, name: "Outro", specify: true },
    { id: 6, name: "Não quero informar" }
  ]

  MARITAL_STATUS = [
    { id: 1, name: "Solteiro(a)" },
    { id: 2, name: "Casado(a)" },
    { id: 3, name: "Divorciado(a)" },
    { id: 4, name: "Viúvo(a)" },
    { id: 5, name: "União Estável" },
    { id: 6, name: "Outro", specify: true },
    { id: 7, name: "Não quero informar" }
  ]

  def sync_vector_after_commit
    return unless embedding_fields_changed?
    Candidates::EmbeddingSyncJob.perform_later(id, updated_at.to_i, account_id)
  end

  def embedding_fields_changed?
    saved_change_to_name? ||
    saved_change_to_role_name? ||
    saved_change_to_position_level? ||
    saved_change_to_self_introduction? ||
    saved_change_to_curriculum_text? ||
    saved_change_to_interests? ||
    saved_change_to_current_company? ||
    saved_change_to_city? ||
    saved_change_to_state? ||
    saved_change_to_country? ||
    saved_change_to_street? ||
    saved_change_to_number? ||
    saved_change_to_district? ||
    saved_change_to_zip? ||
    saved_change_to_current_salary? ||
    saved_change_to_desired_salary? ||
    saved_change_to_currency? ||
    saved_change_to_clt_expectation? ||
    saved_change_to_pj_expectation? ||
    saved_change_to_freelance_expectation? ||
    saved_change_to_remote_work? ||
    saved_change_to_mobility? ||
    saved_change_to_linkedin? ||
    saved_change_to_github? ||
    saved_change_to_portfolio? ||
    saved_change_to_source?
  end

  after_commit(on: :destroy) do
    Candidates::EmbeddingDeleteJob.perform_later(id, account_id) if Rails.env.development? || Rails.env.production?
  end

  def skip_vector_sync
    @skip_vector_sync ||= false
  end

  def should_enrich_from_linkedin?
    return false if Rails.env.test?
    return false if linkedin.blank?
    return false unless saved_change_to_linkedin?
    return false unless LinkedinUrlValidator.valid?(linkedin)
    true
  end

  def reindex_applies_on_favorite_change
    ReindexAppliesForCandidateJob.perform_later(id, account_id)
  end

  def enqueue_linkedin_enrichment
    Rails.logger.info "🔄 [Candidate##{id}] Enqueuing LinkedIn enrichment"
    Candidates::LinkedinEnrichmentJob.perform_later(id, account_id)
  end

  def avatar_public_url
    return nil unless avatar.attached?
    Rails.application.routes.url_helpers.url_for(avatar)
  end

  def self.include_base
    select(column_names.map { |c| arel_table[c] })
  end

  # Elasticsearch search field configuration with boosts
  def self.search_fields
    [
      "name^3",              # Nome: peso médio
      "role_name^10",        # Cargo atual: peso muito alto
      "current_company^5",   # Empresa atual: peso médio-alto
      "all_companies^4",     # Todas as empresas (atual + anteriores): peso médio
      "previous_companies^3", # Empresas anteriores: peso médio-baixo
      "current_company_sectors^4", # Setores da empresa atual: peso médio
      "all_company_sectors^3",     # Setores de todas as empresas: peso médio-baixo
      "all_institutions^4",  # Todas as instituições de ensino: peso médio
      "all_study_areas^4",   # Todas as áreas de estudo: peso médio
      "all_education_levels^4", # Todos os níveis de formação: peso médio
      "skills^8",            # Skills: peso alto
      "curriculum_summary^7", # Currículo: peso alto - para busca textual
      "experiences_a^6",
      "recent_roles^6",      # Cargos recentes: peso alto
      "self_introduction^4", # Bio: peso médio
      "recent_companies^3",  # Empresas recentes
      "education_institutions^2",
      "study_areas^2"
    ]
  end

  def search_data
    candidate_data = Candidate.select(<<~SQL.squish)
      candidates.*,
      COUNT(DISTINCT evaluation_candidates.id) AS total_evaluations
    SQL
      .left_joins(:evaluation_candidates)
      .where(id: id)
      .group("candidates.id")
      .first

    return base_search_data unless candidate_data

    skills_data = skill_relationships_data
    languages_data = language_relationships_data
    educations_data = educations_summary_data
    experiences_data = experiences_summary_data

    {
      id: id,
      uid: uid,
      name: name&.downcase,
      email: email&.downcase,
      has_emails: email.present? && email != "",
      has_phone_numbers: mobile_phone.present? || phone.present?,
      has_contact: (email.present? && email != "") || mobile_phone.present? || phone.present?,
      gender: gender,
      gender_text: gender_text,
      marital_status: marital_status,
      marital_status_text: marital_status_text,
      age_range: calculate_age_range,
      city: city&.downcase,
      state: state&.downcase,
      remote_work: remote_work,
      remote_work_text: remote_work ? "Aceita remoto" : "Apenas presencial",
      work_model: resolved_work_model,
      mobility: mobility,
      mobility_text: mobility ? "Tem mobilidade" : "Sem mobilidade",
      mobile_phone: mobile_phone,
      phone: phone,
      current_company: current_company&.downcase,
      role_name: role_name&.downcase,
      position_level: position_level&.downcase,
      currency: currency,
      salary_range: calculate_salary_range,
      total_evaluations: candidate_data.total_evaluations || 0,
      current_role_time: current_role_time,
      average_time_in_companies: average_time_in_companies,
      created_at: created_at,
      updated_at: updated_at,
      account_id: account_id,
      is_deleted: is_deleted,
      has_curriculum: curriculum_text.present?,
      curriculum_text: curriculum_text&.downcase,
      pin_user_ids: pin_user_ids || [],
      favorite_user_ids: favorite_user_ids || [],
      confidential_user_ids: confidential_user_ids || nil,
      last_valid_apply_days_ago: last_valid_apply_days_ago,
      has_valid_apply: has_valid_apply,
      all_apply_job_ids: all_apply_job_ids,
      max_salary_expectation: [ clt_expectation || 0, pj_expectation || 0, freelance_expectation || 0 ].max,
      pcd: pcd,
      ethnicity: ethnicity,
      ethnicity_text: ethnicity,
      lgbtqia: lgbtqia,
      neurodivergent: neurodivergent,
      is_hidden: is_hidden,
      is_twin: is_twin,
      twin_source_id: twin_source_id,
      lgpd_expires_at: lgpd_expires_at,
      lgpd_active: lgpd_expires_at.nil? || lgpd_expires_at > Time.current,
      **applies_search_data,
      availability: try(:availability)
    }.merge(skill_relationships_data)
     .merge(languages_data)
     .merge(educations_data)
     .merge(experiences_data)
     .merge(sectors_data)
  end

  def self.agg_search_array(_params = {})
    {
      pcd:            { field: "pcd",            limit: 2 },
      ethnicity:      { field: "ethnicity",      limit: 10 },
      ethnicity_text: { field: "ethnicity_text", limit: 10 },
      lgbtqia:        { field: "lgbtqia",        limit: 2 },
      neurodivergent: { field: "neurodivergent", limit: 2 },
      is_hidden:      { field: "is_hidden",      limit: 2 },
      is_twin:        { field: "is_twin",        limit: 2 },
      gender: { field: "gender", limit: 10 },
      gender_text: { field: "gender_text", limit: 10 },
      marital_status: { field: "marital_status", limit: 10 },
      marital_status_text: { field: "marital_status_text", limit: 10 },
      age_range: { field: "age_range", limit: 10 },
      city: { field: "city", limit: 50 },
      state: { field: "state", limit: 30 },
      remote_work: { field: "remote_work", limit: 2 },
      remote_work_text: { field: "remote_work_text", limit: 2 },
      mobility: { field: "mobility", limit: 2 },
      mobility_text: { field: "mobility_text", limit: 2 },
      current_company: { field: "current_company", limit: 50 },
      previous_companies: { field: "previous_companies", limit: 100 },
      all_companies: { field: "all_companies", limit: 100 },
      all_institutions: { field: "all_institutions", limit: 100 },
      all_study_areas: { field: "all_study_areas", limit: 100 },
      all_education_levels: { field: "all_education_levels", limit: 20 },
      current_company_sectors: { field: "current_company_sectors", limit: 50 },
      all_company_sectors: { field: "all_company_sectors", limit: 100 },
      role_name: { field: "role_name", limit: 50 },
      position_level: { field: "position_level", limit: 20 },
      recent_companies: { field: "recent_companies", limit: 50 },
      experiences_a: { field: "experiences_a", limit: 200 },
      education_levels: { field: "education_levels", limit: 20 },
      skills: { field: "skills", limit: 200 },
      skill_categories: { field: "skill_categories", limit: 100 },
      languages: { field: "languages", limit: 30 },
      language_levels: { field: "language_levels", limit: 10 },
      languages_with_proficiency: { field: "languages_with_proficiency", limit: 100 },
      currency: { field: "currency", limit: 10 },
      salary_range: { field: "salary_range", limit: 20 },
      total_evaluations: { field: "total_evaluations", limit: 50 },
      current_role_time: { field: "current_role_time", limit: 50 },
      average_time_in_companies: { field: "average_time_in_companies", limit: 50 },
      favorite_user_ids: { field: "favorite_user_ids", limit: 5 },
      sectors_a: { field: "sectors_a", limit: 100 }
    }
  end

  def skill_relationships_data
    skills_with_categories = skill_relationships.includes(skill: :skill_category).map do |sr|
      {
        skill: sr.skill,
        category: sr.skill&.skill_category
      }
    end

    skills_list = skills_with_categories.map { |s| s[:skill]&.name&.downcase }.compact
    skill_categories_list = skills_with_categories
      .map { |s| s[:category]&.name&.downcase }
      .compact
      .uniq

    {
      skills: skills_list,
      skill_categories: skill_categories_list
    }
  end

  def last_valid_apply_days_ago
    last_apply = applies
      .where(is_deleted: false)
      .order(created_at: :desc)
      .first

    return nil unless last_apply

    ((Time.current - last_apply.created_at) / 1.day).to_i
  end

  def has_valid_apply
    applies.where(is_deleted: false).exists?
  end

  def all_apply_job_ids
    applies.where(is_deleted: false).pluck(:job_id).uniq
  end

  def recent_apply_job_ids(period_days)
    return [] unless period_days.present? && period_days.positive?

    applies
      .where(is_deleted: false)
      .where("applies.created_at >= ?", period_days.days.ago)
      .pluck(:job_id)
      .uniq
  end

  def current_role_time
    current_experience = experiences.find_by(work_here: true)
    return nil unless current_experience&.start_date

    start_date = current_experience.start_date
    now = Time.current

    years = (now.year - start_date.year)
    months = (now.month - start_date.month)

    total_months = (years * 12) + months
    total_months.positive? ? total_months : 0
  end

  def average_time_in_companies
    return nil if experiences.empty?

    experiences_by_company = experiences.group_by(&:company_id)

    company_durations = experiences_by_company.map do |company_id, company_experiences|
      total_months = company_experiences.sum do |exp|
        next 0 unless exp.start_date

        end_date = exp.end_date || Time.current
        start_date = exp.start_date

        years = (end_date.year - start_date.year)
        months = (end_date.month - start_date.month)

        total = (years * 12) + months
        total.positive? ? total : 0
      end

      total_months
    end

    valid_durations = company_durations.select { |d| d.positive? }
    return 0 if valid_durations.empty?

    (valid_durations.sum.to_f / valid_durations.size).round
  end

  private

  def resolved_work_model
    return work_model if work_model.present?
    return "remote" if remote_work == true
    "on_site" if remote_work == false
  end

  def applies_search_data
    active_applies = applies.where(is_deleted: false)
                            .pluck(:selective_process_status, :job_id, :updated_at)

    shortlisted = active_applies.select { |status, _, _| status == "shortlisted" }
    placed = active_applies.select { |status, _, _| status == "placement" }

    {
      selective_process_statuses: active_applies.map(&:first).compact.uniq,
      shortlisted_job_ids: shortlisted.map { |_, job_id, _| job_id }.compact,
      shortlisted_at: shortlisted.map { |_, _, updated| updated }.compact.max,
      placed_job_ids: placed.map { |_, job_id, _| job_id }.compact,
      placed_at: placed.map { |_, _, updated| updated }.compact.max
    }
  end

  def base_search_data
    {
      id: id,
      uid: uid,
      name: name&.downcase,
      email: email&.downcase,
      account_id: account_id,
      is_deleted: is_deleted,
      created_at: created_at
    }
  end

  def gender_text
    return nil if gender.nil?
    case gender
    when 0 then "Masculino"
    when 1 then "Feminino"
    when 2 then "Outro"
    when 3 then "Prefiro não informar"
    else "Não especificado"
    end
  end

  def marital_status_text
    return nil if marital_status.nil?
    case marital_status
    when 0 then "Solteiro(a)"
    when 1 then "Casado(a)"
    when 2 then "Divorciado(a)"
    when 3 then "Viúvo(a)"
    when 4 then "União estável"
    else "Não especificado"
    end
  end

  def calculate_age_range
    return nil unless date_birth
    age = ((Time.current - date_birth.to_time) / 1.year).to_i
    case age
    when 0..17 then "0-17"
    when 18..24 then "18-24"
    when 25..34 then "25-34"
    when 35..44 then "35-44"
    when 45..54 then "45-54"
    when 55..64 then "55-64"
    else "65+"
    end
  end

  def calculate_salary_range
    salary = [ clt_expectation || 0, pj_expectation || 0, freelance_expectation || 0 ].max
    return nil if salary <= 0
    case salary
    when 0..2999 then "0-2999"
    when 3000..4999 then "3000-4999"
    when 5000..7999 then "5000-7999"
    when 8000..11999 then "8000-11999"
    when 12000..19999 then "12000-19999"
    when 20000..29999 then "20000-29999"
    else "30000+"
    end
  end

  def language_relationships_data
    language_rels = language_relationships.includes(:language)

    languages_list = language_rels.map { |lr| lr.language&.name&.downcase }.compact

    levels_list = language_rels.map do |lr|
      normalize_proficiency_level(lr.level)
    end.compact

    languages_with_proficiency = language_rels.map do |lr|
      language_name = lr.language&.name&.downcase
      level = normalize_proficiency_level(lr.level)

      "#{language_name}:#{level}" if language_name.present? && level.present?
    end.compact

    {
      languages: languages_list,
      language_levels: languages_with_proficiency,
      languages_with_proficiency: languages_with_proficiency
    }
  end

  def normalize_proficiency_level(level)
    return nil if level.blank?

    normalized = level.to_s.strip.downcase

    proficiency_mapping = {
      "básico" => "basic",
      "basico" => "basic",
      "intermediário" => "intermediate",
      "intermediario" => "intermediate",
      "avançado" => "advanced",
      "avancado" => "advanced",
      "fluente" => "fluent",
      "nativo" => "native"
    }

    proficiency_mapping[normalized] || normalized
  end

  def educations_summary_data
    edus = educations.order(end_date: :desc).limit(5)
    all_edus = educations.includes(:institution, :study_area).order(end_date: :desc)

    all_institutions_list = all_edus
      .map { |edu| edu.institution&.name }
      .compact
      .map(&:downcase)
      .uniq

    all_study_areas_list = all_edus
      .map { |edu| edu.study_area&.name }
      .compact
      .map(&:downcase)
      .uniq

    all_education_levels_list = all_edus
      .map { |edu| map_formation_type_to_label(edu.formation_type) }
      .compact
      .map(&:downcase)
      .uniq

    {
      education_levels: edus.map { |edu| map_formation_type_name(edu.formation_type) }.compact.map(&:downcase),
      education_institutions: edus.map { |e| e.institution&.name }.compact.map(&:downcase),
      study_areas: edus.map { |e| e.study_area&.name }.compact.map(&:downcase),
      all_institutions: all_institutions_list,
      all_study_areas: all_study_areas_list,
      all_education_levels: all_education_levels_list
    }
  end

  def map_formation_type_to_label(type)
    return nil unless type
    case type.to_i
    when 1 then "high school"
    when 2 then "technical"
    when 3 then "online course"
    when 4 then "bachelors"
    when 5 then "postgraduate"
    when 6 then "masters"
    when 7 then "doctorate"
    when 8 then "phd"
    when 9 then "other"
    else nil
    end
  rescue
    nil
  end

  def map_formation_type_name(type)
    return nil unless type

    case type.to_i
    when 1 then "Elementary School"
    when 2 then "High School"
    when 3 then "Technical"
    when 4 then "Associate Degree"
    when 5 then "Bachelor"
    when 6 then "Teaching Degree"
    when 7 then "Postgraduate"
    else nil
    end
  rescue
    nil
  end

  def experiences_summary_data
    exps = experiences.includes(:company, :occupation).order(end_date: :desc).limit(10)
    all_exps = experiences.includes(:occupation, :company).order(end_date: :desc)

    years = experiences.sum do |exp|
      next 0 unless exp.start_date
      end_date = exp.end_date || Time.current
      start_date = exp.start_date
      ((end_date - start_date) / 1.year).to_i.abs
    end
    years_range = case years
    when 0..1 then "0-1"
    when 2..3 then "2-3"
    when 4..5 then "4-5"
    when 6..9 then "6-9"
    when 10..14 then "10-14"
    else "15+"
    end

    all_roles = all_exps
      .map { |exp| exp.occupation&.name }
      .compact
      .map(&:downcase)
      .uniq

    previous_roles = all_exps
      .select { |exp| exp.work_here != true }
      .map { |exp| exp.occupation&.name }
      .compact
      .map(&:downcase)
      .uniq

    previous_companies = all_exps
      .select { |exp| exp.is_deleted == false && exp.work_here == false }
      .map { |exp| exp.company&.name }
      .compact
      .map(&:downcase)
      .uniq

    all_companies_list = all_exps
      .select { |exp| exp.is_deleted == false }
      .map { |exp| exp.company&.name }
      .compact
      .map(&:downcase)
      .uniq

    if current_company.present?
      all_companies_list = ([ current_company.downcase ] + all_companies_list).uniq
    end

    current_company_sectors = []
    current_exp = all_exps.find { |exp| exp.work_here == true && exp.company.present? }
    if current_exp&.company
      current_company_sectors = SectorRelationship
        .where(reference_type: "Company", reference_id: current_exp.company_id, is_deleted: false)
        .includes(:sector)
        .map { |sr| sr.sector&.name }
        .compact
        .map(&:downcase)
        .uniq
    end

    company_ids = all_exps
      .select { |exp| exp.is_deleted == false && exp.company_id.present? }
      .map(&:company_id)
      .uniq

    all_company_sectors = []
    if company_ids.any?
      all_company_sectors = SectorRelationship
        .where(reference_type: "Company", reference_id: company_ids, is_deleted: false)
        .includes(:sector)
        .map { |sr| sr.sector&.name }
        .compact
        .map(&:downcase)
        .uniq
    end

    {
      recent_companies: exps.map(&:company).compact.map(&:name).map(&:downcase),
      recent_roles: exps.map { |exp| exp.occupation&.name }.compact.map(&:downcase),
      experiences_a: all_roles,
      previous_experiences: previous_roles,
      previous_companies: previous_companies,
      all_companies: all_companies_list,
      current_company_sectors: current_company_sectors,
      all_company_sectors: all_company_sectors,
      years_of_experience: years,
      years_of_experience_range: years_range
    }
  end

  def sectors_data
    sectors_list = sector_relationships
      .where(is_deleted: false)
      .includes(:sector)
      .map { |sr| sr.sector&.name }
      .compact
      .map(&:downcase)
      .uniq

    {
      sectors_a: sectors_list
    }
  end
end
