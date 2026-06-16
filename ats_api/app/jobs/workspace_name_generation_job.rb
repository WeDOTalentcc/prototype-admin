# frozen_string_literal: true

class WorkspaceNameGenerationJob < ApplicationJob
  queue_as :default
  sidekiq_options retry: 2

  def perform(workspace_id, message_content, tenant)
    Apartment::Tenant.switch(tenant) do
      workspace = Workspace.find_by(id: workspace_id)
      return unless workspace

      workspace.generate_name_from_content(message_content)
    end
  rescue => e
    Rails.logger.error "[WorkspaceNameGenerationJob] Error for workspace #{workspace_id}: #{e.class} - #{e.message}"
  end
end
