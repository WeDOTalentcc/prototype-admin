class CreateSourcedProfileActivities < ActiveRecord::Migration[7.0]
  def change
    create_table :sourced_profile_activities do |t|
      t.references :sourced_profile, null: false, foreign_key: true
      t.references :user, null: false, foreign_key: true

      t.string :uid, null: false
      t.string :activity_type, null: false # viewed, rated, status_changed, note_added, imported, ai_analyzed
      t.jsonb :data, default: {}
      t.string :old_value
      t.string :new_value

      t.timestamps
    end

    add_index :sourced_profile_activities, :uid, unique: true
    add_index :sourced_profile_activities, :activity_type
    add_index :sourced_profile_activities, [ :sourced_profile_id, :created_at ], name: 'idx_sp_activities_on_profile_id_created_at'
  end
end
