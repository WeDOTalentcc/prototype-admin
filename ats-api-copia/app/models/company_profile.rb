# frozen_string_literal: true

class CompanyProfile < ApplicationRecord
  belongs_to :client_account

  has_many :departments, foreign_key: :company_id, dependent: :destroy
  has_many :benefits, foreign_key: :company_id, dependent: :destroy
  has_many :culture_values, foreign_key: :company_id, dependent: :destroy
  has_many :ideal_profiles, foreign_key: :company_id, dependent: :destroy
  has_many :compensation_policies, foreign_key: :company_id, dependent: :destroy

  validates :name, presence: true
end
