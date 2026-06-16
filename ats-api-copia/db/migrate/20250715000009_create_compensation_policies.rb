class CreateCompensationPolicies < ActiveRecord::Migration[7.1]
  def change
    create_table :compensation_policies, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :company_id, null: false
      t.string :name, limit: 255
      t.text :description
      t.string :policy_type, limit: 50
      t.string :currency, limit: 10, default: "BRL"
      t.jsonb :salary_bands, default: []
      t.jsonb :bonus_structure, default: {}
      t.jsonb :equity_rules, default: {}
      t.jsonb :benefits_package, default: {}
      t.jsonb :variable_compensation, default: {}
      t.string :applicable_departments, array: true, default: []
      t.string :applicable_seniority, array: true, default: []
      t.string :applicable_roles, array: true, default: []
      t.boolean :is_active, default: true
      t.boolean :is_default, default: false
      t.datetime :effective_from
      t.datetime :effective_until
      t.string :approved_by, limit: 255
      t.datetime :approved_at
      t.integer :version, default: 1
      t.jsonb :revision_history, default: []
      t.string :created_by, limit: 255
      t.timestamps
    end

    add_index :compensation_policies, :company_id
    add_foreign_key :compensation_policies, :company_profiles, column: :company_id
  end
end
