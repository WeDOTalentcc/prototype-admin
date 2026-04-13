class TemplateUsageLog < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :job_template, foreign_key: :template_id

  validates :template_id, presence: true
end
