class CreateOccupation < ActiveRecord::Migration[7.1]
  def change
    create_table :occupations do |t|
      t.string :name, null: false
      t.string :description
      t.boolean :is_deleted, default: false, null: false
      t.references :account, null: false
      t.references :user, null: true
      t.timestamps
    end
  end
end
