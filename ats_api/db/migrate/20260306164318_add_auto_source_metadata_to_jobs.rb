class AddAutoSourceMetadataToJobs < ActiveRecord::Migration[7.1]
  def change
    add_column :jobs, :auto_source_metadata, :jsonb, default: {}, null: false
    add_index :jobs, :auto_source_metadata, using: :gin
  end
end
