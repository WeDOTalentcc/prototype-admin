class Country < ApplicationRecord
  include Searchable

  has_many :states, dependent: :destroy

  validates :name, presence: true, uniqueness: { case_sensitive: false }
end
