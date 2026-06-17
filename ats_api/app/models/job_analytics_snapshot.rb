# frozen_string_literal: true

class JobAnalyticsSnapshot < ApplicationRecord
  belongs_to :job

  validates :job_id, uniqueness: true
end
