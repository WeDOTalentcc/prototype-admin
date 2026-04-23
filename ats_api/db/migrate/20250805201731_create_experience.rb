class CreateExperience < ActiveRecord::Migration[7.1]
  def change
    create_table :experiences do |t|
      t.boolean "work_here", default: false
      t.datetime "start_date", precision: nil
      t.datetime "end_date", precision: nil
      t.string "reference_type", null: false
      t.bigint "reference_id", null: false
      t.bigint "occupation_id", null: false
      t.bigint "company_id", null: false
      t.bigint "city_id"
      t.text "description"
      t.text "reasons_leaving"
      t.string "contract_type"
      t.string "parse_language"
      t.boolean "is_deleted", default: false
      t.references :account, null: false
      t.references :user, null: true
      t.timestamps
    end
  end
end
