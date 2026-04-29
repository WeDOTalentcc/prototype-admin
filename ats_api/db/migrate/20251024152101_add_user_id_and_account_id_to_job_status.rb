class AddUserIdAndAccountIdToJobStatus < ActiveRecord::Migration[7.1]
  def change
    add_reference :job_statuses, :user, foreign_key: false, null: true unless column_exists?(:job_statuses, :user_id)
    add_reference :job_statuses, :account, foreign_key: false, null: true unless column_exists?(:job_statuses, :account_id)
  end
end
