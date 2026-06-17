class CreateOpinions < ActiveRecord::Migration[7.1]
  def change
    create_table :opinions do |t|
      t.string :uid
      t.text :content, null: false
      t.string :status, default: "active", null: false
      t.jsonb :metadata, default: {}
      t.boolean :is_deleted, default: false, null: false
      t.references :candidate, null: false, foreign_key: true
      t.references :job, foreign_key: true
      t.references :user, null: false, foreign_key: true
      t.references :account, null: false, foreign_key: true

      t.timestamps
    end

    add_index :opinions, :uid, unique: true
    add_index :opinions, [ :candidate_id, :job_id ]
    add_index :opinions, [ :account_id, :is_deleted ]
  end
end
