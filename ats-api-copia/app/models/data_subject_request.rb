# frozen_string_literal: true

class DataSubjectRequest < ApplicationRecord
  validates :candidate_id, :request_type, presence: true
end
