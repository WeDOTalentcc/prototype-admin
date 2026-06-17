class SearchArchetype < ApplicationRecord
  include Searchable

  belongs_to :account
  belongs_to :user, optional: true
  has_many :sourcings, dependent: :nullify

  enum :seniority, {
    intern: 0, junior: 1, mid: 2, senior: 3,
    lead: 4, manager: 5, director: 6, c_level: 7
  }, prefix: true

  enum :work_model, {
    any_work_model: 0, remote: 1, hybrid: 2, onsite: 3
  }, prefix: true

  enum :contract_type, {
    any_contract: 0, clt: 1, pj: 2, freelance: 3
  }, prefix: true

  validates :name, :uid, presence: true
  validates :uid, uniqueness: true

  before_validation :generate_uid, on: :create
  before_save :normalize_arrays

  scope :active, -> { where(is_deleted: false) }

  SENIORITY_LABELS = {
    "intern" => "Estágio",
    "junior" => "Júnior",
    "mid" => "Pleno",
    "senior" => "Sênior",
    "lead" => "Tech Lead",
    "manager" => "Gerente",
    "director" => "Diretor",
    "c_level" => "C-Level"
  }.freeze

  WORK_MODEL_LABELS = {
    "any_work_model" => "Qualquer",
    "remote" => "Remoto",
    "hybrid" => "Híbrido",
    "onsite" => "Presencial"
  }.freeze

  CONTRACT_TYPE_LABELS = {
    "any_contract" => "Qualquer",
    "clt" => "CLT",
    "pj" => "PJ",
    "freelance" => "Freelance"
  }.freeze

  def search_data
    {
      id: id,
      uid: uid,
      name: name&.downcase,
      description: description&.downcase,
      query: query&.downcase,
      emoji: emoji,
      seniority: seniority,
      seniority_text: seniority_label,
      work_model: work_model,
      work_model_text: work_model_label,
      contract_type: contract_type,
      contract_type_text: contract_type_label,
      min_experience_years: min_experience_years,
      industry: industry&.downcase,
      location: location&.downcase,
      skills: normalized_skills,
      tags: normalized_tags,
      languages: normalized_languages,
      is_default: is_default,
      is_public: is_public,
      is_deleted: is_deleted,
      usage_count: usage_count,
      last_used_at: last_used_at,
      account_id: account_id,
      user_id: user_id,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.agg_search_array(_params = {})
    {
      seniority: { field: "seniority", limit: 10 },
      seniority_text: { field: "seniority_text", limit: 10 },
      work_model: { field: "work_model", limit: 5 },
      work_model_text: { field: "work_model_text", limit: 5 },
      contract_type: { field: "contract_type", limit: 5 },
      contract_type_text: { field: "contract_type_text", limit: 5 },
      industry: { field: "industry", limit: 30 },
      skills: { field: "skills", limit: 100 },
      tags: { field: "tags", limit: 50 },
      languages: { field: "languages", limit: 20 },
      is_default: { field: "is_default", limit: 2 },
      is_public: { field: "is_public", limit: 2 },
      user_id: { field: "user_id", limit: 50 }
    }
  end

  def seniority_label
    SENIORITY_LABELS[seniority] || seniority&.humanize
  end

  def work_model_label
    WORK_MODEL_LABELS[work_model] || work_model&.humanize
  end

  def contract_type_label
    CONTRACT_TYPE_LABELS[contract_type] || contract_type&.humanize
  end

  def filters_for(source)
    return { query: query } unless %w[local global].include?(source.to_s)

    source.to_s == "local" ? build_local_filters : build_global_filters
  end

  def execute_search!(user:, sources: [ "local", "global" ])
    increment!(:usage_count)
    update!(last_used_at: Time.current)

    SearchArchetypes::ExecuteSearchService.call(
      archetype: self,
      user: user,
      sources: Array(sources)
    )
  end

  def duplicate_for(user)
    dup.tap do |new_archetype|
      new_archetype.uid = nil
      new_archetype.user = user
      new_archetype.is_default = false
      new_archetype.is_public = false
      new_archetype.usage_count = 0
      new_archetype.last_used_at = nil
      new_archetype.name = "#{name} (cópia)"
    end
  end

  private

  def generate_uid
    self.uid ||= SecureRandom.uuid
  end

  def normalize_arrays
    self.skills = normalized_array(skills)
    self.tags = normalized_array(tags)
    self.languages = normalized_array(languages)
  end

  def normalized_array(array)
    return [] if array.blank?
    array.map(&:strip).reject(&:blank?).uniq
  end

  def normalized_skills
    normalized_array(skills).map(&:downcase)
  end

  def normalized_tags
    normalized_array(tags).map(&:downcase)
  end

  def normalized_languages
    normalized_array(languages).map(&:downcase)
  end

  def build_local_filters
    base = symbolized_filters(local_filters)
    base.deep_merge(local_structured_filters)
  end

  def build_global_filters
    base = symbolized_filters(global_filters)
    base.deep_merge(global_structured_filters)
  end

  def symbolized_filters(filters)
    (filters.presence || {}).deep_symbolize_keys
  end

  def local_structured_filters
    {
      skills: skills.presence,
      position_level: seniority&.to_s,
      remote_work: work_model_remote? ? true : nil,
      city: extract_city,
      state: extract_state,
      languages: languages.presence
    }.compact
  end

  def global_structured_filters
    {
      years_experience: min_experience_years,
      current_or_past_titles: query_titles,
      locations: location.present? ? [ location ] : nil,
      skills: skills.presence,
      languages: languages.presence
    }.compact
  end

  def extract_city
    return nil if location.blank?
    location.split(",").first&.strip
  end

  def extract_state
    return nil if location.blank?
    parts = location.split(",")
    return nil if parts.size < 2
    parts[1]&.strip
  end

  def query_titles
    return nil if query.blank?
    query.split(/[,;]/).map(&:strip).first(3)
  end
end
