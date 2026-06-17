# frozen_string_literal: true

class AtsConnection < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  has_many :ats_sync_jobs, foreign_key: :connection_id, dependent: :destroy
  has_many :ats_candidates, foreign_key: :connection_id, dependent: :destroy
  has_many :ats_webhook_logs, foreign_key: :connection_id, dependent: :destroy
  has_many :ats_job_mappings, foreign_key: :connection_id, dependent: :destroy

  validates :company_id, :provider, presence: true
end
