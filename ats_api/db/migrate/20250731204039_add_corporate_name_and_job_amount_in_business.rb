class AddCorporateNameAndJobAmountInBusiness < ActiveRecord::Migration[7.1]
  def change
    add_column :businesses, :corporate_name, :string, null: false, default: ''
    add_column :businesses, :job_amount, :integer, null: false, default: 0
  end
end
