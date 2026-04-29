# frozen_string_literal: true

class Report < ApplicationRecord
  include Searchable

  belongs_to :account
  belongs_to :user, optional: true

  validates :name, presence: true

  scope :main_reports, -> { where(is_main: true) }
  scope :active, -> { where(is_deleted: false) }

  def search_data
    {
      id: id,
      name: name,
      description: description,
      is_main: is_main,
      is_deleted: is_deleted,
      account_id: account_id,
      user_id: user_id,
      created_at: created_at,
      updated_at: updated_at
    }
  end
end
