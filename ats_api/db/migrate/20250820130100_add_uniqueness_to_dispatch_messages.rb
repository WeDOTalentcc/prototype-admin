class AddUniquenessToDispatchMessages < ActiveRecord::Migration[7.1]
  def change
    add_index :dispatch_messages, [ :dispatch_id, :recipient_type, :recipient_id ], unique: true, name: 'idx_dispatch_messages_uniq_dispatch_recipient' unless index_exists?(:dispatch_messages, [ :dispatch_id, :recipient_type, :recipient_id ], name: 'idx_dispatch_messages_uniq_dispatch_recipient')
  end
end
