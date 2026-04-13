# frozen_string_literal: true

class EmailLog < ApplicationRecord
  belongs_to :email_template, foreign_key: :template_id, optional: true

  has_many :email_tracking_events, dependent: :destroy
end
