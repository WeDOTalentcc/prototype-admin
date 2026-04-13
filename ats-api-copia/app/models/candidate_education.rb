# frozen_string_literal: true

class CandidateEducation < ApplicationRecord
  self.table_name = "candidate_education"

  belongs_to :candidate

  validates :institution, presence: true
end
