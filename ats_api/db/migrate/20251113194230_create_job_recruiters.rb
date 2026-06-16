class CreateJobRecruiters < ActiveRecord::Migration[7.1]
  def change
    create_table :job_users do |t|
      t.bigint :user_id
      t.bigint :job_id
      t.bigint :account_id
      t.string :person_function, default: "", null: false
      t.float :split, default: 0.0

      t.timestamps
    end

    add_index :job_users, :user_id
    add_index :job_users, :job_id
    add_index :job_users, :account_id
  end
end
