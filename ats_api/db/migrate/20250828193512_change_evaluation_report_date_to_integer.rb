class ChangeEvaluationReportDateToInteger < ActiveRecord::Migration[7.1]
  def change
    remove_column :evaluations, :report_date if column_exists?(:evaluations, :report_date)
    add_column :evaluations, :report_date, :integer unless column_exists?(:evaluations, :report_date)

    remove_column :evaluations, :is_report_generated if column_exists?(:evaluations, :is_report_generated)
    add_column :evaluations, :report_generated_at, :datetime, default: nil unless column_exists?(:evaluations, :report_generated_at)
  end
end
