class AddAlertsToAppliesIfNotExists < ActiveRecord::Migration[7.1]
  def up
    unless column_exists?(:applies, :alerts)
      add_column :applies, :alerts, :jsonb, default: []
    end
  end

  def down
    if column_exists?(:applies, :alerts)
      remove_column :applies, :alerts
    end
  end
end
