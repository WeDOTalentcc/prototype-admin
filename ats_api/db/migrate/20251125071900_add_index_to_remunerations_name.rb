class AddIndexToRemunerationsName < ActiveRecord::Migration[7.1]
  def change
    add_index :remunerations, :name
  end
end
