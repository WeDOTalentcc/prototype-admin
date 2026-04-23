class CreateRemuneration < ActiveRecord::Migration[7.1]
  def change
    create_table :remunerations do |t|
      t.string :name, null: true
      t.string :description, null: true
      t.boolean :is_deleted, default: false, null: false
      t.string :entity, null: false, default: 'Job'
      t.references :account, null: false
      t.references :user, null: true
      t.timestamps
    end
  end
end
