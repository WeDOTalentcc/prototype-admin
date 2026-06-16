class AddLevelToLanguageRelationships < ActiveRecord::Migration[7.1]
  def change
    return unless table_exists?(:language_relationships)
    add_column :language_relationships, :level, :string unless column_exists?(:language_relationships, :level)
    add_index  :language_relationships, :level unless index_exists?(:language_relationships, :level)
  end
end
