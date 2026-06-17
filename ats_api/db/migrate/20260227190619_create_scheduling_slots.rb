class CreateSchedulingSlots < ActiveRecord::Migration[7.1]
  def change
    create_table :scheduling_slots do |t|
      t.references :scheduling_link, null: false, foreign_key: true
      t.datetime :start_time, null: false
      t.datetime :end_time, null: false
      t.boolean :is_available, default: true

      t.timestamps
    end

    add_index :scheduling_slots, [ :scheduling_link_id, :is_available ]
    add_index :scheduling_slots, :start_time
  end
end
