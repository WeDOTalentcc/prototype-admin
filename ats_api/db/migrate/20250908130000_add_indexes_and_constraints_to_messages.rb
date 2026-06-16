class AddIndexesAndConstraintsToMessages < ActiveRecord::Migration[7.1]
  disable_ddl_transaction!

  def up
    # Add a GIN index for metadata querying if not present
    unless index_exists?(:messages, :metadata, using: :gin)
      execute 'CREATE INDEX CONCURRENTLY index_messages_on_metadata ON messages USING gin ((metadata));'
    end

    # Composite index to speed conversation queries
    unless index_exists?(:messages, [ :reference_type, :reference_id, :created_at ], name: 'index_messages_on_reference_created_at')
      add_index :messages, [ :reference_type, :reference_id, :created_at ], name: 'index_messages_on_reference_created_at', algorithm: :concurrently
    end

    # Foreign key for parent_message (self reference) - validate separately to avoid locking
    unless foreign_key_exists?(:messages, :messages, column: :parent_message_id)
      add_foreign_key :messages, :messages, column: :parent_message_id, validate: false
      validate_foreign_key :messages, :messages
    end
  end

  def down
    if foreign_key_exists?(:messages, :messages, column: :parent_message_id)
      remove_foreign_key :messages, column: :parent_message_id
    end

    if index_exists?(:messages, name: 'index_messages_on_reference_created_at')
      remove_index :messages, name: 'index_messages_on_reference_created_at'
    end

    if index_exists?(:messages, :metadata, using: :gin)
      execute 'DROP INDEX CONCURRENTLY IF EXISTS index_messages_on_metadata'
    end
  end
end
