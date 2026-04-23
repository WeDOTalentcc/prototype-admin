class AddCategoryInActivityLog < ActiveRecord::Migration[7.1]
  def change
    unless column_exists?(:activity_logs, :category)
      add_column :activity_logs, :category, :string, null: false, default: 'others'
    end
  end
end
