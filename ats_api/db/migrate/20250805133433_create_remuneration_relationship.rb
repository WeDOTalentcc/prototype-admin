class CreateRemunerationRelationship < ActiveRecord::Migration[7.1]
  def change
    create_table :remuneration_relationships do |t|
      t.string "currency", null: true
      t.integer "period", null: true
      t.text "comments", null: true
      t.decimal "value", precision: 8, scale: 2, null: true
      t.integer "amount", null: true
      t.string "contract_type", default: [], array: true, null: true
      t.string "reference_type", null: false
      t.bigint "reference_id", null: false
      t.boolean "is_deleted", default: false, null: false
      t.references :account, null: false
      t.references :user, null: true
      t.references :remuneration, null: false, foreign_key: true
      t.timestamps
    end
  end
end
