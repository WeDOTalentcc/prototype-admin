class CreateApplies < ActiveRecord::Migration[7.1]
  def change
    create_table :applies do |t|
      t.references :candidate, null: false, foreign_key: true
      t.references :job, null: false, foreign_key: true
      t.references :selective_process, null: false, foreign_key: true
      t.boolean :is_deleted, default: false, null: false
      t.timestamps
    end
  end
end
