class CreateAddress < ActiveRecord::Migration[7.1]
  def change
    create_table :addresses do |t|
      t.string "street"
      t.string "number"
      t.string "neighborhood"
      t.string "zip_code"
      t.string "complement"
      t.string "title"
      t.string "address_type"
      t.text "description"
      t.boolean "is_deleted", default: false
      t.boolean "worksite", default: false
      t.boolean "bill_to", default: false
      t.boolean "sold_to", default: false
      t.references "state", foreign_key: false
      t.references "city", foreign_key: false
      t.references "country", foreign_key: false
      t.references "account", foreign_key: false
      t.references "user", foreign_key: false
      t.timestamps
    end
  end
end
