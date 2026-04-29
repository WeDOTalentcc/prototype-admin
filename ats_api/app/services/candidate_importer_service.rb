require "csv"

class CandidateImporterService
  def self.call(data_file_id:, mapping:, user_id: nil)
    new(data_file_id: data_file_id, mapping: mapping, user_id: user_id).call
  end

  attr_reader :data_file, :mapping, :total_rows, :processed_count, :failed_imports

  def initialize(data_file_id:, mapping:, user_id: nil)
    Apartment::Tenant.switch!(User.find(user_id).account.tenant)
    @account = User.find(user_id).account
    @data_file = DataFile.find(data_file_id)
    @mapping = mapping.transform_keys(&:to_sym).compact
    @processed_count = 0
    @failed_imports = []
  end

  def call
    broadcast_status("iniciando")

    csv_data = data_file.file.download
    csv = CSV.parse(csv_data, headers: true)
    @total_rows = csv.size

    header_to_attribute_map = mapping.invert

    csv.each do |row|
      candidate_attributes = build_attributes_from(row, header_to_attribute_map)
      create_candidate(candidate_attributes, row.to_s.strip)

      @processed_count += 1
      broadcast_progress if processed_count % 5 == 0 || processed_count == total_rows
    end

    broadcast_status("finalizado")
  end

  private

  def build_attributes_from(row, header_map)
    header_map.each_with_object({}) do |(header, attribute), attrs|
      attrs[attribute] = row[header]
    end
  end

  def create_candidate(attributes, raw_data)
    attributes["account_id"] = @account.id
    "Criando candidato com atributos: #{attributes.inspect}"
  rescue ActiveRecord::RecordInvalid => e
    failed_imports << { raw_data: raw_data, errors: e.record.errors.full_messages }
  end

  def broadcast(payload)
    CandidateImportChannel.broadcast_to(data_file, payload)
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
    payload = {
      status: "processando",
      progress: (processed_count.to_f / total_rows * 100).round(2),
      processed_count: processed_count,
      total_count: total_rows
    }
    broadcast(payload)
  end
end
