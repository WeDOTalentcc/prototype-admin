# frozen_string_literal: true

class EmailTemplate < ApplicationRecord
  has_many :email_logs, foreign_key: :template_id, dependent: :destroy
  has_many :recruitment_email_templates, foreign_key: :template_id, dependent: :destroy

  validates :name, :subject, presence: true
end
