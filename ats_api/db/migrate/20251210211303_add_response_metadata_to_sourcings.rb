class AddResponseMetadataToSourcings < ActiveRecord::Migration[7.1]
  def change
    add_column :sourcings, :response_metadata, :jsonb, default: {}, null: false
    add_index :sourcings, :response_metadata, using: :gin
  end
end
