class AddWsiScoringContractFields < ActiveRecord::Migration[7.1]
  def change
    add_question_fields
    add_answer_fields
    add_evaluation_candidate_fields
  end

  private

  def add_question_fields
    return unless table_exists?(:questions)

    add_column :questions, :framework_weights, :jsonb, default: {}, null: false unless column_exists?(:questions, :framework_weights)
    add_column :questions, :validation_type_weight, :decimal, precision: 5, scale: 4 unless column_exists?(:questions, :validation_type_weight)
  end

  def add_answer_fields
    return unless table_exists?(:answers)

    add_column :answers, :analysis_data, :jsonb, default: {}, null: false unless column_exists?(:answers, :analysis_data)
    add_column :answers, :final_skill_score, :decimal, precision: 4, scale: 2 unless column_exists?(:answers, :final_skill_score)
  end

  def add_evaluation_candidate_fields
    return unless table_exists?(:evaluation_candidates)

    add_column :evaluation_candidates, :wsi_classification, :string unless column_exists?(:evaluation_candidates, :wsi_classification)
    add_column :evaluation_candidates, :wsi_level, :string unless column_exists?(:evaluation_candidates, :wsi_level)
    add_column :evaluation_candidates, :wsi_summary, :text unless column_exists?(:evaluation_candidates, :wsi_summary)
  end
end
