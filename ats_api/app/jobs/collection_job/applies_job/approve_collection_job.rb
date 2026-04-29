# frozen_string_literal: true

module CollectionJob
  module AppliesJob
    class ApproveCollectionJob < ApplicationJob
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
        Thread.current[:skip_screening_enqueue] = true

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

        applies.each_with_index do |apply, index|
          result = approve_apply(apply)
          if result[:success]
            updated_count += 1
          else
            skipped_count += 1
          end

          if (index + 1) % 10 == 0 || (index + 1) == total_count
            percent = ((index + 1) * 100.0 / total_count).round
            CollectionChannel.broadcast_to("#{user_id}_collection", {
              action: "approve_collection",
              status: "loading",
              percent: percent,
              message: "Processando: #{updated_count}/#{total_count} aprovados, #{skipped_count} ignorados"
            })
          end
        end

        sleep(1)
        CollectionChannel.broadcast_to("#{user_id}_collection", {
          action: "approve_collection",
          status: "completed",
          percent: 100,
          updated: updated_count,
          skipped: skipped_count,
          total: total_count,
          message: "#{updated_count} candidaturas aprovadas com sucesso"
        })
      rescue => e
        CollectionChannel.broadcast_to("#{user_id}_collection", {
          action: "approve_collection",
          status: "error",
          message: "Erro ao processar aprovação: #{e.message}"
        })

        raise
      ensure
        Thread.current[:skip_screening_enqueue] = false
        if defined?(account) && account && updated_count.positive?
          Jobs::SendScreeningEvaluationsJob.perform_async(job_id, account.id)
        end
      end

      private

      def approve_apply(apply)
        current_process = apply.selective_process
        unless current_process
          return {
            success: false,
            message: "Apply #{apply.id} não possui processo seletivo definido"
          }
        end

        unless current_process.approved_process_id.present?
          return {
            success: false,
            message: "Apply #{apply.id}: Processo '#{current_process.id} - '#{current_process.approved_process_id}' não tem processo aprovado configurado"
          }
        end

        approved_process = SelectiveProcess.find_by(id: current_process.approved_process_id)
        unless approved_process
          return {
            success: false,
            message: "Apply #{apply.id}: Processo aprovado ID #{current_process.approved_process_id} não encontrado"
          }
        end

        apply.update!(
          selective_process_id: approved_process.id,
          selective_process_status: approved_process.status
        )


        { success: true }
      rescue => e
        { success: false, message: "Apply #{apply.id}: #{e.message}" }
      end
    end
  end
end
