class AddCvMatchInApply < ActiveRecord::Migration[7.1]
  def change
    if !column_exists?(:applies, :cv_match)
      add_column :applies, :cv_match, :float, default: 0.0, null: true
    end
  end
end
