class AddActionTypeToWhatsappConfigurations < ActiveRecord::Migration[7.1]
  def change
    add_column :whatsapp_configurations, :action_type, :string, default: 'webhook'
    add_column :whatsapp_configurations, :metadata, :jsonb, default: {}
    add_column :whatsapp_configurations, :priority, :integer, default: 0

    add_index :whatsapp_configurations, :action_type
    add_index :whatsapp_configurations, :metadata, using: 'gin'
    add_index :whatsapp_configurations, [ :environment, :action_type ]
  end
end
