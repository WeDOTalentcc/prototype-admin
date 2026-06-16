class AddAccountInOthersModels < ActiveRecord::Migration[7.1]
  def change
    add_reference :applies, :account, null: false, foreign_key: true
    add_reference :candidates, :account, null: false, foreign_key: true
    add_reference :selective_processes, :account, null: false, foreign_key: true
  end
end
