class DropAiCosts < ActiveRecord::Migration[7.1]
  def up
    drop_table :ai_costs, if_exists: true
  end

  def down
    create_table :ai_costs do |t|
      t.references :user, null: false, foreign_key: false
      t.references :account, null: false, foreign_key: false
      t.references :message, null: true, foreign_key: false
      t.decimal :cost, precision: 10, scale: 5, null: false
      t.string :service, null: false
      t.text :prompt
      t.string :agent
      t.timestamps
    end
  end
end
