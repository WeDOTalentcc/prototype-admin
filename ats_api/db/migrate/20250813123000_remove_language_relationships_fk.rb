class RemoveLanguageRelationshipsFk < ActiveRecord::Migration[7.1]
  def change
    if foreign_key_exists?(:language_relationships, :languages)
      remove_foreign_key :language_relationships, :languages
    end
  end
end
