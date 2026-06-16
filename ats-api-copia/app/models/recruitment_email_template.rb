# frozen_string_literal: true

class RecruitmentEmailTemplate < ApplicationRecord
  belongs_to :email_template, foreign_key: :template_id, optional: true

  validates :company_id, presence: true
end
