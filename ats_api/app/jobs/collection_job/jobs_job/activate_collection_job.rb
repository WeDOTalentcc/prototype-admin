# frozen_string_literal: true

module CollectionJob
  module JobsJob
    class ActivateCollectionJob < ApplicationJob
      queue_as :default
      sidekiq_options retry: 2

      RECORDS_PER_PAGE = 30

      def perform(select_all_params, user_id, is_active: true, reason_for_pause: nil)
        setup_context(user_id)

        result = process_jobs_activation(
          select_all_params: select_all_params,
          user_id: user_id,
          is_active: is_active,
          reason_for_pause: reason_for_pause
        )

        broadcast_completion(user_id, result, is_active)
      rescue StandardError => e
        handle_error(user_id, is_active, e)
        raise
      end

      private

      attr_reader :target_status

      def setup_context(user_id)
        user = User.find(user_id)
        Current.user = user
        Apartment::Tenant.switch!(user.account.tenant)
      end

      def process_jobs_activation(select_all_params:, user_id:, is_active:, reason_for_pause:)
        @target_status = find_target_status(is_active)

        pagination = calculate_pagination(select_all_params)
        return { updated_count: 0, total_count: 0 } if pagination[:total_count].zero?

        updated_count = process_all_pages(
          select_all_params: select_all_params,
          pagination: pagination,
          user_id: user_id,
          is_active: is_active,
          reason_for_pause: reason_for_pause
        )

        { updated_count: updated_count, total_count: pagination[:total_count] }
      end

      def calculate_pagination(select_all_params)
        first_page = CollectionService.call(select_all_params, 1)
        total_count = first_page[:total_count]

        {
          total_count: total_count,
          total_pages: (total_count / RECORDS_PER_PAGE.to_f).ceil
        }
      end

      def process_all_pages(select_all_params:, pagination:, user_id:, is_active:, reason_for_pause:)
        updated_count = 0

        (1..pagination[:total_pages]).each do |page|
          records = fetch_page_records(select_all_params, page)
          updated_count += process_page_records(records, is_active, reason_for_pause)

          broadcast_progress(user_id, page, pagination[:total_pages], updated_count, pagination[:total_count])
        end

        updated_count
      end

      def fetch_page_records(select_all_params, page)
        CollectionService.call(select_all_params, page)[:records]
      end

      def process_page_records(records, is_active, reason_for_pause)
        records.count do |job|
          update_job_status(job, is_active, reason_for_pause)
        end
      end

      def update_job_status(job, is_active, reason_for_pause)
        return false if job.is_deleted

        job.update!(build_update_params(is_active, reason_for_pause))
        true
      rescue StandardError => e
        log_job_update_error(job, e)
        false
      end

      def build_update_params(is_active, reason_for_pause)
        params = { is_active: is_active }
        params[:job_status_id] = target_status.id if target_status
        params[:reason_for_pause] = is_active ? nil : reason_for_pause
        params
      end

      def broadcast_progress(user_id, current_page, total_pages, updated_count, total_count)
        percent = (current_page * 100.0 / total_pages).round

        CollectionChannel.broadcast_to("#{user_id}_collection", {
          status: "loading",
          percent: percent,
          message: "Processing: #{updated_count}/#{total_count} jobs"
        })
      end

      def broadcast_completion(user_id, result, is_active)
        sleep(1)

        CollectionChannel.broadcast_to("#{user_id}_collection", {
          status: "completed",
          percent: 100,
          message: build_completion_message(result, is_active)
        })
      end

      def build_completion_message(result, is_active)
        action = is_active ? "activated" : "paused"
        status_info = target_status ? " and status changed to '#{target_status.name}'" : ""
        "#{result[:updated_count]} jobs #{action} successfully#{status_info}"
      end

      def handle_error(user_id, is_active, error)
        action = is_active ? "activation" : "pause"
        Rails.logger.error "[#{self.class.name}] Error processing #{action}: #{error.message}"

        CollectionChannel.broadcast_to("#{user_id}_collection", {
          status: "error",
          message: "Error processing #{action}: #{error.message}"
        })
      end

      def find_target_status(is_active)
        return nil unless defined?(JobStatus)

        status_names = is_active ? [ "Ativa", "Ativas" ] : [ "Paralisada", "Paralisadas" ]
        JobStatus.find_by(name: status_names)
      end

      def log_job_update_error(job, error)
        Rails.logger.error "[#{self.class.name}] Error updating Job ##{job.id}: #{error.message}"
      end
    end
  end
end
