class AddIntroductionDetailsInEvaluation < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluations, :introduction_details, :text, default: nil if not column_exists?(:evaluations, :introduction_details)
  end
end
