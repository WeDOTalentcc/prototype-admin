class AddContactFieldsToSourcedProfiles < ActiveRecord::Migration[7.1]
  def change
    add_column :sourced_profiles, :emails, :jsonb
    add_column :sourced_profiles, :phones, :jsonb
  end
end
