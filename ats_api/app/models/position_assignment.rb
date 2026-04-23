class PositionAssignment < ApplicationRecord
  include Searchable

  belongs_to :user
  belongs_to :organizational_position
  belongs_to :account

  scope :current, -> { where(is_current: true) }

  validates :start_date, presence: true

  def self.include_base
    includes(:user, :organizational_position)
  end

  def search_data
    {
      user_id: user_id,
      user_name: user&.name,
      organizational_position_id: organizational_position_id,
      organizational_position_title: organizational_position&.title,
      employment_type: employment_type,
      is_current: is_current,
      start_date: start_date,
      end_date: end_date,
      account_id: account_id
    }
  end

  def self.search_fields
    [ :employment_type, :user_name, :organizational_position_title ]
  end

  def self.agg_search_array(_params = {})
    {
      user_id: { field: "user_id", limit: 20 },
      organizational_position_id: { field: "organizational_position_id", limit: 20 },
      employment_type: { field: "employment_type", limit: 10 },
      is_current: { field: "is_current", limit: 2 }
    }
  end

  def self.default_search_order
    { start_date: :desc }
  end
end
