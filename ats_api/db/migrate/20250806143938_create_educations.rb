# frozen_string_literal: true

class CreateEducations < ActiveRecord::Migration[7.1]
  def change
    create_table :educations do |t|
      t.boolean :study_here
      t.datetime :start_date
      t.datetime :end_date
      t.references :candidate, null: false
      t.references :institution, null: true
      t.references :study_area, null: true
      t.references :city, null: true
      t.references :account, null: true
      t.integer :formation_type, default: 8
      t.string :parse_language
      t.timestamps
    end
  end
end
