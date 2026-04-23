class EmbeddingCache < ApplicationRecord
  has_neighbors :embedding
  belongs_to :account

  validates :key, presence: true, uniqueness: true
  validates :model_version, presence: true
  validates :query_text, presence: true
  validates :embedding, presence: true
  validates :account_id, presence: true

  scope :by_account, ->(account_id) { where(account_id: account_id) }
  scope :by_model_version, ->(version) { where(model_version: version) }
  scope :stale, ->(ttl) { where("last_accessed_at < ?", ttl.ago) }

  def touch_access
    increment!(:hit_count)
    touch(:last_accessed_at)
  end

  def self.cleanup_stale!(ttl: 30.days)
    deleted = stale(ttl).delete_all
    Rails.logger.info("[EmbeddingCache] Cleaned up #{deleted} stale entries")
    deleted
  end
end
