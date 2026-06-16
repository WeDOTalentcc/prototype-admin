class AddResponsibilitiesInJob < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :responsibilities, :string, array: true, default: [] unless column_exists?(:jobs, :responsibilities)
  end
end
