class AddAlertsInApply < ActiveRecord::Migration[7.1]
  def change
    add_column :applies, :alerts, :jsonb, default: []
  end
end
