class Language < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  validates :name, presence: true, uniqueness: { case_sensitive: false }
  validates :acronym, presence: true, uniqueness: { case_sensitive: false }
  validates :name_ptbr, presence: true
end
