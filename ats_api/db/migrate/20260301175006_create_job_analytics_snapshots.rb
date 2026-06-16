class CreateJobAnalyticsSnapshots < ActiveRecord::Migration[7.1]
  def change
    create_table :job_analytics_snapshots do |t|
      t.bigint :job_id, null: false
      t.jsonb :snapshot_data, null: false, default: {}
      t.datetime :computed_at, null: false
      t.integer :version, null: false, default: 1

      t.timestamps
    end

    add_index :job_analytics_snapshots, :job_id, unique: true
    add_index :job_analytics_snapshots, :computed_at
  end
end
