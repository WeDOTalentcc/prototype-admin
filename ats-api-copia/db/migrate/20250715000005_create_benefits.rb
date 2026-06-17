class CreateBenefits < ActiveRecord::Migration[7.1]
  def change
    create_table :benefits, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :company_id, null: false
      t.string :name, limit: 255, null: false
      t.text :description
      t.string :category, limit: 100
      t.string :icon, limit: 50
      t.float :value
      t.float :percentage_value
      t.string :value_type, limit: 50, default: "informative"
      t.text :value_details
      t.string :applicable_to, array: true, default: []
      t.string :seniority_levels, array: true, default: []
      t.string :contract_types, array: true, default: []
      t.jsonb :departments, default: {}
      t.integer :waiting_period_days
      t.boolean :is_mandatory, default: false
      t.boolean :is_active, default: true
      t.boolean :is_highlighted, default: false
      t.boolean :is_discount, default: false
      t.integer :order
      t.string :provider, limit: 255
      t.string :provider_contact, limit: 255
      t.timestamps
    end

    add_index :benefits, :company_id
    add_foreign_key :benefits, :company_profiles, column: :company_id
  end
end
