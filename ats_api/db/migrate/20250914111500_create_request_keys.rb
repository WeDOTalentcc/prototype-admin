class CreateRequestKeys < ActiveRecord::Migration[7.1]
  def change
    create_table :request_keys do |t|
      t.string :key, null: false
      t.datetime :expires_at, null: false

      t.timestamps
    end

    add_index :request_keys, :key, unique: true
    add_index :request_keys, :expires_at
  end
end
