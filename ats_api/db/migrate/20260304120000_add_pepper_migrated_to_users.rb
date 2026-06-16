class AddPepperMigratedToUsers < ActiveRecord::Migration[7.1]
  def change
    add_column :users, :pepper_migrated, :boolean, default: false, null: false
  end
end
