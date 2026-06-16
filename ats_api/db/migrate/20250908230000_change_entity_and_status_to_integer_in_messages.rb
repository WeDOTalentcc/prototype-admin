class ChangeEntityAndStatusToIntegerInMessages < ActiveRecord::Migration[7.1]
  def change
    # drop existing enum columns if they exist
    if column_exists?(:messages, :entity)
      remove_column :messages, :entity
    end
    if column_exists?(:messages, :status)
      remove_column :messages, :status
    end
    # add new integer columns with default values
    add_column :messages, :entity, :integer, default: 0, null: false
    add_column :messages, :status, :integer, default: 0, null: false
    # change_column :messages, :entity, :integer, default: 0, null: false
    # change_column :messages, :status, :integer, default: 0, null: false
  end
end
