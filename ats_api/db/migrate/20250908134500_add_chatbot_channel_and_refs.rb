class AddChatbotChannelAndRefs < ActiveRecord::Migration[7.1]
  def change
    unless column_exists?(:evaluations, :chatbot_channel)
      add_column :evaluations, :chatbot_channel, :integer, null: false, default: 0
      add_index  :evaluations, :chatbot_channel
    end

    unless column_exists?(:messages, :evaluation_id)
      add_column :messages, :evaluation_id, :bigint
      add_index  :messages, :evaluation_id
    end

    unless column_exists?(:messages, :apply_id)
      add_column :messages, :apply_id, :bigint
      add_index  :messages, :apply_id
    end

    unless index_exists?(:messages, [ :reference_type, :reference_id, :evaluation_id ], name: 'idx_messages_reference_eval')
      add_index :messages, [ :reference_type, :reference_id, :evaluation_id ], name: 'idx_messages_reference_eval'
    end
  end
end
