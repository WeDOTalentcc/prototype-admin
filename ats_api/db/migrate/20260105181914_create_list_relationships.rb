class CreateListRelationships < ActiveRecord::Migration[7.1]
  def change
    create_table :list_relationships do |t|
      t.references :reference, polymorphic: true, null: false, index: true
      t.references :list, foreign_key: true, null: false
      t.references :account, foreign_key: true, null: false

      t.integer :position, default: 0
      t.text :general_comments
      t.integer :score
      t.boolean :is_deleted, default: false

      t.timestamps
    end

    add_index :list_relationships, [ :reference_type, :reference_id, :list_id ],
              unique: true, name: 'index_list_rel_on_reference_and_list'
    add_index :list_relationships, :position
    add_index :list_relationships, :is_deleted
    add_index :list_relationships, [ :account_id, :is_deleted ]
    add_index :list_relationships, [ :list_id, :position ]
    add_index :list_relationships, [ :reference_type, :reference_id, :is_deleted ]
  end
end
