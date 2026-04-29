class AddDeletedAtToWhatsappConfigurations < ActiveRecord::Migration[7.1]
  def change
    add_column :whatsapp_configurations, :deleted_at, :datetime
    add_index :whatsapp_configurations, :deleted_at
  end
end
