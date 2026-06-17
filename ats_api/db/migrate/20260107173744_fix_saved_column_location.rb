class FixSavedColumnLocation < ActiveRecord::Migration[7.1]
  def change
    remove_column :sourcings, :saved, :boolean if column_exists?(:sourcings, :saved)
    add_column :sourced_profile_sourcings, :saved, :boolean, default: false unless column_exists?(:sourced_profile_sourcings, :saved)
  end
end
