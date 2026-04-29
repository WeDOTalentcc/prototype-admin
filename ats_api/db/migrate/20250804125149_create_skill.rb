class CreateSkill < ActiveRecord::Migration[7.1]
  def change
    create_table :skills do |t|
      t.string :name, null: false
      t.boolean :is_deleted, default: false
      t.references :account, null: false
      t.timestamps
    end
  end
end
