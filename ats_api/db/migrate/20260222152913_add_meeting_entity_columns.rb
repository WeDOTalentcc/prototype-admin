# frozen_string_literal: true

class AddMeetingEntityColumns < ActiveRecord::Migration[7.1]
  def up
    return unless ActiveRecord::Base.connection.table_exists?(:entity_columns)

    Account.find_each do |account|
      Apartment::Tenant.switch(account.tenant) do
        next if EntityColumn.exists?(entity: 'meeting', account_id: account.id, requested: 'default', is_main: true)

        default_columns = EntityColumnService::Entities::Meeting.default_columns
        structure = EntityColumnService::Entities::Meeting.structure

        columns_view = structure.select { |col| default_columns.include?(col[:value]) }

        EntityColumn.create!(
          entity: 'meeting',
          account_id: account.id,
          requested: 'default',
          is_main: true,
          is_views: false,
          is_public: false,
          is_deleted: false,
          columns_view: columns_view
        )

        Rails.logger.info "Created default entity_column for meetings in account #{account.id} (#{account.tenant})"
      rescue => e
        Rails.logger.error "Failed to create entity_column for meetings in account #{account.id}: #{e.message}"
      end
    end
  end

  def down
    return unless ActiveRecord::Base.connection.table_exists?(:entity_columns)

    Account.find_each do |account|
      Apartment::Tenant.switch(account.tenant) do
        EntityColumn.where(entity: 'meeting', account_id: account.id).destroy_all
      end
    end
  end
end
