class ChangeAccountIdOnInstitutions < ActiveRecord::Migration[7.1]
  def up
    remove_column :institutions, :account_id, :integer, array: true, default: []
    add_reference :institutions, :account, null: true
  end

  def down
    remove_reference :institutions, :account, foreign_key: true
    add_column :institutions, :account_id, :integer, array: true, default: []
    add_index :institutions, :account_id, using: :gin
  end
end
