class RevertSavedColumnLocation < ActiveRecord::Migration[7.1]
  def change
    remove_column :sourced_profile_sourcings, :saved, :boolean if column_exists?(:sourced_profile_sourcings, :saved)
    add_column :sourcings, :saved, :boolean, default: false unless column_exists?(:sourcings, :saved)
  end
end
