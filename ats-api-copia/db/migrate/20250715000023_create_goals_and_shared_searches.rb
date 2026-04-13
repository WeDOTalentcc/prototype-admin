class CreateGoalsAndSharedSearches < ActiveRecord::Migration[7.1]
  def change
    create_table :goals, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :user_id, limit: 255
      t.uuid :company_id
      t.string :template_id, limit: 255
      t.string :name, limit: 255, null: false
      t.text :description
      t.float :target
      t.float :current, default: 0
      t.string :unit, limit: 100
      t.float :progress, default: 0
      t.string :period, limit: 50
      t.string :category, limit: 50
      t.string :status, limit: 50, default: "pending"
      t.datetime :start_date
      t.datetime :end_date
      t.boolean :is_custom, default: true
      t.boolean :is_active, default: true
      t.jsonb :goal_metadata, default: {}
      t.timestamps
    end

    add_index :goals, :user_id
    add_index :goals, :company_id

    create_table :goal_templates, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.string :name, limit: 255, null: false
      t.text :description
      t.string :category, limit: 50
      t.float :default_target
      t.string :unit, limit: 100
      t.string :period, limit: 50
      t.boolean :is_active, default: true
      t.timestamps
    end

    create_table :shared_searches, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :company_id
      t.uuid :created_by_user_id
      t.string :share_type, limit: 50
      t.text :source_query
      t.uuid :source_list_id
      t.string :title, limit: 255
      t.text :description
      t.jsonb :snapshot_payload, default: {}
      t.datetime :expires_at
      t.string :status, limit: 50, default: "active"
      t.boolean :can_comment, default: true
      t.boolean :can_rate, default: true
      t.timestamps
    end

    add_index :shared_searches, :company_id
    add_index :shared_searches, :created_by_user_id
    add_index :shared_searches, :status
    add_index :shared_searches, :expires_at

    create_table :shared_search_access, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :shared_search_id, null: false
      t.string :recipient_email, limit: 255
      t.string :access_token, limit: 255
      t.datetime :expires_at
      t.timestamps
    end

    add_index :shared_search_access, :shared_search_id
    add_index :shared_search_access, :access_token, unique: true
    add_index :shared_search_access, :recipient_email
    add_foreign_key :shared_search_access, :shared_searches

    create_table :shared_search_feedback, id: :uuid, default: -> { "gen_random_uuid()" } do |t|
      t.uuid :shared_search_id, null: false
      t.string :candidate_id, limit: 255
      t.string :given_by_email, limit: 255
      t.string :decision, limit: 50
      t.integer :rating
      t.text :comment
      t.timestamps
    end

    add_index :shared_search_feedback, :shared_search_id
    add_index :shared_search_feedback, :candidate_id
    add_foreign_key :shared_search_feedback, :shared_searches
  end
end
