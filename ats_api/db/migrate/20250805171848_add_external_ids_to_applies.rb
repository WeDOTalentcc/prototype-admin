class AddExternalIdsToApplies < ActiveRecord::Migration[7.1]
  def change
    add_column :applies, :external_job_id, :string
    add_column :applies, :external_candidate_id, :string

    add_index :applies, :external_job_id
    add_index :applies, :external_candidate_id

    add_column :jobs, :external_id, :string
    add_index :jobs, :external_id
  end
end
