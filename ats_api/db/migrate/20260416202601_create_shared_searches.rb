class CreateSharedSearches < ActiveRecord::Migration[7.1]
  def change
    create_table :shared_searches do |t|
      t.string :uid
      t.string :title, null: false
      t.text :description
      t.text :query
      t.string :token, null: false
      t.jsonb :candidate_ids, default: []
      t.jsonb :shared_with_emails, default: []
      t.integer :viewed_count, default: 0, null: false
      t.datetime :expires_at
      t.boolean :is_deleted, default: false, null: false
      t.references :user, null: false, foreign_key: true
      t.references :account, null: false, foreign_key: true

      t.timestamps
    end

    add_index :shared_searches, :uid, unique: true
    add_index :shared_searches, :token, unique: true
    add_index :shared_searches, :candidate_ids, using: :gin
    add_index :shared_searches, :is_deleted
  end
end
