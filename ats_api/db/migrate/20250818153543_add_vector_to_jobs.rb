class AddVectorToJobs < ActiveRecord::Migration[7.1]
  def change
  add_column :jobs, :embedding, 'extensions.vector', limit: 1536
  end
end
