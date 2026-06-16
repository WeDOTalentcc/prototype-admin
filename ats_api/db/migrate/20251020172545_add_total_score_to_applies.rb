class AddTotalScoreToApplies < ActiveRecord::Migration[7.1]
  def change
    unless column_exists?(:applies, :total_score)
      add_column :applies, :total_score, :float, default: 0.0, null: true
    end
  end
end
