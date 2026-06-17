class CreateSchedulingLinks < ActiveRecord::Migration[7.1]
  def change
    create_table :scheduling_links do |t|
      t.references :account, null: false, foreign_key: true
      t.references :created_by, null: false, foreign_key: { to_table: :users }
      t.references :apply, null: true, foreign_key: true
      t.references :candidate, null: true
      t.references :job, null: true, foreign_key: true
      t.references :meeting, null: true, foreign_key: true
      t.references :calendar_event, null: true, foreign_key: true

      t.string :token, null: false
      t.string :status, default: "active"
      t.string :interview_type
      t.string :platform
      t.integer :duration_minutes, default: 60
      t.string :location
      t.string :subject
      t.text :message
      t.datetime :expires_at
      t.datetime :booked_at

      t.timestamps
    end

    add_index :scheduling_links, :token, unique: true
    add_index :scheduling_links, :status
    add_index :scheduling_links, [ :account_id, :status ]
  end
end
