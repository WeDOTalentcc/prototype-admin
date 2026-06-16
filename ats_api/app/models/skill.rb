class Skill < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  belongs_to :account
  belongs_to :skill_category, optional: true

  validates :name, presence: true
  validates :account_id, presence: true

  validates :name, uniqueness: { scope: :account_id, message: "Skill name must be unique for the account" }

  def search_data
    {
      id: id,
      name: name,
      is_deleted: is_deleted,
      account_id: account_id,
      skill_category_id: skill_category_id,
      skill_category_name: skill_category&.name,
      created_at: created_at,
      updated_at: updated_at
    }
  end
end
