# frozen_string_literal: true

module CollectionJob
  module SourcedProfilesJob
    class ConvertToCandidatesCollectionJob < ApplicationJob
      queue_as :default
      sidekiq_options retry: 2

      def perform(select_all_params, user_id)
        user = User.find(user_id)
        account = user.account
        Apartment::Tenant.switch!(account.tenant)

        page = 1
        converted_count = 0
        failed_count = 0
        skipped_count = 0

        reference_type = select_all_params[:reference_type].to_s
        is_sourced_profile_sourcing = reference_type.casecmp("SourcedProfileSourcing").zero? ||
                                     reference_type.downcase == "sourced_profile_sourcings"

        # Primeira busca para obter total de páginas e primeira página de dados
        result = CollectionService.call(select_all_params, page)
        total_count = result[:total_count]
        total_pages = (total_count / 30.0).ceil

        while page <= total_pages
          # Buscar apenas para páginas subsequentes (reusar primeira busca)
          result = CollectionService.call(select_all_params, page) if page > 1

          sourced_profile_ids = []

          result[:records].each do |record|
            next if record.is_deleted

            sourced_profile_id = extract_sourced_profile_id(record, is_sourced_profile_sourcing, account)

            if sourced_profile_id
              sourced_profile_ids << sourced_profile_id
            else
              skipped_count += 1
            end
          end

          if sourced_profile_ids.any?
            begin
              conversion_result = SourcedProfiles::ConvertToCandidateService.call(sourced_profile_ids)

              converted_count += conversion_result[:converted]
              skipped_count += conversion_result[:skipped]
              failed_count += conversion_result[:failed]
            rescue => e
              failed_count += sourced_profile_ids.size
            end
          end

          broadcast_progress(user_id, page, total_pages, converted_count, failed_count, skipped_count)

          page += 1
        end

        sleep(1)
        broadcast_completion(user_id, converted_count, failed_count, skipped_count)
      rescue => e

        broadcast_error(user_id, e.message)
        raise
      end

      private

      def extract_sourced_profile_id(record, is_sourced_profile_sourcing, account)
        return nil unless record

        if is_sourced_profile_sourcing
          sourced_profile = record.respond_to?(:sourced_profile) ? record.sourced_profile : nil
          return nil unless sourced_profile

          if sourced_profile.candidate_id.present?
            return nil
          end

          sourced_profile.id
        else
          record.id
        end
      end

      def broadcast_progress(user_id, page, total_pages, converted, failed, skipped)
        percent = (page * 100.0 / total_pages).round

        CollectionChannel.broadcast_to(
          "#{user_id}_collection",
          {
            status: "loading",
            percent: percent,
            converted: converted,
            failed: failed,
            skipped: skipped
          }
        )
      end

      def broadcast_completion(user_id, converted, failed, skipped)
        CollectionChannel.broadcast_to(
          "#{user_id}_collection",
          {
            status: "completed",
            percent: 100,
            converted: converted,
            failed: failed,
            skipped: skipped,
            message: "Conversão concluída: #{converted} perfis convertidos, #{skipped} pulados"
          }
        )
      end

      def broadcast_error(user_id, error_message)
        CollectionChannel.broadcast_to(
          "#{user_id}_collection",
          {
            status: "error",
            percent: 0,
            message: "Erro na conversão: #{error_message}"
          }
        )
      end
    end
  end
end
