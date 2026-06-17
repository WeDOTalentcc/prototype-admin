class AddSectorRelationship < ActiveRecord::Migration[7.1]
  def change
    create_table :sector_relationships do |t|
      t.references :sector, null: false, foreign_key: false
      t.string :sector_name, null: false
      t.string :reference_type, null: false
      t.bigint :reference_id, null: false
      t.boolean :is_deleted, default: false, null: false
      t.references :account, null: false, foreign_key: false
      t.timestamps
    end
  end
end
