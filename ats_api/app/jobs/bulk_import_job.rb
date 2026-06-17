
class BulkImportJob < ApplicationJob
  queue_as :default

  def perform(entity_type:, data_file_id:, mapping:, user_id:, account_id:)
    account = Account.find_by(id: account_id)
    return unless account

    Apartment::Tenant.switch(account.tenant) do
      importer_service = "BulkImports::#{entity_type.camelize}ImporterService".constantize

      importer_service.call(
        data_file_id: data_file_id,
        mapping: mapping,
        user_id: user_id
      )
    end
  rescue NameError
    Rails.logger.error "[BulkImportJob] No importer service for entity: #{entity_type}"
  end
end
