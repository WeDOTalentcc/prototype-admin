# frozen_string_literal: true

module CollectionJob
  module AppliesJob
    class RejectCollectionJob < ApplicationJob
      queue_as :default
      sidekiq_options retry: 2

      def perform(select_all_params, user_id, job_id)
        user = User.find(user_id)
        account = user.account
        Current.user = user
        Apartment::Tenant.switch!(account.tenant)

        updated_count = 0
        skipped_count = 0
        applies = nil
        total_count = 0

        if select_all_params[:reference_ids].present?
          reference_ids = select_all_params[:reference_ids]
          applies = Apply.where(id: reference_ids, job_id: job_id, is_deleted: false)
          total_count = applies.count
          Rails.logger.info "💡 Total de applies a processar: #{total_count} (via reference_ids)"
        else
          applies = Apply.where(job_id: job_id, is_deleted: false)

          if select_all_params[:where].present?
            select_all_params[:where].each do |key, value|
              applies = applies.where(key => value)
            end
          end

          if select_all_params[:filter].present?
            filter = select_all_params[:filter]
            filter.each do |field_name, field_value|
              next unless Apply.column_names.include?(field_name.to_s)

              if field_value.is_a?(Array) || field_value.is_a?(Integer) || field_value.is_a?(Hash)
                applies = applies.where(field_name => field_value)
              elsif field_value.present?
                applies = applies.where(Apply.arel_table[field_name].matches("%#{Apply.sanitize_sql_like(field_value.to_s)}%"))
              end
            end
          end

          if select_all_params[:except_ids].present?
            applies = applies.where.not(id: select_all_params[:except_ids])
          end

          if select_all_params[:order].present?
            applies = applies.order(select_all_params[:order])
          end

          total_count = applies.count
          Rails.logger.info "💡 Total de applies a processar: #{total_count} (via filtros)"
        end

        reason_for_reject = (select_all_params["reason_for_reject"] || select_all_params[:reason_for_reject]).presence
        reason_code = (select_all_params["reason_code"] || select_all_params[:reason_code]).presence
        reason_category = (select_all_params["reason_category"] || select_all_params[:reason_category]).presence
        internal_comment = (select_all_params["internal_comment"] || select_all_params[:internal_comment]).presence

        applies.each_with_index do |apply, index|
          result = reject_apply(apply, reason_for_reject: reason_for_reject, reason_code: reason_code, reason_category: reason_category, internal_comment: internal_comment)
          if result[:success]
            updated_count += 1
          else
            skipped_count += 1
          end

          if (index + 1) % 10 == 0 || (index + 1) == total_count
            percent = ((index + 1) * 100.0 / total_count).round
            CollectionChannel.broadcast_to("#{user_id}_collection", {
              action: "reject_collection",
              status: "loading",
              percent: percent,
              message: "Processando: #{updated_count}/#{total_count} rejeitados, #{skipped_count} ignorados"
            })
          end
        end

        sleep(1)
        CollectionChannel.broadcast_to("#{user_id}_collection", {
          action: "reject_collection",
          status: "completed",
          percent: 100,
          updated: updated_count,
          skipped: skipped_count,
          total: total_count,
          message: "#{updated_count} candidaturas rejeitadas com sucesso"
        })

      rescue => e
        CollectionChannel.broadcast_to("#{user_id}_collection", {
          action: "reject_collection",
          status: "error",
          message: "Erro ao processar rejeição: #{e.message}"
        })

        raise
      end

      private

      def reject_apply(apply, reason_for_reject: nil, reason_code: nil, reason_category: nil, internal_comment: nil)
        current_process = apply.selective_process
        unless current_process
          return {
            success: false,
            message: "Apply #{apply.id} não possui processo seletivo definido"
          }
        end

        unless current_process.rejected_process_id.present?
          return {
            success: false,
            message: "Apply #{apply.id}: Processo '#{current_process.id}' não tem processo rejeitado configurado"
          }
        end

        rejected_process = SelectiveProcess.find_by(id: current_process.rejected_process_id)
        unless rejected_process
          return {
            success: false,
            message: "Apply #{apply.id}: Processo rejeitado ID #{current_process.rejected_process_id} não encontrado"
          }
        end

        update_attrs = {
          selective_process_id: rejected_process.id,
          selective_process_status: rejected_process.status
        }
        update_attrs[:reason_for_reject] = reason_for_reject if reason_for_reject.present?
        update_attrs[:reason_code] = reason_code if reason_code.present?
        update_attrs[:reason_category] = reason_category if reason_category.present?
        update_attrs[:internal_comment] = internal_comment if internal_comment.present?

        apply.update!(update_attrs)


        { success: true }
      rescue => e
        { success: false, message: "Apply #{apply.id}: #{e.message}" }
      end
    end
  end
end
