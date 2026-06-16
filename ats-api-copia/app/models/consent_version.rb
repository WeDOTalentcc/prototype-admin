# frozen_string_literal: true

class ConsentVersion < ApplicationRecord
  validates :consent_type, :version, presence: true
end
