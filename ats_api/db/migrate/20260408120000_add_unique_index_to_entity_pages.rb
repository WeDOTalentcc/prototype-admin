# frozen_string_literal: true

class AddUniqueIndexToEntityPages < ActiveRecord::Migration[7.1]
  def up
    execute <<~SQL
      CREATE UNIQUE INDEX idx_entity_pages_unique_per_user
        ON entity_pages (user_id, entity, type_view, COALESCE(link, ''), COALESCE(custom_entity, ''))
    SQL
  end

  def down
    remove_index :entity_pages, name: "idx_entity_pages_unique_per_user"
  end
end
