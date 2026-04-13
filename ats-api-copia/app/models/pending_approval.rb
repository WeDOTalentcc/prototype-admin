class PendingApproval < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :approval_request, optional: true

  validates :company_id, presence: true
  validates :approver_id, presence: true
end
