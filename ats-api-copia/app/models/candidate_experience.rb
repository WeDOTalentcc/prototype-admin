# frozen_string_literal: true

class CandidateExperience < ApplicationRecord
  belongs_to :candidate

  validates :company_name, presence: true
end
