class AddExternalProviderToApplies < ActiveRecord::Migration[7.1]
  def change
    add_column :applies, :external_provider, :string
  end
end
