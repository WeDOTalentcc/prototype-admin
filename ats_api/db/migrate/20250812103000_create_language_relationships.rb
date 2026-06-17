class CreateLanguageRelationships < ActiveRecord::Migration[7.1]
  def change
    create_table :language_relationships do |t|
      # Usamos apenas a coluna language_id (sem FK) porque languages ficará no schema público
      # e as tabelas tenant não podem ter FK cross-schema em alguns setups.
      t.bigint :language_id, null: false
      t.string :reference_type, null: false
      t.bigint :reference_id, null: false
      t.integer :min_value, null: false
      t.integer :max_value, null: false
      t.integer :priority, null: false, default: 0
      t.timestamps
    end unless table_exists?(:language_relationships)

    add_index :language_relationships, [ :reference_type, :reference_id ], name: 'index_language_relationships_on_reference'
    add_index :language_relationships, :language_id unless index_exists?(:language_relationships, :language_id)
  end
end
