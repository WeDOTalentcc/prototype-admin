class Occupation < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  belongs_to :account
  belongs_to :user, optional: true

  validates :name, presence: true, uniqueness: {
    scope: [ :account_id ],
    conditions: -> { where(is_deleted: false) },
    message: "Ocupação já existe"
  }
end
