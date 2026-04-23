# frozen_string_literal: true

class Sourcing < ApplicationRecord
  include Searchable
  include SourcingAggregations

  belongs_to :user
  belongs_to :account
  belongs_to :job, optional: true
  belongs_to :search_archetype, optional: true
  has_many :sourced_profiles, dependent: :destroy
  has_many :sourced_profile_sourcings, dependent: :destroy
  has_many :agent_cycles, dependent: :nullify
  has_many :candidate_feedbacks, dependent: :destroy
  has_many_attached :files

  validates :uid, presence: true, uniqueness: true
  validates :query, presence: true
  validates :provider, inclusion: { in: %w[pearch linkedin local global hybrid background_agent] }
  validates :status, inclusion: { in: %w[done processing failed] }, allow_blank: true
  validates :files, content_type: [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain"
  ], if: -> { files.attached? }

  before_validation :generate_uid, on: :create

  scope :recent, -> { order(created_at: :desc) }
  scope :by_account, ->(account_id) { where(account_id: account_id) }
  scope :active, -> { where(is_deleted: false) }
  scope :completed, -> { where(status: "done") }
  scope :processing, -> { where(status: "processing") }
  scope :failed, -> { where(status: "failed") }
  scope :by_provider, ->(provider) { where(provider: provider) }
  scope :by_job, ->(job_id) { where(job_id: job_id) }
  scope :by_period, ->(start_date, end_date) { where(searched_at: start_date..end_date) }

  def local?
    provider == "local" || (provider == "hybrid" && parameters["sources"]&.include?("local"))
  end

  def global?
    provider == "global" || provider == "pearch" || (provider == "hybrid" && parameters["sources"]&.include?("global"))
  end

  def hybrid?
    provider == "hybrid"
  end

  def sources
    return [ provider ] unless hybrid?
    parameters["sources"] || []
  end

  def top_profiles(limit = 10)
    sourced_profile_sourcings
      .where(is_deleted: false)
      .includes(:sourced_profile)
      .order(score: :desc)
      .limit(limit)
      .map(&:sourced_profile)
  end

  def new_profiles
    sourced_profiles.active.where(status: "new")
  end

  EMPTY_PROFILE_STATS = {
    total: 0, new: 0, viewed: 0, interested: 0, contacted: 0,
    rejected: 0, hired: 0, imported: 0, avg_score: nil,
    avg_experience: nil, with_email: 0, with_phone: 0
  }.freeze

  def stats
    aggregated_stats&.dig("profile_stats")&.symbolize_keys || EMPTY_PROFILE_STATS
  end

  def score_distribution
    sourced_profile_sourcings.where(is_deleted: false).group(:score).count
  end

  def cost_per_profile
    self[:cost_per_profile] || 0
  end

  def roi_metrics
    profiles = sourced_profiles.active
    total = profiles.count
    useful = profiles.where(status: %w[interested contacted hired]).count

    {
      total_profiles: total,
      useful_profiles: useful,
      useful_percentage: total.zero? ? 0 : ((useful.to_f / total) * 100).round(2),
      credits_used: credits_used || 0,
      cost_per_useful: useful.zero? ? 0 : ((credits_used || 0).to_f / useful).round(2)
    }
  end

  def search_data
    profile_stats = aggregated_stats&.dig("profile_stats") || {}

    {
      id: id,
      uid: uid,
      query: query&.downcase,
      provider: provider,
      status: status,
      results_count: results_count,
      credits_used: credits_used,
      cost_per_profile: cost_per_profile,
      searched_at: searched_at,
      account_id: account_id,
      user_id: user_id,
      saved: saved,
      is_deleted: is_deleted,
      total_profiles: profile_stats["total"] || 0,
      profiles_new: profile_stats["new"] || 0,
      profiles_viewed: profile_stats["viewed"] || 0,
      profiles_interested: profile_stats["interested"] || 0,
      profiles_contacted: profile_stats["contacted"] || 0,
      profiles_rejected: profile_stats["rejected"] || 0,
      profiles_hired: profile_stats["hired"] || 0,
      profiles_imported: profile_stats["imported"] || 0,
      avg_score: profile_stats["avg_score"],
      avg_experience: profile_stats["avg_experience"],
      profiles_with_email: profile_stats["with_email"] || 0,
      profiles_with_phone: profile_stats["with_phone"] || 0,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def enqueue_stats_calculation
    Sourcings::CalculateStatsJob.perform_later(id, { force: true, account_id: account_id })
  end

  def stats_for_domain_prompt
    {
      sourcing: {
        id: id,
        query: query,
        name: name,
        provider: provider,
        created_at: created_at
      },
      stats: aggregated_stats.presence || {}
    }
  end

  private

  def generate_uid
    self.uid ||= SecureRandom.uuid
  end
end
