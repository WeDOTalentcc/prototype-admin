# frozen_string_literal: true

class CreateStageScreeningQuestions < ActiveRecord::Migration[7.1]
  def change
    create_table :stage_screening_questions, id: :uuid do |t|
      t.references :recruitment_stage, type: :uuid, foreign_key: { on_delete: :cascade }
      t.string :company_id, null: false
      t.text :question, null: false
      t.string :question_type, limit: 30, default: "text"  # text, yes_no, scale, multiple_choice
      t.jsonb :options, default: []         # for multiple_choice
      t.string :expected_answer, limit: 500
      t.boolean :required, default: true
      t.boolean :eliminatory, default: false
      t.integer :order, default: 0
      t.boolean :is_active, default: true
      t.float :weight, default: 1.0
      t.string :competency, limit: 100      # technical, behavioral, logistical
      t.string :created_by
      t.timestamps
    end

    add_index :stage_screening_questions, :company_id
    add_index :stage_screening_questions, [:recruitment_stage_id, :order]
  end
end
