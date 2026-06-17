# frozen_string_literal: true

class TalentPool < ApplicationRecord
  belongs_to :account
  belongs_to :ideal_profile, optional: true
  belongs_to :created_by_user, class_name: "User", optional: true

  has_many :talent_pool_candidates, dependent: :destroy
  has_many :candidates, through: :talent_pool_candidates

  validates :name, presence: true
  validates :status, inclusion: { in: %w[active paused archived] }

  scope :active, -> { where(status: "active") }
  scope :for_account, ->(account_id) { where(account_id: account_id) }

  def update_counters!
    update_columns(
      candidates_count: talent_pool_candidates.count,
      screened_count: talent_pool_candidates.where(stage: "screened").count,
      ready_count: talent_pool_candidates.where(stage: "ready").count
    )
  end
end
