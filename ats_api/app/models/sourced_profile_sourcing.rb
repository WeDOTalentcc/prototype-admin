# frozen_string_literal: true

class SourcedProfileSourcing < ApplicationRecord
  include Searchable

  belongs_to :sourced_profile
  belongs_to :sourcing
  belongs_to :account
  belongs_to :user

  has_many :candidate_feedbacks, dependent: :nullify

  delegate :candidate, to: :sourced_profile, allow_nil: true

  def certifications
    raw = sourced_profile&.certifications || []
    raw.filter_map do |entry|
      case entry
      when String
        entry.strip.presence
      when Hash
        (entry["title"] || entry["name"] || entry[:title] || entry[:name]).presence&.to_s&.strip
      end
    end.uniq
  end

  validates :sourced_profile_id, presence: true, uniqueness: { scope: :sourcing_id }
  validates :sourcing_id, presence: true
  validates :account_id, presence: true
  validates :user_id, presence: true
  validates :score, numericality: { greater_than_or_equal_to: 0, less_than_or_equal_to: 100 }, allow_nil: true

  scope :active, -> { where(is_deleted: false) }

  after_commit :enqueue_ai_analysis, on: :create
  after_commit :enqueue_stats_recalculation, on: [ :create, :update, :destroy ]

  def self.include_base
    joins(:sourced_profile).select(<<~SQL)
      sourced_profile_sourcings.id,
      sourced_profile_sourcings.sourced_profile_id,
      sourced_profile_sourcings.sourcing_id,
      sourced_profile_sourcings.account_id,
      sourced_profile_sourcings.user_id,
      sourced_profile_sourcings.analysis,
      sourced_profile_sourcings.ai_metadata,
      sourced_profile_sourcings.score,
      sourced_profile_sourcings.score AS sourcing_score,
      sourced_profile_sourcings.search_source,
      sourced_profile_sourcings.search_score,
      sourced_profile_sourcings.similarity_score,
      sourced_profile_sourcings.is_deleted,
      sourced_profile_sourcings.created_at,
      sourced_profile_sourcings.updated_at,
      sourced_profiles.sourcing_id AS profile_sourcing_id,
      sourced_profiles.account_id AS profile_account_id,
      sourced_profiles.uid,
      sourced_profiles.provider,
      sourced_profiles.external_id,
      sourced_profiles.linkedin_slug,
      sourced_profiles.linkedin_url,
      sourced_profiles.name,
      sourced_profiles.first_name,
      sourced_profiles.middle_name,
      sourced_profiles.last_name,
      sourced_profiles.email,
      sourced_profiles.phone,
      sourced_profiles.cpf,
      sourced_profiles.date_birth,
      sourced_profiles.title,
      sourced_profiles.summary,
      sourced_profiles.picture_url,
      sourced_profiles.gender,
      sourced_profiles.marital_status,
      sourced_profiles.estimated_age,
      sourced_profiles.location,
      sourced_profiles.city,
      sourced_profiles.state,
      sourced_profiles.country,
      sourced_profiles.address,
      sourced_profiles.zip_code,
      sourced_profiles.remote_work,
      sourced_profiles.mobility,
      sourced_profiles.current_company,
      sourced_profiles.current_title,
      sourced_profiles.role_name,
      sourced_profiles.position_level,
      sourced_profiles.total_experience_years,
      sourced_profiles.currency,
      sourced_profiles.clt_expectation,
      sourced_profiles.pj_expectation,
      sourced_profiles.freelance_expectation,
      sourced_profiles.is_decision_maker,
      sourced_profiles.is_top_universities,
      sourced_profiles.expertise,
      sourced_profiles.languages_data,
      sourced_profiles.skills_data,
      sourced_profiles.behavioral_skills_list,
      sourced_profiles.has_emails,
      sourced_profiles.has_phone_numbers,
      sourced_profiles.followers_count,
      sourced_profiles.connections_count,
      sourced_profiles.profile_data,
      sourced_profiles.experiences_data,
      sourced_profiles.educations_data,
      sourced_profiles.certifications_data,
      sourced_profiles.awards_data,
      sourced_profiles.status,
      sourced_profiles.rating,
      sourced_profiles.internal_notes,
      sourced_profiles.tags,
      sourced_profiles.pin_user_ids,
      sourced_profiles.confidential_user_ids,
      sourced_profiles.candidate_id,
      sourced_profiles.profile_updated_at,
      sourced_profiles.last_viewed_at,
      sourced_profiles.is_deleted AS profile_is_deleted,
      sourced_profiles.created_at AS profile_created_at,
      sourced_profiles.updated_at AS profile_updated_at,
      sourced_profiles.emails,
      sourced_profiles.phones,
      sourced_profiles.emails_enriched_at,
      sourced_profiles.phones_enriched_at,
      sourced_profiles.linkedin,
      sourced_profiles.github,
      sourced_profiles.portfolio,
      sourced_profiles.secondary_email,
      sourced_profiles.mobile_phone,
      sourced_profiles.secondary_phone,
      sourced_profiles.street,
      sourced_profiles.number,
      sourced_profiles.district,
      sourced_profiles.complement,
      sourced_profiles.zip,
      sourced_profiles.nationality,
      sourced_profiles.self_introduction,
      sourced_profiles.curriculum_text,
      sourced_profiles.current_salary,
      sourced_profiles.desired_salary,
      sourced_profiles.interests,
      sourced_profiles.comments,
      sourced_profiles.source,
      sourced_profiles.curriculum_pdf_url,
      sourced_profiles.completed_register,
      sourced_profiles.accept_terms
    SQL
  end

  def search_data
    profile = sourced_profile
    return base_search_data unless profile

    skills_list = (profile.skills_data || []).map { |s| s.is_a?(Hash) ? s["name"] : s }.compact.map { |v| v.to_s.downcase }
    behavioral_skills_for_index = (profile.behavioral_skills_list || []).filter_map do |row|
      next unless row.is_a?(Hash)

      row["name"].presence&.to_s&.downcase
    end.uniq
    certifications_for_index = (profile.certifications_data || []).filter_map do |row|
      next unless row.is_a?(Hash)

      (row["title"].presence || row["name"].presence)&.to_s&.downcase
    end.uniq
    languages_list = (profile.languages_data || []).map { |l| l.is_a?(Hash) ? l["name"] : l }.compact.map { |v| v.to_s.downcase }
    languages_attributes = build_languages_attributes(profile.languages_data)
    language_levels = (profile.languages_data || []).map { |l| l.is_a?(Hash) ? l["level"] : nil }.compact.map { |v| v.to_s.downcase }

    recent_companies = profile.experience_by_company.map { |e| e[:company] }.compact.map { |v| v.to_s.downcase }
    recent_roles = profile.experience_by_company.flat_map { |e| e[:roles] }.compact.map { |v| v.to_s.downcase }

    education_levels = profile.educations.map do |e|
      value = e["degree"]&.first || e["education_level"]
      value.is_a?(Array) ? value.first : value
    end.compact.map { |v| v.to_s.downcase }

    education_institutions = profile.educations.map do |e|
      value = e["campus"] || e["institution"]
      value.is_a?(Array) ? value.first : value
    end.compact.map { |v| v.to_s.downcase }

    study_areas = profile.educations.map do |e|
      value = e["major"] || e["study_area"]
      value.is_a?(Array) ? value.first : value
    end.compact.map { |v| v.to_s.downcase }

    {
      id: id,
      sourced_profile_id: sourced_profile_id,
      sourcing_id: sourcing_id,
      account_id: account_id,
      user_id: user_id,
      sourcing_score: score,
      is_deleted: is_deleted,
      created_at: created_at,
      updated_at: updated_at,
      uid: profile.uid,
      external_id: profile.external_id,
      provider: profile.provider,
      name: profile.name&.downcase,
      email: profile.email&.downcase,
      phone: profile.phone,
      gender: profile.gender,
      gender_text: profile.gender_text&.downcase,
      marital_status: profile.marital_status,
      marital_status_text: profile.marital_status_text&.downcase,
      age_range: profile.calculate_age_range,
      estimated_age: profile.estimated_age,
      city: profile.city&.downcase,
      state: profile.state&.downcase,
      location: profile.location&.downcase,
      remote_work: profile.remote_work,
      remote_work_text: profile.remote_work ? "aceita remoto" : "apenas presencial",
      mobility: profile.mobility,
      mobility_text: profile.mobility ? "tem mobilidade" : "sem mobilidade",
      current_company: profile.current_company_name&.downcase,
      role_name: (profile.role_name || profile.current_role)&.downcase,
      position_level: profile.position_level&.downcase,
      currency: profile.currency,
      salary_range: profile.calculate_salary_range,
      desired_salary: profile.desired_salary&.to_f,
      total_experience_years: profile.total_experience_years,
      skills: skills_list,
      behavioral_skills: behavioral_skills_for_index,
      certifications: certifications_for_index,
      expertise: (profile.expertise || []).map { |e| e.is_a?(String) ? e.downcase : e.to_s.downcase },
      languages: languages_list,
      languages_attributes: languages_attributes&.downcase,
      language_levels: language_levels,
      recent_companies: recent_companies,
      recent_roles: recent_roles,
      education_levels: education_levels,
      education_institutions: education_institutions,
      study_areas: study_areas,
      status: profile.status,
      rating: profile.rating,
      tags: (profile.tags || []).map { |t| t.is_a?(String) ? t.downcase : t.to_s.downcase },
      has_emails: profile.has_emails,
      has_phone_numbers: profile.has_phone_numbers,
      has_linkedin: has_linkedin,
      is_top_universities: profile.is_top_universities,
      is_decision_maker: profile.is_decision_maker,
      imported: profile.imported?,
      sourcing_query: sourcing&.query&.downcase,
      pin_user_ids: profile.pin_user_ids || [],
      confidential_user_ids: profile.confidential_user_ids || [],
      profile_created_at: profile.created_at,
      profile_updated_at: profile.updated_at,
      last_viewed_at: profile.last_viewed_at,
      candidate_feedback: get_candidate_feedback_type
    }
  end

  def base_search_data
    {
      id: id,
      sourced_profile_id: sourced_profile_id,
      sourcing_id: sourcing_id,
      account_id: account_id,
      user_id: user_id,
      sourcing_score: score,
      is_deleted: is_deleted,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def has_linkedin
    profile = sourced_profile
    return false unless profile
  
    profile.linkedin_url.present? ||
      profile.linkedin.present? ||
      profile.linkedin_slug.present?
  end

  def self.agg_search_array(_params = {})
    {}
  end

  def languages_attributes
    build_languages_attributes(sourced_profile&.languages_data)
  end

  def behavioral_skills
    (sourced_profile&.behavioral_skills_list || []).filter_map do |row|
      next unless row.is_a?(Hash)

      row["name"].presence&.to_s
    end.uniq
  end

  def candidate_id
    sourced_profile&.candidate_id
  end

  def get_candidate_feedback_type
    feedback = candidate_feedbacks.active.first

    if feedback.blank? && sourcing_id.present? && candidate_id.present?
      feedback = CandidateFeedback.active
        .where(sourcing_id: sourcing_id, candidate_id: candidate_id)
        .first
    end

    feedback&.feedback_type
  end

  private

  def build_languages_attributes(languages_data)
    return "" unless languages_data.present?

    languages_list = (languages_data || []).map do |l|
      language_name = l.is_a?(Hash) ? (l["language"] || l["name"]) : l
      level = l.is_a?(Hash) ? (l["level"] || l["proficiency"]) : nil
      level ? "#{language_name} - #{level}" : language_name.to_s
    end.compact

    languages_list.join(", ")
  end

  def enqueue_stats_recalculation
    # force: true para ignorar cooldown quando candidato é adicionado/removido/atualizado
    Sourcings::CalculateStatsJob.perform_later(sourcing_id, { force: true, account_id: account_id })
  end

  def enqueue_ai_analysis
    Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    Rails.logger.info "🔍 [SourcedProfileSourcing] ENQUEUE AI ANALYSIS CHECK"
    Rails.logger.info "   ID: #{id}"
    Rails.logger.info "   Profile ID: #{sourced_profile_id}"
    Rails.logger.info "   Sourcing ID: #{sourcing_id}"
    Rails.logger.info "   Account ID: #{account_id}"

    Rails.logger.info "✅ [SourcedProfileSourcing] ENQUEUEING AI ANALYSIS JOB"
    Rails.logger.info "   Job args: [#{account_id}, #{sourced_profile_id}, #{sourcing_id}]"
    SourcedProfiles::AiAnalysisJob.perform_later(account_id, sourced_profile_id, sourcing_id)
    Rails.logger.info "✅ [SourcedProfileSourcing] JOB ENQUEUED SUCCESSFULLY"
    Rails.logger.info "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  end
end
