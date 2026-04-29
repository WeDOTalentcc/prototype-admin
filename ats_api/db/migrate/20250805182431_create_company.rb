class CreateCompany < ActiveRecord::Migration[7.1]
  def change
    create_table :companies do |t|
      t.string "name", null: false
      t.boolean "is_deleted", default: false
      t.string "linkedin_url"
      t.references :account, null: false
      t.references :user, null: true
      t.timestamps
    end
  end
end
