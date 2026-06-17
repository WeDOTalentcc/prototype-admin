class CreateWhatsappConfigurations < ActiveRecord::Migration[7.1]
  def change
    create_table :whatsapp_configurations do |t|
      t.string :environment, null: false # 'development', 'staging', 'production'
      t.string :phone_number, null: false # '15551924179'
      t.string :redirect_url # 'https://abc123.ngrok.io/api/v1/webhooks/meta_whatsapp'
      t.boolean :active, default: true
      t.text :description # 'João - Desenvolvimento Local'
      t.string :developer_name # 'João Silva'
      t.timestamps
    end

    add_index :whatsapp_configurations, [ :environment, :phone_number ], unique: true
    add_index :whatsapp_configurations, :phone_number
    add_index :whatsapp_configurations, :active
  end
end
