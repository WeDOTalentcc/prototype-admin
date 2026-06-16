class ChangeUserIdToBeNullableInJobs < ActiveRecord::Migration[7.1]
  def change
    change_column_null :jobs, :user_id, true
  end
end
