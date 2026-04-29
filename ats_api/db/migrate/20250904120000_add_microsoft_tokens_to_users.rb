class AddMicrosoftTokensToUsers < ActiveRecord::Migration[7.1]
  def change
    add_column :users, :ms_access_token, :text
    add_column :users, :ms_refresh_token, :text
    add_column :users, :ms_expires_at, :datetime
  end
end
