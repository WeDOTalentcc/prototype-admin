class ApprovalRequest < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  validates :company_id, presence: true
end
