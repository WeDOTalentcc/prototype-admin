class AddWsiFieldsInQuestion < ActiveRecord::Migration[7.1]
  def change
    add_column :questions, :competence_type, :string if !column_exists?(:questions, :competence_type)
    add_column :questions, :bloom_level, :string if !column_exists?(:questions, :bloom_level)
    add_column :questions, :dreyfus_target, :integer if !column_exists?(:questions, :dreyfus_target)
    add_column :questions, :ocean_trait, :string if !column_exists?(:questions, :ocean_trait)
  end
end
