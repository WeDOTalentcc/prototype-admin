class CreateSelectiveProcesses < ActiveRecord::Migration[7.1]
  def change
    create_table :selective_processes do |t|
      t.string :name
      t.integer :position
      t.integer :status
      t.references :job, null: true, foreign_key: true, type: :bigint
      t.string :uid
      t.jsonb :sub_status, default: []
      t.integer :childrens, array: true, default: []
      t.integer :position_x, null: true
      t.integer :position_y, null: true

      t.timestamps
    end

    add_index :selective_processes, :uid
  end
end
