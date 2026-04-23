# frozen_string_literal: true

class CandidateImportJob < ApplicationJob
  include AtsSyncable

  queue_as :default

  def perform(data_file_ids:, user_id:, account_id:)
    return unless (user = User.find_by(id: user_id))

    account = Account.find_by(id: account_id)
    return unless account

    Apartment::Tenant.switch(account.tenant) do
      data_files = DataFile.where(id: data_file_ids).to_a
      total_files = data_files.count
      processed_files = 0
      successful_imports = 0
      failed_imports = 0

      broadcast_progress(user, {
        status: "started",
        total: total_files,
        processed: 0,
        successful: 0,
        failed: 0,
        message: "Starting import of #{total_files} file(s)..."
      })

      data_files.each do |data_file|
        next unless data_file.file.attached?

        begin
          result = import_candidate_from(data_file, user)

          if result
            successful_imports += 1
          else
            failed_imports += 1
          end
        rescue => e
          failed_imports += 1
          Rails.logger.error "[CandidateImportJob] Error processing DataFile ##{data_file.id}: #{e.message}"
        end

        processed_files += 1

        broadcast_progress(user, {
          status: "processing",
          total: total_files,
          processed: processed_files,
          successful: successful_imports,
          failed: failed_imports,
          current_file: data_file.id,
          message: "Processing file #{processed_files} of #{total_files}..."
        })
      end

      broadcast_progress(user, {
        status: "completed",
        total: total_files,
        processed: processed_files,
        successful: successful_imports,
        failed: failed_imports,
        message: "Import complete! #{successful_imports} success(es), #{failed_imports} failure(s)."
      })

      Rails.logger.info "✅ [CandidateImportJob] Import completed: #{successful_imports} successes, #{failed_imports} failures"
    end
  end

  private

  def broadcast_progress(user, data)
    ActionCable.server.broadcast(
      "candidate_import_#{user.account_id}",
      {
        type: "candidate_import_progress",
        data: data,
        timestamp: Time.current.iso8601
      }
    )
  end

  def import_candidate_from(data_file, user)
    text = extract_text(data_file)
    return false if text.blank?

    candidate_data = RecruitAgentService.extract_candidate_data(text)
    return false unless candidate_data

    candidate = Candidate.create(
      name: candidate_data.dig(:basics, :name) || "Imported Candidate ##{data_file.id}",
      account_id: user.account_id
    )

    if candidate.persisted?
      sync_candidate_to_ats(candidate)
      true
    else
      Rails.logger.error "[CandidateImportJob] Failed to save candidate from DataFile ##{data_file.id}: #{candidate.errors.full_messages.join(', ')}"
      false
    end
  rescue => e
    Rails.logger.error "[CandidateImportJob] Failed to import candidate from DataFile ##{data_file.id}: #{e.message}"
    false
  end

  def extract_text(data_file)
    io = StringIO.new(data_file.file.download)
    yomu = Yomu.new(io)
    yomu.text
  end
end
