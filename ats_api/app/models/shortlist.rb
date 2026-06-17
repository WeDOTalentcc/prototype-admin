# frozen_string_literal: true

class Shortlist < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  belongs_to :account
  belongs_to :user, optional: true

  validates :name, presence: true

  def search_data
    {
      id: id,
      name: name,
      description: description,
      is_deleted: is_deleted,
      account_id: account_id,
      user_id: user_id,
      created_at: created_at,
      updated_at: updated_at
    }
  end
end
