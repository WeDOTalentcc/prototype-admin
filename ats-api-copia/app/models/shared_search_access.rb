class SharedSearchAccess < ApplicationRecord
  self.table_name = "shared_search_access"

  # ApplicationRecord already includes AccountScopable

  belongs_to :shared_search

  validates :shared_search_id, presence: true
end
