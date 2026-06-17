class CreateOrganizationalStructure < ActiveRecord::Migration[7.1]
  def change
    create_table :departments do |t|
      t.string :name, null: false
      t.text :description
      t.references :parent_department, foreign_key: { to_table: :departments }
      t.references :manager, foreign_key: { to_table: :users }
      t.integer :level, default: 0, null: false
      t.boolean :is_deleted, default: false, null: false
      t.references :account, null: false, foreign_key: true
      t.timestamps
      t.index [ :account_id, :name ]
      t.index :level
    end

    create_table :organizational_positions do |t|
      t.string :title, null: false
      t.text :description
      t.references :department, null: false, foreign_key: true
      t.references :reports_to, foreign_key: { to_table: :organizational_positions }
      t.integer :level, default: 0, null: false
      t.string :position_type
      t.boolean :is_active, default: true, null: false
      t.references :account, null: false, foreign_key: true
      t.timestamps
      t.index [ :account_id, :title ]
      t.index :level
    end

    create_table :position_assignments do |t|
      t.references :user, null: false, foreign_key: true
      t.references :organizational_position, null: false, foreign_key: true
      t.date :start_date, null: false
      t.date :end_date
      t.boolean :is_current, default: true, null: false
      t.string :employment_type
      t.references :account, null: false, foreign_key: true
      t.timestamps
      t.index [ :user_id, :is_current ]
      t.index [ :organizational_position_id, :is_current ]
    end

    create_table :teams do |t|
      t.string :name, null: false
      t.text :description
      t.references :department, foreign_key: true
      t.references :team_lead, foreign_key: { to_table: :users }
      t.integer :member_count, default: 0, null: false
      t.boolean :is_active, default: true, null: false
      t.references :account, null: false, foreign_key: true
      t.timestamps
      t.index [ :account_id, :name ]
    end

    create_table :team_members do |t|
      t.references :team, null: false, foreign_key: true
      t.references :user, null: false, foreign_key: true
      t.string :role
      t.date :joined_at
      t.date :left_at
      t.boolean :is_active, default: true, null: false
      t.references :account, null: false, foreign_key: true
      t.timestamps
      t.index [ :team_id, :user_id, :is_active ], unique: true
    end

    change_table :jobs, bulk: true do |t|
      t.references :department, foreign_key: true
      t.references :team, foreign_key: true
      t.references :reports_to_position, foreign_key: { to_table: :organizational_positions }
      t.references :hiring_manager, foreign_key: { to_table: :users }
      t.jsonb :team_composition, default: [], null: false
    end

    add_index :jobs, [ :department_id, :is_deleted ]
    add_index :jobs, [ :team_id, :is_deleted ]
  end
end
