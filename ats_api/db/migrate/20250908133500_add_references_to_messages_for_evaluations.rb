class AddReferencesToMessagesForEvaluations < ActiveRecord::Migration[7.1]
  def change
    unless column_exists?(:messages, :evaluation_id)
      add_column :messages, :evaluation_id, :bigint
      add_index  :messages, :evaluation_id
    end
    unless column_exists?(:messages, :apply_id)
      add_column :messages, :apply_id, :bigint
      add_index  :messages, :apply_id
    end
  end
end
