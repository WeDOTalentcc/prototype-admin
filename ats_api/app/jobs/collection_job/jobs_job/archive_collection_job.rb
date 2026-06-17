# frozen_string_literal: true

module CollectionJob
  module JobsJob
    class ArchiveCollectionJob < ApplicationJob
      queue_as :default
      sidekiq_options retry: 2

      def perform(select_all_params, user_id, is_archived: true)
        user = User.find(user_id)
        account = user.account
        Current.user = user
        Apartment::Tenant.switch!(account.tenant)

        page = 1
        first_record = CollectionService.call(select_all_params, page)
        total_count = first_record[:total_count]
        total_page = (total_count / 30.0).ceil
        updated_count = 0

        Rails.logger.info "💡 Total de jobs a processar: #{total_count}"
        Rails.logger.info "💡 Total de páginas: #{total_page}"

        while page <= total_page
          records = CollectionService.call(select_all_params, page)[:records]

          records.each do |job|
            next if job.is_deleted

            begin
              job.update!(is_archived: is_archived)
              updated_count += 1
            rescue => e
              Rails.logger.error "❌ Erro ao atualizar Job ##{job.id}: #{e.message}"
            end
          end

          percent = (page * 100.0 / total_page).round
          CollectionChannel.broadcast_to("#{user_id}_collection", {
            status: "loading",
            percent: percent,
            message: "Processando: #{updated_count}/#{total_count} jobs"
          })

          page += 1
        end

        sleep(1)
        CollectionChannel.broadcast_to("#{user_id}_collection", {
          status: "completed",
          percent: 100,
          message: "#{updated_count} jobs #{is_archived ? 'arquivados' : 'desarquivados'} com sucesso"
        })

      rescue => e
        CollectionChannel.broadcast_to("#{user_id}_collection", {
          status: "error",
          message: "Erro ao processar arquivamento: #{e.message}"
        })

        raise
      end
    end
  end
end
