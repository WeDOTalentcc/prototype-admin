class Candidate < ApplicationRecord
  include Searchable

  # belongs_to :city, optional: true
  belongs_to :account

  has_many :candidate_experiences, dependent: :destroy
  has_many :candidate_education, dependent: :destroy
  has_many :candidate_attachments, dependent: :destroy
  has_many :interviews, dependent: :destroy
  has_many :talent_pool_candidates, dependent: :destroy
  has_many :talent_pools, through: :talent_pool_candidates

  validates :name, presence: true
  validates :email, presence: true, uniqueness: true
  validates :cpf, uniqueness: true, allow_blank: true
end
