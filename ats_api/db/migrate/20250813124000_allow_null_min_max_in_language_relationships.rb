class AllowNullMinMaxInLanguageRelationships < ActiveRecord::Migration[7.1]
  def change
    return unless table_exists?(:language_relationships)

    # Permitir valores nulos em min_value e max_value
    change_column_null :language_relationships, :min_value, true if column_exists?(:language_relationships, :min_value)
    change_column_null :language_relationships, :max_value, true if column_exists?(:language_relationships, :max_value)
  end
end
