class CreateActivityLogs < ActiveRecord::Migration[7.1]
  def change
    create_table :activity_logs do |t|
      t.string :reference_type, null: false
      t.bigint :reference_id, null: false
      t.string :action, null: false
      t.jsonb :changeset, default: {}
      t.references :user, foreign_key: false, null: true
      t.references :account, foreign_key: false, null: true
      t.string :ip_address
      t.bigint :rolled_back_from_id, index: true
      t.timestamps
    end

    add_index :activity_logs, %i[reference_type reference_id]
  end
end
