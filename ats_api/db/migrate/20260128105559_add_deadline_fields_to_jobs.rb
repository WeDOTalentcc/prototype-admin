class AddDeadlineFieldsToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :screening_deadline, :date, null: true
    add_column :jobs, :shortlist_deadline, :date, null: true
    add_column :jobs, :closing_deadline, :date, null: true
  end
end
