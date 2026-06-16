class AddAvailabilityToCandidates < ActiveRecord::Migration[7.1]
  def change
    add_column :candidates, :availability, :string
  end
end
