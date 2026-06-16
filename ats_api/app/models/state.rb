class State < ApplicationRecord
  include Searchable

  belongs_to :country
  has_many :cities
  validates :name, presence: true, uniqueness: { scope: :country_id, case_sensitive: false }
end
