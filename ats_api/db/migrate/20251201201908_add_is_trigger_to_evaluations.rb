class AddIsTriggerToEvaluations < ActiveRecord::Migration[7.1]
  def change
    add_column :evaluations, :is_trigger, :boolean, default: false, null: false
  end
end
