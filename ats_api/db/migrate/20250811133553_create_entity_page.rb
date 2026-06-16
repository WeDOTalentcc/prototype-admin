class CreateEntityPage < ActiveRecord::Migration[7.1]
  def change
    create_table :entity_pages do |t|
      t.string "entity", null: false
      t.string "type_view", null: false
      t.jsonb "pages"
      t.string "link"
      t.string "custom_entity"
      t.references :account, null: false
      t.references :user, null: false
      t.timestamps
    end
  end
end
