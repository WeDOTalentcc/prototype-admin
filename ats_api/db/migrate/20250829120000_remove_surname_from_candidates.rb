class RemoveSurnameFromCandidates < ActiveRecord::Migration[7.1]
  def up
    if column_exists?(:candidates, :surname)
      remove_column :candidates, :surname, :string
    end
  end

  def down
    add_column :candidates, :surname, :string unless column_exists?(:candidates, :surname)
  end
end
