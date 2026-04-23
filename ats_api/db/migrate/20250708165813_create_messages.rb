class CreateMessages < ActiveRecord::Migration[7.1]
  def change
    create_table :messages do |t|
      t.string :content
      t.integer :entity, null: false, default: 0
      t.boolean :is_deleted, default: false
      t.integer :status, null: false, default: 0
      t.bigint :parent_message_id
      t.references :reference, polymorphic: true, null: false
      t.references :account, null: true, foreign_key: true
      t.timestamps
    end
  end
end
