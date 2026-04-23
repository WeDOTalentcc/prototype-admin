class AddParsedRequirementsToSourcings < ActiveRecord::Migration[7.1]
  def change
    add_column :sourcings, :parsed_requirements, :jsonb, default: {}, null: false
    add_index :sourcings, :parsed_requirements, using: :gin
  end
end
