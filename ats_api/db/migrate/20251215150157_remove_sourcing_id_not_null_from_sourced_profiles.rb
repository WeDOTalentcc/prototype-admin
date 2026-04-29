class RemoveSourcingIdNotNullFromSourcedProfiles < ActiveRecord::Migration[7.1]
  def change
    change_column_null :sourced_profiles, :sourcing_id, true
  end
end
