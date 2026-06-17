class AddProgressFieldsToSourcings < ActiveRecord::Migration[7.1]
  def change
    add_column :sourcings, :local_results_count, :integer, default: 0 unless column_exists?(:sourcings, :local_results_count)
    add_column :sourcings, :global_results_count, :integer, default: 0 unless column_exists?(:sourcings, :global_results_count)
    add_column :sourcings, :processed_count, :integer, default: 0 unless column_exists?(:sourcings, :processed_count)
  end
end
