class CreateWhatsappTenantMappings < ActiveRecord::Migration[7.1]
  def change
    create_table :whatsapp_tenant_mappings do |t|
      t.string :phone_number, null: false
      t.bigint :account_id, null: false
      t.datetime :last_interaction_at
      t.timestamps
    end

    add_index :whatsapp_tenant_mappings, :phone_number
    add_index :whatsapp_tenant_mappings, :account_id
    add_index :whatsapp_tenant_mappings, [ :phone_number, :account_id ], unique: true, name: 'idx_whatsapp_mappings_phone_account'
    add_index :whatsapp_tenant_mappings, :last_interaction_at

    add_foreign_key :whatsapp_tenant_mappings, :accounts, on_delete: :cascade
  end
end
