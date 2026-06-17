class AddJourneyFieldsInJob < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :seniority, :integer, null: true
    add_column :jobs, :employment_type, :integer, null: true
  end
end
