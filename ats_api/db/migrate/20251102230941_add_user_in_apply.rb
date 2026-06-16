class AddUserInApply < ActiveRecord::Migration[7.1]
  def change
    add_reference :applies, :user, foreign_key: false, null: true unless column_exists?(:applies, :user_id)
  end
end
