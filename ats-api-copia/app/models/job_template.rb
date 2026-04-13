class JobTemplate < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  has_many :template_usage_logs, foreign_key: :template_id, dependent: :destroy

  validates :title, presence: true
end
