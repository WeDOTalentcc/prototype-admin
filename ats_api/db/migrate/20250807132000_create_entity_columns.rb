class CreateEntityColumns < ActiveRecord::Migration[7.1]
  def change
    create_table :entity_columns do |t|
      t.string :entity, null: false
      t.bigint :user_id, null: true
      t.bigint :account_id, null: false
      t.bigint :shortlist_id, null: true
      t.bigint :job_id, null: true
      t.string :label
      t.text :columns_view
      t.string :requested, null: false, default: 'default'
      t.boolean :is_main, default: false
      t.boolean :is_views, default: false
      t.boolean :is_public, default: false
      t.text :business_ids
      t.boolean :is_deleted, default: false

      t.timestamps
    end

    add_index :entity_columns, [ :entity, :user_id, :requested, :is_main ]
    add_index :entity_columns, [ :entity, :user_id, :shortlist_id, :job_id ]
    add_index :entity_columns, [ :is_public, :entity ]
    add_index :entity_columns, [ :account_id, :entity ]
    add_index :entity_columns, :is_deleted
    add_index :entity_columns, :shortlist_id
    add_index :entity_columns, :user_id
    add_index :entity_columns, :job_id
  end
end
