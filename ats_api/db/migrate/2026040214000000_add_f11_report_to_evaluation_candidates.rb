# frozen_string_literal: true

class AddF11ReportToEvaluationCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluation_candidates, :f11_report_json, :jsonb unless column_exists?(:evaluation_candidates, :f11_report_json)
    add_column :evaluation_candidates, :report_generated_at, :datetime unless column_exists?(:evaluation_candidates, :report_generated_at)
    add_column :evaluation_candidates, :report_version, :string unless column_exists?(:evaluation_candidates, :report_version)
    add_column :evaluation_candidates, :f11_report_stale, :boolean, default: true, null: false unless column_exists?(:evaluation_candidates, :f11_report_stale)
  end
end
