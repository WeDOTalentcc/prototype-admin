class DropWhatsappConfigurationsFromTenants < ActiveRecord::Migration[7.1]
  def up
    Account.where.not(tenant: "public").pluck(:tenant).each do |tenant|
      Apartment::Tenant.switch(tenant) do
        drop_table :whatsapp_configurations if table_exists?(:whatsapp_configurations)
      end
    end
  end

  def down
  end
end
