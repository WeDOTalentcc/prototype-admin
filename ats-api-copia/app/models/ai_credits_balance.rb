# frozen_string_literal: true

class AiCreditsBalance < ApplicationRecord
  self.table_name = "ai_credits_balance"

  validates :company_id, presence: true
end
