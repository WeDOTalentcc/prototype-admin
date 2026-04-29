# frozen_string_literal: true

class AddWsiF8InjectionAndG2Gate < ActiveRecord::Migration[7.1]
  def change
    add_column :answers, :injection_attempt_count, :integer, default: 0, null: false unless column_exists?(:answers, :injection_attempt_count)
    add_column :evaluation_candidates, :g2_gate_triggered, :boolean, default: false, null: false unless column_exists?(:evaluation_candidates, :g2_gate_triggered)

    change_column :answers, :final_skill_score, :decimal, precision: 5, scale: 2
  end
end
