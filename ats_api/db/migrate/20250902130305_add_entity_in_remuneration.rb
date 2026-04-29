class AddEntityInRemuneration < ActiveRecord::Migration[7.1]
  def change
    add_column :remunerations, :entity, :string, default: 'Job', null: false if !column_exists?(:remunerations, :entity)
  end
end
