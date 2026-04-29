class ApplyStatus < ApplicationRecord
  include Searchable
  include TracksJobAnalytics

  enable_autocomplete :status_name

  validates :apply_id, presence: true
  validates :selective_process_id, presence: true
  validates :status_name, presence: true

  belongs_to :apply
  belongs_to :selective_process
  belongs_to :user, optional: true

  def search_data
    {
      **attributes.deep_symbolize_keys,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.include_base
    joins(:selective_process).joins(:apply).joins(:user).select(
      "apply_statuses.*, selective_processes.name AS selective_process_name, users.name AS user_name"
    )
  end
end
