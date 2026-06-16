class AddRawToCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :candidates, :data_raw, :jsonb
  end
end
