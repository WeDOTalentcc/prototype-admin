class CreateCultureValues < ActiveRecord::Migration[7.1]
  def change
    create_table :culture_values, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :company_id, null: false
      t.string :name, limit: 255, null: false
      t.text :description
      t.string :category, limit: 100, default: "value"
      t.string :icon, limit: 50
      t.string :color, limit: 20
      t.string :behavioral_indicators, array: true, default: []
      t.string :interview_questions, array: true, default: []
      t.float :weight, default: 1.0
      t.boolean :is_active, default: true
      t.integer :order
      t.boolean :ai_generated, default: false
      t.string :source, limit: 100
      t.timestamps
    end

    add_index :culture_values, :company_id
    add_foreign_key :culture_values, :company_profiles, column: :company_id
  end
end
