class CreateSearchArchetypes < ActiveRecord::Migration[7.1]
  def change
    create_table :search_archetypes do |t|
      t.references :account, null: false, foreign_key: true
      t.references :user, foreign_key: true

      t.string :uid, null: false, index: { unique: true }
      t.string :name, null: false
      t.string :emoji, default: '🎯'
      t.text :description

      t.text :query

      t.integer :seniority
      t.integer :min_experience_years
      t.string :industry
      t.string :location
      t.integer :work_model, default: 0
      t.integer :contract_type, default: 0

      t.string :languages, default: [], array: true
      t.string :skills, default: [], array: true
      t.string :tags, default: [], array: true

      t.jsonb :local_filters, default: {}
      t.jsonb :global_filters, default: {}

      t.boolean :is_default, default: false
      t.boolean :is_public, default: false
      t.integer :usage_count, default: 0
      t.datetime :last_used_at
      t.boolean :is_deleted, default: false

      t.timestamps
    end

    add_index :search_archetypes, [ :account_id, :is_deleted ]
    add_index :search_archetypes, [ :account_id, :is_public ], where: "is_public = true"
    add_index :search_archetypes, :skills, using: :gin
    add_index :search_archetypes, :tags, using: :gin
  end
end
