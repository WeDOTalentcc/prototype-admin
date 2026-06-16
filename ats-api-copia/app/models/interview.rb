# frozen_string_literal: true

class Interview < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  belongs_to :candidate
  belongs_to :job, foreign_key: :job_vacancy_id

  has_many :interview_feedbacks, dependent: :destroy
  has_many :interview_notes, dependent: :destroy
  has_many :interview_reminders, dependent: :destroy
  has_one :self_scheduling_link, dependent: :destroy
  has_many :reschedule_histories, dependent: :destroy
end
