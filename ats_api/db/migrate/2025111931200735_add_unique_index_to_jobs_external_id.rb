class AddUniqueIndexToJobsExternalId < ActiveRecord::Migration[7.1]
  def change
    remove_index :jobs, :external_id, if_exists: true

    add_index :jobs, [ :external_id, :account_id ],
              unique: true,
              where: "external_id IS NOT NULL",
              name: "index_jobs_on_external_id_and_account_id_unique"
  end
end
