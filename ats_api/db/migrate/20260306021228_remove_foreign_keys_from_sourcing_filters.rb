class RemoveForeignKeysFromSourcingFilters < ActiveRecord::Migration[7.1]
  def change
    remove_foreign_key :sourcing_filters, :accounts, if_exists: true
    remove_foreign_key :sourcing_filters, :users, if_exists: true
  end
end
