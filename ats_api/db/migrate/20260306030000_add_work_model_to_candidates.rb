class AddWorkModelToCandidates < ActiveRecord::Migration[7.0]
  def change
    add_column :candidates, :work_model, :string
  end
end
