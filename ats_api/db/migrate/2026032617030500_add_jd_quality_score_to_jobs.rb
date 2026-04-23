class AddJdQualityScoreToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :jd_quality_score, :jsonb, default: {} if !column_exists?(:jobs, :jd_quality_score)
  end
end
