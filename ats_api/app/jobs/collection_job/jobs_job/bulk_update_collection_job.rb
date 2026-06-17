# frozen_string_literal: true

module CollectionJob
  module JobsJob
    class BulkUpdateCollectionJob < ApplicationJob
      queue_as :default
      sidekiq_options retry: 2

      def perform(job_ids, fields, user_id)
        setup_context(user_id)

        result = ::Jobs::BulkUpdateService.new(
          job_ids: job_ids,
          fields: fields,
          user: Current.user
        ).call

        broadcast_completion(user_id, result)
      rescue StandardError => e
        handle_error(user_id, e)
        raise
      end

      private

      def setup_context(user_id)
        user = User.find(user_id)
        Current.user = user
        Apartment::Tenant.switch!(user.account.tenant)
      end

      def broadcast_completion(user_id, result)
        CollectionChannel.broadcast_to("#{user_id}_collection", {
          status: "completed",
          percent: 100,
          message: "#{result[:updated]} vagas atualizadas",
          batch_id: result[:batch_id]
        })
      end

      def handle_error(user_id, error)
        Rails.logger.error "[#{self.class.name}] Error: #{error.message}"

        CollectionChannel.broadcast_to("#{user_id}_collection", {
          status: "error",
          message: "Erro ao atualizar vagas: #{error.message}"
        })
      end
    end
  end
end
