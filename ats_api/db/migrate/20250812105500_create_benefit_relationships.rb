class CreateBenefitRelationships < ActiveRecord::Migration[7.1]
  def change
    create_table :benefit_relationships do |t|
      t.references :benefit, foreign_key: true
      t.string :name, null: false
      t.string :reference_type, null: false
      t.bigint :reference_id, null: false
      t.boolean :is_deleted, default: false
      t.boolean :is_possible_extend_to_dependents, default: false, null: false
      t.boolean :is_per_day, default: false, null: false
      t.integer :days_of_month, default: 0, null: false
      t.boolean :enable_value_editing, default: true, null: false
      t.string :types, array: true, default: []
      t.string :type_description
      t.string :description
      t.boolean :is_company, default: false
      t.text :details
      t.boolean :is_extendable_to_dependents, default: false
      t.integer :dependents_count, default: 0
      t.timestamps
    end unless table_exists?(:benefit_relationships)

    add_index :benefit_relationships, [ :reference_type, :reference_id ], name: 'index_benefit_relationships_on_reference'
    add_index :benefit_relationships, :types, using: :gin unless index_exists?(:benefit_relationships, :types)
  end
end
