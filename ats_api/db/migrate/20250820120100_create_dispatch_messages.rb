class CreateDispatchMessages < ActiveRecord::Migration[7.1]
  def change
    create_table :dispatch_messages do |t|
      t.references :account, null: false, foreign_key: true
      t.references :dispatch, null: false, foreign_key: true
      t.string :recipient_type, null: false
      t.bigint :recipient_id, null: false
      t.string :recipient_address, null: false
      t.integer :status, null: false, default: 0
      t.integer :attempts, null: false, default: 0
      t.datetime :sent_at
      t.jsonb :provider_response, default: {}
      t.timestamps
    end unless table_exists?(:dispatch_messages)

    add_index :dispatch_messages, [ :recipient_type, :recipient_id ], name: 'index_dispatch_messages_on_recipient' unless index_exists?(:dispatch_messages, [ :recipient_type, :recipient_id ], name: 'index_dispatch_messages_on_recipient')
  end
end
