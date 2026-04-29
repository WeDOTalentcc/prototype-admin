# app/services/bulk_imports/base_service.rb
require "csv"

module BulkImports
  class BaseService
    def self.call(**args)
      new(**args).call
    end

    attr_reader :data_file, :user, :account, :mapping,
                :total_rows, :processed_count, :failed_imports

    def initialize(data_file_id:, mapping:, user_id:)
      @user = User.find(user_id)
      @account = @user.account
      Apartment::Tenant.switch!(@account.tenant)

      @data_file = DataFile.find(data_file_id)
      @mapping = mapping.transform_keys(&:to_sym).compact
      @processed_count = 0
      @failed_imports = []

      # Adicionando um logger com contexto para fácil rastreamento
      @logger = Rails.logger
      @log_prefix = "[BulkImport][DataFileID: #{@data_file.id}][User: #{@user.id}]"
    end

    def call
      broadcast_status("started")

      csv_data = data_file.file.download

      csv_data.force_encoding("UTF-8").delete!("\uFEFF")

      csv = CSV.parse(csv_data, headers: true)
      @total_rows = csv.size

      ids = []

      header_to_attribute_map = mapping.invert

      csv.each_with_index do |row, index|
        begin
          p "Processing row ##{index + 1}..."
          new_item = process_row(row, header_to_attribute_map)
          ids << new_item.id if new_item.respond_to?(:id)
          @processed_count += 1
        rescue => e
          p "ERROR processing row ##{index + 1}: #{e.message}", level: :error
          failed_imports << { raw_data: row.to_s.strip, errors: [ e.message ] }
        end

        broadcast_progress if should_broadcast?
      end

      create_finished_message(ids) if ids.any?
      p "Import process completed. Processed: #{@processed_count}, Failed: #{@failed_imports.count}."
      broadcast_status("completed")
    end

    private

    def process_row(row, header_map)
      raise NotImplementedError, "#{self.class.name} must implement the 'process_row' method"
    end

    def build_attributes_from(row, header_map)
      header_map.each_with_object({}) do |(header, attribute), attrs|
        attrs[attribute] = row[header]&.strip
      end
    end

    def should_broadcast?
      # Broadcasts at 0%, 5%, 10%, ..., 100%
      (processed_count % (total_rows / 20.0).ceil).zero? || processed_count == total_rows
    end


    def broadcast(payload)
      ImportCsvChannel.broadcast_to(data_file, payload)
      p "Broadcasting progress: #{payload.inspect}"
    end

    def broadcast_status(status)
      payload = {
        status: status,
        summary: {
          total: total_rows,
          processed: processed_count,
          failed: failed_imports.count
        },
        errors: failed_imports
      }
      broadcast(payload)
    end

    def broadcast_progress
      return if total_rows.zero?
      payload = {
        status: "processing",
        progress: (processed_count.to_f / total_rows * 100).round,
        processed_count: processed_count,
        total_count: total_rows
      }
      broadcast(payload)
    end

    def create_finished_message(imported_ids)
      message_content = "Importação concluída: #{processed_count} registros processados com sucesso."
      message_content += " #{failed_imports.count} falhas." if failed_imports.any?

      Message.create!(
        account_id: account.id,
        reference: user,
        entity: Message::ROLE_SYSTEM,
        content: message_content,
        metadata: {
          next_suggestions: [
            {
              suggestion: "Enviar registros para uma vaga",
              content: "Enviar os candidatos: [#{imported_ids.join(', ')}] para a vaga \"nome da vaga aqui\" usando o status \"status aqui\".",
              metadata: {
                entity: self.class.name.demodulize.gsub("ImporterService", "").singularize,
                reference_ids: imported_ids
              }
            }
          ]
        }
      )
    end
  end
end
