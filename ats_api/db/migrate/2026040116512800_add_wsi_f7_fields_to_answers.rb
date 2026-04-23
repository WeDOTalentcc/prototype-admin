class AddWsiF7FieldsToAnswers < ActiveRecord::Migration[7.1]
  def change
    add_column :answers, :self_declaration_score, :integer unless column_exists?(:answers, :self_declaration_score)
    add_column :answers, :eligibility_answer, :boolean unless column_exists?(:answers, :eligibility_answer)
  end
end
