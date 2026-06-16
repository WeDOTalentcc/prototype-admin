class AddressRelationship < ActiveRecord::Migration[7.1]
  def change
    create_table :address_relationships do |t|
      t.string :reference_type, null: false
      t.bigint :reference_id, null: false
      t.boolean :is_deleted, default: false
      t.references :address, null: false, foreign_key: true
      t.references :account, null: false
      t.references :user, null: true
      t.timestamps
    end
  end
end
