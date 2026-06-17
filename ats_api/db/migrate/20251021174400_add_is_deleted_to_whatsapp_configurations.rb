# frozen_string_literal: true

class AddIsDeletedToWhatsappConfigurations < ActiveRecord::Migration[7.1]
  def change
    unless column_exists?(:whatsapp_configurations, :is_deleted)
      add_column :whatsapp_configurations, :is_deleted, :boolean, default: false, null: false
    end

    unless index_exists?(:whatsapp_configurations, :is_deleted)
      add_index :whatsapp_configurations, :is_deleted
    end
  end
end
