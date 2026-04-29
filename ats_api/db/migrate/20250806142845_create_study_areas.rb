class CreateStudyAreas < ActiveRecord::Migration[7.1]
  def change
    create_table :study_areas do |t|
      t.string :name
      t.boolean :approved, default: false
      t.string :reference_type
      t.integer :reference_id
      t.integer :account_id
      t.timestamps
    end

    add_index :study_areas, :account_id
  end
end
