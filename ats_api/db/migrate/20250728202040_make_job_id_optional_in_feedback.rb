class MakeJobIdOptionalInFeedback < ActiveRecord::Migration[7.1]
  def change
    change_column_null :feedbacks, :job_id, true
    change_column_null :feedbacks, :selective_process_id, true
    # remove_foreign_key :feedbacks, :accounts
  end
end
