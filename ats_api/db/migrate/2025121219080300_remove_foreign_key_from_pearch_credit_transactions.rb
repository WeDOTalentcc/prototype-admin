class RemoveForeignKeyFromPearchCreditTransactions < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :pearch_credit_transactions, :accounts if foreign_key_exists?(:pearch_credit_transactions, :accounts)
    remove_foreign_key :pearch_search_logs, :accounts if foreign_key_exists?(:pearch_search_logs, :accounts)
    remove_foreign_key :pearch_search_logs, :users if foreign_key_exists?(:pearch_search_logs, :users)
  end
end
