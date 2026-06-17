class AddSignupEmailFieldsToAccounts < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists? 'accounts'
      add_column :accounts, :signup_email, :string unless column_exists?(:accounts, :signup_email)
      add_column :accounts, :signup_email_content, :text unless column_exists?(:accounts, :signup_email_content)
    end
  end
end
