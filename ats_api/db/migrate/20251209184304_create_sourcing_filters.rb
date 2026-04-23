class CreateSourcingFilters < ActiveRecord::Migration[7.0]
  def change
    create_table :sourcing_filters do |t|
      t.references :account, null: false, foreign_key: true
      t.references :user, null: false, foreign_key: true

      t.string :uid, null: false
      t.string :name, null: false
      t.text :description

      # Filtros salvos
      t.string :query
      t.jsonb :parameters, default: {}

      # Uso
      t.integer :usage_count, default: 0
      t.datetime :last_used_at
      t.boolean :is_deleted, default: false

      t.timestamps
    end

    add_index :sourcing_filters, :uid, unique: true
    add_index :sourcing_filters, [ :account_id, :name ]
    add_index :sourcing_filters, [ :account_id, :is_deleted ]
  end
end
