class AddSavedToSourcings < ActiveRecord::Migration[7.1]
  def change
    add_column :sourcings, :saved, :boolean, default: false
  end
end
