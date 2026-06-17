class CreateCachedAvailabilities < ActiveRecord::Migration[7.1]
  def change
    create_table :cached_availabilities do |t|
      t.references :user, null: false, foreign_key: true
      t.date :date, null: false
      t.jsonb :slots_data, default: {}
      t.datetime :fetched_at, null: false

      t.timestamps
    end

    add_index :cached_availabilities, [ :user_id, :date ], unique: true
  end
end
