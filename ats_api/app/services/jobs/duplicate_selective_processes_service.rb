# frozen_string_literal: true

module Jobs
  class DuplicateSelectiveProcessesService
    def initialize(target_job:, source_job_id:, replace: false)
      @target_job = target_job
      @source_job_id = source_job_id
      @replace = replace
    end

    def call
      return error("Job de origem não encontrado") unless source_job
      return error("Jobs devem pertencer à mesma conta") unless same_account?

      source_processes = source_job.selective_processes.where(is_deleted: false).order(:position)
      return error("Job de origem não possui etapas") if source_processes.empty?

      ActiveRecord::Base.transaction do
        target_job.selective_processes.update_all(is_deleted: true) if replace
        copy_processes(source_processes)
      end

      success
    end

    private

    attr_reader :target_job, :source_job_id, :replace

    def source_job
      @source_job ||= Job.find_by(id: source_job_id, is_deleted: false)
    end

    def same_account?
      target_job.account_id == source_job.account_id
    end

    def copy_processes(source_processes)
      offset = replace ? 0 : next_position_offset
      old_to_new = {}

      source_processes.each do |original|
        new_process = build_copy(original, offset)
        new_process.save!
        old_to_new[original.id] = new_process
      end

      link_approved_rejected(source_processes, old_to_new)
    end

    def build_copy(original, offset)
      copy = original.dup
      copy.job_id = target_job.id
      copy.account_id = target_job.account_id
      copy.position = (original.position || 0) + offset
      copy.external_id = nil
      copy.is_deleted = false
      copy.approved_process_id = nil
      copy.rejected_process_id = nil
      copy
    end

    def link_approved_rejected(source_processes, old_to_new)
      source_processes.each do |original|
        new_process = old_to_new[original.id]
        next unless new_process

        updates = {}
        updates[:approved_process_id] = old_to_new[original.approved_process_id]&.id if original.approved_process_id
        updates[:rejected_process_id] = old_to_new[original.rejected_process_id]&.id if original.rejected_process_id
        new_process.update!(updates) if updates.any?
      end
    end

    def next_position_offset
      max = target_job.selective_processes.where(is_deleted: false).maximum(:position) || -1
      max + 1
    end

    def success
      processes = target_job.selective_processes.where(is_deleted: false).order(:position)
      { success: true, job: target_job, selective_processes: processes }
    end

    def error(message)
      { success: false, error: message }
    end
  end
end
