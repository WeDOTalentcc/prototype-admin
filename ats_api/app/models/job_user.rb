class JobUser < ApplicationRecord
  include Searchable

  self.table_name = "job_users"

  belongs_to :user, optional: true
  belongs_to :job, optional: true
  belongs_to :account, optional: true

  validates :user_id, presence: true
  validates :job_id, presence: true
  validates :split, numericality: { greater_than_or_equal_to: 0, less_than_or_equal_to: 100 }

  def self.include_base
    select(<<~SQL)
      job_users.id,
      job_users.user_id,
      job_users.job_id,
      job_users.account_id,
      job_users.person_function,
      job_users.split,
      job_users.created_at,
      job_users.updated_at,
      users.name AS user_name,
      users.email AS user_email,
      jobs.title AS job_title
    SQL
    .joins("LEFT JOIN users ON users.id = job_users.user_id")
    .joins("LEFT JOIN jobs ON jobs.id = job_users.job_id")
  end

  def search_data
    {
      id: id,
      user_id: user_id,
      job_id: job_id,
      person_function: person_function&.downcase,
      split: split,
      user_name: user&.name&.downcase,
      user_email: user&.email&.downcase,
      job_title: job&.title&.downcase,
      account_id: account_id,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.agg_search_array(_params = {})
    {
      user_id: { field: "user_id", limit: 20 },
      user_name: { field: "user_name", limit: 20 },
      job_id: { field: "job_id", limit: 20 },
      job_title: { field: "job_title", limit: 20 },
      person_function: { field: "person_function", limit: 15 }
    }
  end
end
