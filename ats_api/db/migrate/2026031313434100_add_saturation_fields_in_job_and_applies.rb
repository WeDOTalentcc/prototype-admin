class AddSaturationFieldsInJobAndApplies < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :web_saturation_amount, :integer, default: 0 unless column_exists?(:jobs, :web_saturation_amount)
    add_column :jobs, :sourcing_saturation_amount, :integer, default: 0 unless column_exists?(:jobs, :sourcing_saturation_amount)
    add_column :jobs, :saturation_amount_increase, :integer, default: 0 unless column_exists?(:jobs, :saturation_amount_increase)
    add_column :jobs, :saturation_release_hours, :integer, default: 0 unless column_exists?(:jobs, :saturation_release_hours)

    add_column :applies, :is_screening_sent, :boolean, default: false unless column_exists?(:applies, :is_screening_sent)
    add_column :applies, :source, :string, default: "sourcing" unless column_exists?(:applies, :source)

    add_column :accounts, :web_saturation_amount, :integer, default: 0 unless column_exists?(:accounts, :web_saturation_amount)
    add_column :accounts, :sourcing_saturation_amount, :integer, default: 0 unless column_exists?(:accounts, :sourcing_saturation_amount)
    add_column :accounts, :saturation_amount_increase, :integer, default: 0 unless column_exists?(:accounts, :saturation_amount_increase)
    add_column :accounts, :saturation_release_hours, :integer, default: 0 unless column_exists?(:accounts, :saturation_release_hours)
  end
end
