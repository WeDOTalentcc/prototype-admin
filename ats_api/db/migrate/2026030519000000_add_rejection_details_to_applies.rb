class AddRejectionDetailsToApplies < ActiveRecord::Migration[7.1]
  def change
    add_column :applies, :reason_code, :string unless column_exists?(:applies, :reason_code)
    add_column :applies, :reason_category, :string unless column_exists?(:applies, :reason_category)
    add_column :applies, :internal_comment, :text unless column_exists?(:applies, :internal_comment)
  end
end
