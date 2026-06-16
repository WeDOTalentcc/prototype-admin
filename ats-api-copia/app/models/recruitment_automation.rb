# frozen_string_literal: true

class RecruitmentAutomation < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  validates :company_id, presence: true
end
