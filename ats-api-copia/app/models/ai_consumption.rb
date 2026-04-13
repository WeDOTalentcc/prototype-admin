# frozen_string_literal: true

class AiConsumption < ApplicationRecord
  self.table_name = "ai_consumption"

  validates :company_id, presence: true
end
