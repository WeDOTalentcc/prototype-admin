class AddNoReplyOnMessage < ActiveRecord::Migration[7.1]
  def change
    add_column :messages, :no_reply, :boolean, default: false
  end
end
