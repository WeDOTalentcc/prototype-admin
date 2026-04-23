class CreateAiCosts < ActiveRecord::Migration[7.1]
  def change
    create_table :ai_costs do |t|
      t.references :user, null: false, foreign_key: false
      t.references :account, null: false, foreign_key: false
      t.references :message, null: true, foreign_key: false
      t.decimal :cost, precision: 10, scale: 5, null: false
      t.string :service, null: false
      t.string :prompt, null: false
      t.string :agent, null: true
      t.timestamps
    end
  end
end
