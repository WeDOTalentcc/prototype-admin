# frozen_string_literal: true

class SourcedProfile < ApplicationRecord
  include Searchable

  def self.search_fields_mapping
    {
      provider: :keyword,
      gender: :keyword,
      gender_text: :keyword,
      marital_status: :keyword,
      marital_status_text: :keyword,
      age_range: :keyword,
      city: :keyword,
      state: :keyword,
      remote_work: :boolean,
      mobility: :boolean,
      current_company: :text,
      role_name: :text,
      position_level: :keyword,
      currency: :keyword,
      salary_range: :keyword,
      status: :keyword,
      rating: :integer,
      tags: :keyword,
      is_top_universities: :boolean,
      is_decision_maker: :boolean,
      imported: :boolean,
      behavioral_skills: :keyword
    }
  end

  def self.behavioral_skills_list_from_candidate(candidate)
    return [] unless candidate&.persisted?

    candidate.behavioral_skill_relationships
      .where(is_deleted: false)
      .includes(:behavioral_skill)
      .order(:priority)
      .filter_map do |rel|
        skill = rel.behavioral_skill
        next unless skill&.name.present?

        {
          "behavioral_skill_id" => skill.id,
          "name" => skill.name,
          "priority" => rel.priority,
          "level_skill" => rel.level_skill,
          "experience_time" => rel.experience_time,
          "main" => rel.main
        }
      end
  end

  belongs_to :sourcing, optional: true
  belongs_to :account
  belongs_to :candidate, optional: true
  has_many :sourced_profile_activities, dependent: :destroy
  has_many :sourced_profile_sourcings, dependent: :destroy
  has_many :sourcings, through: :sourced_profile_sourcings
  has_many :sector_relationships, as: :reference, dependent: :destroy
  has_many :sectors, through: :sector_relationships
  has_many :skill_relationships, as: :reference, dependent: :destroy
  has_many :skills, through: :skill_relationships

  validates :uid, presence: true, uniqueness: true
  validates :external_id, presence: true
  validates :provider, inclusion: { in: %w[pearch linkedin local hybrid] }
  validates :status, inclusion: { in: %w[new viewed interested contacted rejected hired] }
  validates :rating, numericality: { only_integer: true, greater_than_or_equal_to: 1, less_than_or_equal_to: 5 }, allow_nil: true
  validates :gender, inclusion: { in: 0..6 }, allow_nil: true
  validates :marital_status, inclusion: { in: 0..7 }, allow_nil: true

  before_validation :generate_uid, on: :create
  before_validation :build_full_name, if: -> { name.blank? && (first_name.present? || last_name.present?) }
  before_validation :extract_location_data, if: -> { location.present? && (city.blank? || state.blank?) }
  before_save :normalize_data
  after_update :broadcast_profile_updated

  after_update :log_status_change, if: :saved_change_to_status?
  after_update :log_rating_change, if: :saved_change_to_rating?

  scope :recent, -> { order(created_at: :desc) }
  scope :active, -> { where(is_deleted: false) }
  scope :by_status, ->(status) { where(status: status) }
  # Score moved to SourcedProfileSourcing
  scope :with_email, -> { where(has_emails: true) }
  scope :with_phone, -> { where(has_phone_numbers: true) }
  scope :with_contact, -> { where("has_emails = ? OR has_phone_numbers = ?", true, true) }
  scope :with_ai_analysis, -> { joins(:sourced_profile_sourcings).where.not(sourced_profile_sourcings: { analysis: nil }).distinct }
  scope :without_ai_analysis, lambda {
    left_joins(:sourced_profile_sourcings)
      .where(sourced_profile_sourcings: { id: nil })
      .or(
        left_joins(:sourced_profile_sourcings)
          .where("sourced_profile_sourcings.analysis IS NULL OR sourced_profile_sourcings.analysis = '{}'::jsonb")
      ).distinct
  }
  scope :not_imported, -> { where(candidate_id: nil) }
  scope :imported, -> { where.not(candidate_id: nil) }
  scope :by_provider, ->(provider) { where(provider: provider) }
  scope :by_experience_range, ->(min, max) { where(total_experience_years: min..max) }
  scope :by_location, ->(location) { where("location ILIKE ? OR city ILIKE ? OR state ILIKE ?", "%#{location}%", "%#{location}%", "%#{location}%") }
  scope :by_company, ->(company) { where("current_company ILIKE ?", "%#{company}%") }
  scope :with_expertise, ->(skills) { where("expertise ?| array[:skills]", skills: Array(skills)) }
  scope :with_tags, ->(tags) { where("tags ?| array[:tags]", tags: Array(tags)) }

  def full_name
    name || [ first_name, middle_name, last_name ].compact.join(" ")
  end

  def imported?
    candidate_id.present?
  end

  def mark_as_viewed!
    return unless status == "new"
    update(status: "viewed", last_viewed_at: Time.current)
    log_activity("viewed")
  end

  def experiences
    experiences_data || profile_data.dig("experiences") || []
  end

  def educations
    educations_data || profile_data.dig("educations") || []
  end

  def certifications
    certifications_data || profile_data.dig("certifications") || []
  end

  def awards
    awards_data || profile_data.dig("awards") || []
  end

  def current_experience
    experiences
      .flat_map { |exp| exp["company_roles"] || [] }
      .find { |role| role["is_current_experience"] }
  end

  def current_company_name
    current_company || begin
      exp = experiences.find do |e|
        e.dig("company_roles")&.any? { |role| role["is_current_experience"] }
      end
      exp&.dig("company_info", "name")
    end
  end

  def current_role
    current_title || current_experience&.dig("title")
  end

  def current_company_info
    experiences.find do |exp|
      exp.dig("company_roles")&.any? { |role| role["is_current_experience"] }
    end&.dig("company_info")
  end

  def previous_companies
    experiences
      .map { |exp| exp.dig("company_info", "name") }
      .compact
      .uniq
  end

  def experience_by_company
    experiences.map do |exp|
      roles = exp["company_roles"] || []
      total_duration = roles.sum { |role| role["duration_years"].to_f }

      {
        company: exp.dig("company_info", "name"),
        duration: total_duration.round(1),
        roles: roles.map { |r| r["title"] },
        current: roles.any? { |r| r["is_current_experience"] }
      }
    end.sort_by { |e| e[:current] ? 0 : 1 }
  end

  def summary_insights
    analysis = latest_analysis_payload
    return [] unless analysis.present?

    Array(analysis["query_insights"]).map do |insight|
      {
        subquery: insight["subquery"],
        priority: insight["priority"],
        match_level: insight["match_level"],
        rationale: insight["short_rationale"],
        quotes: insight["short_quotes"]
      }
    end
  end

  def overall_summary
    latest_analysis_payload.to_h.dig("overall_summary")
  end

  def similar_profiles(limit = 5)
    return [] if expertise.empty?

    SourcedProfile
      .active
      .where(account_id: account_id)
      .where.not(id: id)
      .where("expertise && ARRAY[?]::varchar[]", expertise.take(10))
      .order(created_at: :desc)
      .limit(limit)
  end

  def gender_text
    gender_name&.downcase
  end

  def marital_status_text
    marital_status_name&.downcase
  end

  def latest_analysis_payload
    raw = sourced_profile_sourcings.order(created_at: :desc).find { |sps| sps.analysis.present? }&.analysis
    return {} if raw.blank?

    raw.is_a?(String) ? JSON.parse(raw) : raw
  rescue JSON::ParserError
    {}
  end

  def sectors_list
    sector_relationships
      .where(is_deleted: false)
      .includes(:sector)
      .map { |sr| sr.sector&.name }
      .compact
      .map(&:downcase)
      .uniq
  end

  AGE_RANGES = [
    [ 0..17, "0-17" ],
    [ 18..24, "18-24" ],
    [ 25..34, "25-34" ],
    [ 35..44, "35-44" ],
    [ 45..54, "45-54" ],
    [ 55..64, "55-64" ]
  ].freeze

  SALARY_RANGES = [
    [ 0..2999, "0-2999" ],
    [ 3000..4999, "3000-4999" ],
    [ 5000..7999, "5000-7999" ],
    [ 8000..11999, "8000-11999" ],
    [ 12000..19999, "12000-19999" ],
    [ 20000..29999, "20000-29999" ]
  ].freeze

  def calculate_age_range
    return nil unless date_birth || estimated_age

    age = estimated_age || ((Time.current - date_birth.to_time) / 1.year).to_i
    AGE_RANGES.find { |range, _| range.cover?(age) }&.last || "65+"
  end

  def calculate_salary_range
    salary = [ clt_expectation || 0, pj_expectation || 0, freelance_expectation || 0 ].max
    return nil if salary <= 0

    SALARY_RANGES.find { |range, _| range.cover?(salary) }&.last || "30000+"
  end

  # Elasticsearch
  def search_data
    skills_list = (skills_data || []).map { |s| s.is_a?(Hash) ? s["name"] : s }.compact.map(&:downcase)
    behavioral_skills_search = (behavioral_skills_list || []).filter_map do |row|
      next unless row.is_a?(Hash)

      row["name"].presence&.downcase
    end.uniq
    languages_list = (languages_data || []).map { |l| l.is_a?(Hash) ? (l["language"] || l["name"]) : l }.compact.map(&:downcase)
    language_levels = (languages_data || []).map { |l| l.is_a?(Hash) ? (l["proficiency"] || l["level"]) : nil }.compact.map(&:downcase)

    languages_with_proficiency = (languages_data || []).map do |l|
      if l.is_a?(Hash)
        language_name = l["language"]&.downcase || l["name"]&.downcase
        proficiency = l["proficiency"]

        if language_name.present? && proficiency.present?
          normalized_proficiency = normalize_pearch_proficiency(proficiency)
          "#{language_name}:#{normalized_proficiency}" if normalized_proficiency.present?
        end
      end
    end.compact

    recent_companies = experience_by_company.map { |e| e[:company] }.compact.map(&:downcase)
    recent_roles = experience_by_company.flat_map { |e| e[:roles] }.compact.map(&:downcase)

    education_levels = educations.flat_map do |e|
      degree = e["degree"]
      level = degree.is_a?(Array) ? degree : [ degree ]
      level.presence || [ e["education_level"] ]
    end.compact.map { |l| l.to_s.downcase }

    education_institutions = educations.map { |e| e["campus"] || e["institution"] }.compact.map { |i| i.to_s.downcase }
    study_areas = educations.map { |e| e["major"] || e["study_area"] }.compact.map { |s| s.to_s.downcase }

    {
      id: id,
      uid: uid,
      external_id: external_id,
      provider: provider,
      name: name&.downcase,
      email: email&.downcase,
      phone: phone,
      gender: gender,
      gender_text: gender_text&.downcase,
      marital_status: marital_status,
      marital_status_text: marital_status_text&.downcase,
      age_range: calculate_age_range,
      estimated_age: estimated_age,
      city: city&.downcase,
      state: state&.downcase,
      location: location&.downcase,
      remote_work: remote_work,
      remote_work_text: remote_work ? "aceita remoto" : "apenas presencial",
      mobility: mobility,
      mobility_text: mobility ? "tem mobilidade" : "sem mobilidade",
      current_company: current_company_name&.downcase,
      role_name: (role_name || current_role)&.downcase,
      position_level: position_level&.downcase,
      currency: currency,
      salary_range: calculate_salary_range,
      total_experience_years: total_experience_years,
      skills: skills_list,
      behavioral_skills: behavioral_skills_search,
      expertise: (expertise || []).filter_map { |e| e.is_a?(String) ? e.downcase : nil },
      languages: languages_list,
      language_levels: language_levels,
      languages_with_proficiency: languages_with_proficiency,
      recent_companies: recent_companies,
      recent_roles: recent_roles,
      education_levels: education_levels,
      education_institutions: education_institutions,
      study_areas: study_areas,
      status: status,
      rating: rating,
      tags: (tags || []).map(&:downcase),
      has_emails: has_emails,
      has_phone_numbers: has_phone_numbers,
      is_top_universities: is_top_universities,
      is_decision_maker: is_decision_maker,
      imported: imported?,
      has_candidate: candidate_id.present?,
      sourcing_id: sourcing_id,
      sourcing_query: sourcing&.query&.downcase,
      account_id: account_id,
      is_deleted: is_deleted,
      pin_user_ids: pin_user_ids || [],
      confidential_user_ids: confidential_user_ids || [],
      created_at: created_at,
      updated_at: updated_at,
      last_viewed_at: last_viewed_at,
      sectors_a: sectors_list
    }
  end

  def self.agg_search_array(_params = {})
    {
      provider: { field: "provider", limit: 5 },
      gender: { field: "gender", limit: 10 },
      gender_text: { field: "gender_text", limit: 10 },
      marital_status: { field: "marital_status", limit: 10 },
      age_range: { field: "age_range", limit: 10 },
      city: { field: "city", limit: 50 },
      state: { field: "state", limit: 30 },
      remote_work: { field: "remote_work", limit: 2 },
      mobility: { field: "mobility", limit: 2 },
      current_company: { field: "current_company", limit: 50 },
      role_name: { field: "role_name", limit: 50 },
      position_level: { field: "position_level", limit: 20 },
      recent_companies: { field: "recent_companies", limit: 50 },
      education_levels: { field: "education_levels", limit: 20 },
      skills: { field: "skills", limit: 200 },
      behavioral_skills: { field: "behavioral_skills", limit: 200 },
      expertise: { field: "expertise", limit: 200 },
      languages: { field: "languages", limit: 30 },
      language_levels: { field: "language_levels", limit: 10 },
      languages_with_proficiency: { field: "languages_with_proficiency", limit: 50 },
      currency: { field: "currency", limit: 10 },
      salary_range: { field: "salary_range", limit: 20 },
      status: { field: "status", limit: 10 },
      rating: { field: "rating", limit: 5 },
      tags: { field: "tags", limit: 50 },
      is_top_universities: { field: "is_top_universities", limit: 2 },
      is_decision_maker: { field: "is_decision_maker", limit: 2 },
      imported: { field: "imported", limit: 2 },
      sectors_a: { field: "sectors_a", limit: 100 }
    }
  end

  def gender_name
    return nil if gender.nil?
    Candidate::GENDER.find { |g| g[:id] == gender + 1 }&.dig(:name)
  end

  def marital_status_name
    return nil if marital_status.nil?
    Candidate::MARITAL_STATUS.find { |m| m[:id] == marital_status + 1 }&.dig(:name)
  end

  def gender_text
    gender_name&.downcase
  end

  def marital_status_text
    marital_status_name&.downcase
  end

  def avatar_url
    picture_url
  end

  def url
    "/user/sourced_profiles/#{id}"
  end

  def pin
    false
  end

  def confidential
    false
  end

  def ensure_sourced_profile_sourcing(sourcing, account, user)
    return nil unless sourcing.present? && sourcing.user_id.present?

    sourced_profile_sourcings.find_or_create_by!(sourcing_id: sourcing.id, account_id: account_id, user_id: sourcing.user_id, sourced_profile_id: id) do |sps|
      sps.analysis = nil
      sps.is_deleted = false
    end
  rescue ActiveRecord::RecordNotUnique
    sourced_profile_sourcings.find_by(sourcing_id: sourcing.id, sourced_profile_id: id)
  rescue => e
    Rails.logger.error "Failed to ensure SourcedProfileSourcing: #{e.message}"
    nil
  end

  def self.find_existing_by_identity(external_id:, account_id:, cpf: nil, email: nil, linkedin_url: nil, phone: nil)
    return nil unless account_id.present?

    query = active.where(account_id: account_id)
    conditions = []

    if external_id.present?
      conditions << query.where(external_id: external_id)
    end

    if cpf.present?
      conditions << query.where(cpf: cpf)
    end

    if email.present?
      conditions << query.where("LOWER(email) = LOWER(?)", email)
    end

    if linkedin_url.present?
      conditions << query.where("linkedin_url = ? OR linkedin_slug = ?", linkedin_url, extract_linkedin_slug(linkedin_url))
    end

    if phone.present?
      normalized_phone = normalize_phone(phone)
      conditions << query.where("phone = ? OR phone = ?", phone, normalized_phone)
    end

    return nil if conditions.empty?

    conditions.each do |condition|
      profile = condition.first
      return profile if profile.present?
    end

    nil
  end

  def self.extract_linkedin_slug(url)
    return nil unless url.present?
    return url if url.exclude?("/")

    url.split("/").last&.split("?")&.first
  end

  def self.normalize_phone(phone)
    return nil unless phone.present?
    phone.gsub(/\D/, "")
  end

  private

  # Normaliza níveis de proficiência da Pearch (CEFR) para formato interno
  # CEFR: A1, A2 (básico), B1, B2 (intermediário), C1 (avançado), C2 (fluente/nativo)
  def normalize_pearch_proficiency(proficiency)
    return nil if proficiency.blank?

    level = proficiency.to_s.upcase.strip

    case level
    when "A1", "A2"
      "basic"
    when "B1", "B2"
      "intermediate"
    when "C1"
      "advanced"
    when "C2"
      "fluent"
    else
      # Se já vier em formato textual (basic, intermediate, etc), retorna lowercase
      proficiency.to_s.downcase
    end
  end

  def generate_uid
    self.uid ||= SecureRandom.uuid
  end

  def build_full_name
    self.name = [ first_name, middle_name, last_name ].compact.join(" ")
  end

  def extract_location_data
    parts = location.split(",").map(&:strip)
    self.city ||= parts[0] if parts.size >= 2
    self.state ||= parts[1] if parts.size >= 2
    self.country ||= parts.last if parts.size >= 3
  end

  def log_status_change
    log_activity("status_changed", old_value: status_before_last_save, new_value: status)
  end

  def log_rating_change
    log_activity("rated", old_value: rating_before_last_save, new_value: rating)
  end

  def log_activity(activity_type, old_value: nil, new_value: nil)
    sourced_profile_activities.create(
      user: Current.user,
      uid: SecureRandom.uuid,
      activity_type: activity_type,
      old_value: old_value,
      new_value: new_value
    )
  rescue => e
    Rails.logger.error "Failed to log activity: #{e.message}"
  end

  def normalize_data
    self.linkedin ||= linkedin_url || profile_data.dig("linkedin_url")
    self.zip ||= zip_code
    extract_contacts_from_arrays
    normalize_salary_fields
  end

  def extract_contacts_from_arrays
    return unless emails.is_a?(Array) || phones.is_a?(Array)

    if emails.is_a?(Array) && email.blank?
      first_email = emails.first
      self.email ||= first_email.is_a?(Hash) ? first_email.dig("email") : first_email
    end

    if emails.is_a?(Array) && secondary_email.blank?
      second_email = emails.second
      self.secondary_email ||= second_email.is_a?(Hash) ? second_email.dig("email") : second_email
    end

    if phones.is_a?(Array) && phone.blank?
      first_phone = phones.first
      self.phone ||= first_phone.is_a?(Hash) ? first_phone.dig("phone") : first_phone
    end

    if phones.is_a?(Array) && mobile_phone.blank?
      second_phone = phones.second
      self.mobile_phone ||= second_phone.is_a?(Hash) ? second_phone.dig("phone") : second_phone
    end
  end

  def normalize_salary_fields
    self.current_salary ||= calculate_average_expectation if clt_expectation || pj_expectation
  end

  def calculate_average_expectation
    expectations = [ clt_expectation, pj_expectation, freelance_expectation ].compact
    return nil if expectations.empty?
    expectations.sum / expectations.size
  end

  def broadcast_profile_updated
    return unless saved_changes.keys.intersect?(%w[status rating internal_notes tags])

    sourced_profile_sourcings.each do |sps|
      ActionCable.server.broadcast(
        "sourcing_#{sps.sourcing_id}",
        {
          type: "profile_updated",
          profile: profile_broadcast_payload,
          changes: saved_changes.slice("status", "rating", "internal_notes", "tags")
        }
      )
    end
  end

  def profile_broadcast_payload
    {
      id: id,
      uid: uid,
      name: name,
      email: email,
      title: title,
      current_company: current_company_name,
      location: location,
      status: status,
      rating: rating,
      has_emails: has_emails,
      has_phone_numbers: has_phone_numbers,
      picture_url: picture_url,
      linkedin_url: linkedin_url
    }
  end
end
