class CreateJobJourney < ActiveRecord::Migration[7.1]
  def change
    create_table :job_journeys do |t|
      t.string :name, null: false
      t.text :description
      t.integer :position, default: 0
      t.boolean :active, default: true
      t.boolean :required, default: true
      t.references :account, null: false, foreign_key: false
      t.references :job, null: true, foreign_key: false

      t.timestamps
    end
  end
end
