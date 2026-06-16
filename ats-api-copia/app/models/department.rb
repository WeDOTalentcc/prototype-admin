# frozen_string_literal: true

class Department < ApplicationRecord
  belongs_to :company_profile, foreign_key: :company_id
  belongs_to :parent, class_name: "Department", optional: true
  has_many :children, class_name: "Department", foreign_key: :parent_id, dependent: :destroy
  has_many :ideal_profiles, dependent: :destroy

  validates :company_id, :name, presence: true
end
