class CandidateFeedback < ApplicationRecord
  include Searchable
  include TracksJobAnalytics

  belongs_to :account
  belongs_to :user

  belongs_to :sourcing, optional: true
  belongs_to :apply, optional: true
  belongs_to :candidate, optional: true
  belongs_to :job, optional: true
  belongs_to :sourced_profile_sourcing, optional: true

  belongs_to :reference, polymorphic: true, optional: true

  validates :account_id, presence: true
  validates :user_id, presence: true

  validates :feedback_type,
            presence: true,
            inclusion: {
              in: %w[like dislike],
              message: "deve ser 'like' ou 'dislike'"
            }

  validate :at_least_one_context_present

  validates :candidate_id,
            uniqueness: {
              scope: [ :user_id, :sourcing_id, :apply_id, :sourced_profile_sourcing_id ],
              conditions: -> { where(is_deleted: false) },
              message: "já possui feedback neste contexto"
            },
            allow_nil: true

  scope :active,   -> { where(is_deleted: false) }
  scope :deleted,  -> { where(is_deleted: true) }

  scope :likes,     -> { where(feedback_type: "like") }
  scope :dislikes,  -> { where(feedback_type: "dislike") }

  scope :for_sourcing,  ->(sourcing_id)  { where(sourcing_id: sourcing_id) }
  scope :for_candidate, ->(candidate_id) { where(candidate_id: candidate_id) }
  scope :for_job,       ->(job_id)       { where(job_id: job_id) }
  scope :by_user,       ->(user_id)      { where(user_id: user_id) }
  scope :for_sourced_profile_sourcing, ->(sourced_profile_sourcing_id) { where(sourced_profile_sourcing_id: sourced_profile_sourcing_id) }

  scope :recent, -> { order(created_at: :desc) }

  def like?
    feedback_type == "like"
  end

  def dislike?
    feedback_type == "dislike"
  end

  def toggle_type!
    raise "Invalid feedback_type" unless %w[like dislike].include?(feedback_type)

    update!(feedback_type: like? ? "dislike" : "like")
  end

  def soft_delete!
    update!(is_deleted: true)
  end

  def restore!
    update!(is_deleted: false)
  end

  def search_data
    {
      id: id,
      account_id: account_id,
      user_id: user_id,
      sourcing_id: sourcing_id,
      apply_id: apply_id,
      candidate_id: candidate_id,
      job_id: job_id,
      sourced_profile_sourcing_id: sourced_profile_sourcing_id,
      reference_type: reference_type,
      reference_id: reference_id,
      reason: reason&.downcase,
      feedback_type: feedback_type,
      is_like: like?,
      is_dislike: dislike?,
      is_deleted: is_deleted,
      user_name: user&.name&.downcase,
      candidate_name: candidate&.name&.downcase,
      job_title: job&.title&.downcase,
      sourcing_query: sourcing&.query&.downcase,
      search_query_snapshot: search_query_snapshot,
      candidate_score_snapshot: candidate_score_snapshot,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.agg_search_array(_params = {})
    {
      feedback_type: { field: "feedback_type", limit: 5 },
      is_like:       { field: "is_like", limit: 2 },
      is_dislike:    { field: "is_dislike", limit: 2 },
      user_id:       { field: "user_id", limit: 25 },
      user_name:     { field: "user_name", limit: 25 },
      job_id:        { field: "job_id", limit: 25 },
      job_title:     { field: "job_title", limit: 25 },
      sourcing_id:   { field: "sourcing_id", limit: 25 },
      is_deleted:    { field: "is_deleted", limit: 2 }
    }
  end

  def self.find_existing(sourcing_id: nil, apply_id: nil, candidate_id: nil, sourced_profile_sourcing_id: nil, user_id:)
    return nil if user_id.blank?

    query = active.where(user_id: user_id)

    if apply_id.present?
      query.find_by(apply_id: apply_id)
    elsif sourced_profile_sourcing_id.present?
      query.find_by(sourced_profile_sourcing_id: sourced_profile_sourcing_id)
    elsif sourcing_id.present? && candidate_id.present?
      query.find_by(sourcing_id: sourcing_id, candidate_id: candidate_id)
    elsif candidate_id.present?
      query.find_by(candidate_id: candidate_id, sourcing_id: nil, apply_id: nil, sourced_profile_sourcing_id: nil)
    end
  end

  def self.stats_for_sourcing(sourcing_id)
    active.where(sourcing_id: sourcing_id)
          .group(:feedback_type)
          .count
  end

  def self.stats_for_candidate(candidate_id)
    active.where(candidate_id: candidate_id)
          .group(:feedback_type)
          .count
  end

  def self.stats_for_sourced_profile_sourcing(sourced_profile_sourcing_id)
    active.where(sourced_profile_sourcing_id: sourced_profile_sourcing_id)
          .group(:feedback_type)
          .count
  end

  def self.stats_by_user(account_id)
    active.where(account_id: account_id)
          .group(:user_id, :feedback_type)
          .count
  end

  private

  def at_least_one_context_present
    if sourcing_id.blank? && apply_id.blank? && candidate_id.blank? && sourced_profile_sourcing_id.blank?
      errors.add(:base, "Pelo menos um contexto deve estar presente: sourcing_id, apply_id, candidate_id ou sourced_profile_sourcing_id")
    end
  end
end
