class AddAggregatedStatsToSourcings < ActiveRecord::Migration[7.1]
  def change
    add_column :sourcings, :aggregated_stats, :jsonb, default: {}
    add_index :sourcings, :aggregated_stats, using: :gin
  end
end
