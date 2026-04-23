class CreateSchedulingSettings < ActiveRecord::Migration[7.1]
  def change
    create_table :scheduling_settings do |t|
      t.references :user, null: false, foreign_key: true
      t.references :account, null: false, foreign_key: true
      t.string :timezone, default: "America/Sao_Paulo"
      t.time :work_hours_start, default: "09:00"
      t.time :work_hours_end, default: "18:00"
      t.integer :default_duration_minutes, default: 60
      t.integer :buffer_minutes, default: 15
      t.integer :lookahead_days, default: 14

      t.timestamps
    end

    add_index :scheduling_settings, :user_id, unique: true
  end
end
