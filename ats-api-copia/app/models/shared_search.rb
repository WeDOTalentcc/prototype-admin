class SharedSearch < ApplicationRecord
  # ApplicationRecord already includes AccountScopable

  has_many :shared_search_accesses, dependent: :destroy
  has_many :shared_search_feedbacks, dependent: :destroy
end
