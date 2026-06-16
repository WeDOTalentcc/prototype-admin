# frozen_string_literal: true

class AddIndexesToCandidates < ActiveRecord::Migration[7.1]
  disable_ddl_transaction!

  def change
    # Add partial index for candidates with data_raw populated
    # Speeds up queries filtering by data_raw presence
    add_index :candidates, :account_id,
              where: "data_raw IS NOT NULL",
              algorithm: :concurrently,
              name: :index_candidates_on_account_id_where_data_raw_present,
              if_not_exists: true

    # Add partial index for candidates with linkedin null
    # Speeds up queries looking for candidates needing linkedin update
    add_index :candidates, :account_id,
              where: "linkedin IS NULL",
              algorithm: :concurrently,
              name: :index_candidates_on_account_id_where_linkedin_null,
              if_not_exists: true

    # Add index to count experiences by candidate
    # Speeds up LEFT JOIN queries checking for candidates without experiences
    add_index :experiences, :candidate_id,
              algorithm: :concurrently,
              if_not_exists: true

    # Add index to count educations by candidate
    # Speeds up LEFT JOIN queries checking for candidates without educations
    add_index :educations, :candidate_id,
              algorithm: :concurrently,
              if_not_exists: true
  end
end
