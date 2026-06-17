class AddContentFormatToMessages < ActiveRecord::Migration[7.1]
  def change
    add_column :messages, :content_format, :string, null: false, default: "plain_text"
  end
end
