class DepartmentImportJob < ApplicationJob
  queue_as :default

  def perform(data_file_id:, user_id:)
    BulkImports::DepartmentsImporterService.call(
      data_file_id: data_file_id,
      user_id: user_id
    )
  end
end
