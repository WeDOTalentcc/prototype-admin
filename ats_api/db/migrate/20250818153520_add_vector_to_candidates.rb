class AddVectorToCandidates < ActiveRecord::Migration[7.1]
  def change
  # Use fully qualified type so it doesn't depend on search_path
  add_column :candidates, :embedding, 'extensions.vector', limit: 1536
  end
end
