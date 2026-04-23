class Institution < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  belongs_to :account, optional: true
  validates :name, presence: true
end
