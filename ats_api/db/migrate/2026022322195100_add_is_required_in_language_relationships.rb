class AddIsRequiredInLanguageRelationships < ActiveRecord::Migration[7.1]
  def change
    add_column :language_relationships, :is_required, :boolean, default: false unless column_exists?(:language_relationships, :is_required)
  end
end
