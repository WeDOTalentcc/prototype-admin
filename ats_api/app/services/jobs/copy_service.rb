# frozen_string_literal: true

module Jobs
  class CopyService
    MAX_COPY_AMOUNT = 99

    def initialize(job_id:, user_id:, entities: [])
      @job_id = job_id
      @user_id = user_id
      @entities = entities
      @account = nil
    end

    def call
      return error_result("Job not found") unless load_job
      return error_result("User not found") unless load_user

      copy_job
    end

    def load_and_validate
      return false unless load_job
      return false unless load_user

      true
    end

    def self.copy_multiple(amount:, job_id:, user_id:, entities: [])
      return if amount.nil? || amount.zero?
      return if amount > MAX_COPY_AMOUNT

      service = new(job_id: job_id, user_id: user_id, entities: entities)
      return unless service.load_and_validate

      service.copy_multiple_jobs(amount)
    end

    def copy_multiple_jobs(amount)
      current_amount = 0
      copied_job_ids = []
      start_time = Time.current

      amount.times do |index|
        result = copy_job
        break unless result[:success]

        copied_job_ids << result[:job].id
        current_amount += 1

        broadcast_progress(
          current: current_amount,
          total: amount,
          copied_job_ids: copied_job_ids,
          elapsed_time: (Time.current - start_time).round(2)
        )

        sleep(1) unless Rails.env.test?
      end

      broadcast_completion(
        total: current_amount,
        copied_job_ids: copied_job_ids,
        total_time: (Time.current - start_time).round(2)
      )

      success_result(nil, current_amount)
    rescue StandardError => e
      Rails.logger.error "[#{self.class.name}] Error copying jobs: #{e.message}"
      broadcast_error(e.message)
      error_result(e.message)
    end

    private

    attr_reader :job_id, :user_id, :entities, :job, :user, :account

    def load_job
      @job = Job.find_by(id: job_id, is_deleted: false)
      @job.present?
    end

    def load_user
      @user = User.find_by(id: user_id)
      return false unless @user

      @account = @user.account
      true
    end

    def copy_job
      new_job = duplicate_job_attributes
      return error_result("Failed to save job") unless new_job.save

      copy_relationships(new_job)
      reindex_job(new_job)

      success_result(new_job, 1)
    rescue StandardError => e
      Rails.logger.error "[#{self.class.name}] Error copying job ##{job_id}: #{e.message}"
      error_result(e.message)
    end

    def duplicate_job_attributes
      new_job = job.dup
      apply_job_modifications(new_job)
      new_job
    end

    def apply_job_modifications(new_job)
      new_job.title = next_copy_title
      new_job.source_job_id = job.id
      new_job.is_archived = false
      new_job.is_active = true
      new_job.external_id = nil
      new_job.provider_job_id = ""
      new_job.published_date = nil
      new_job.user_id = user_id
      new_job.account_id = account.id
    end

    def next_copy_title
      copy_count = Job.where(source_job_id: job.id).count + 1
      "#{job.title} ##{copy_count}"
    end

    def copy_relationships(new_job)
      copy_direct_relationships(new_job)
      copy_polymorphic_relationships(new_job) if should_copy_polymorphic?
    end

    def copy_direct_relationships(new_job)
      DIRECT_RELATIONSHIPS.each do |relation_name|
        next unless should_copy_relation?(relation_name)

        if relation_name == :selective_processes
          copy_selective_processes(new_job)
        else
          copy_relation(new_job, relation_name)
        end
      end
    end

    def copy_polymorphic_relationships(new_job)
      POLYMORPHIC_RELATIONSHIPS.each do |relation_name|
        next unless should_copy_relation?(relation_name)

        copy_polymorphic_relation(new_job, relation_name)
      end
    end

    def should_copy_polymorphic?
      entities.empty? || entities.any? { |e| POLYMORPHIC_RELATIONSHIPS.include?(e.to_sym) }
    end

    def should_copy_relation?(relation_name)
      entities.empty? || entities.include?(relation_name.to_s)
    end

    def copy_relation(new_job, relation_name)
      return unless job.respond_to?(relation_name)

      relations = relation_scope_for_copy(relation_name)
      return if relations.blank?

      relations.each do |relation|
        copy_single_relation(new_job, relation_name, relation)
      end
    end

    def copy_selective_processes(new_job)
      ordered_processes = job.selective_processes.order(:position)
      return if ordered_processes.blank?

      old_id_to_new = {}
      ordered_processes.each do |old_process|
        new_process = build_and_save_selective_process_copy(new_job, old_process)
        old_id_to_new[old_process.id] = new_process if new_process
      end

      ordered_processes.each do |old_process|
        new_process = old_id_to_new[old_process.id]
        next unless new_process

        new_approved_id = old_id_to_new[old_process.approved_process_id]&.id
        new_rejected_id = old_id_to_new[old_process.rejected_process_id]&.id
        new_process.update(approved_process_id: new_approved_id, rejected_process_id: new_rejected_id)
      end
    end

    def build_and_save_selective_process_copy(new_job, old_process)
      new_process = old_process.dup
      new_process.job_id = new_job.id
      new_process.account_id = account.id
      apply_selective_process_modifications(new_process)
      new_process.save
      new_process
    rescue StandardError => e
      Rails.logger.warn "[#{self.class.name}] Error copying selective_process #{old_process.id}: #{e.message}"
      nil
    end

    def relation_scope_for_copy(relation_name)
      scope = job.send(relation_name)
      return scope.order(:position) if relation_name == :selective_processes && scope.respond_to?(:order)
      scope
    end

    def copy_single_relation(new_job, relation_name, relation)
      new_relation = relation.dup
      new_relation.job_id = new_job.id
      new_relation.account_id = account.id if new_relation.respond_to?(:account_id=)
      new_relation.save
    rescue StandardError => e
      Rails.logger.warn "[#{self.class.name}] Error copying #{relation_name}: #{e.message}"
    end

    def apply_selective_process_modifications(new_process)
      new_process.external_id = nil
      new_process.workflow_template_id = nil if new_process.respond_to?(:workflow_template_id=)
      new_process.uid = nil if new_process.respond_to?(:uid=)
      new_process.approved_process_id = nil if new_process.respond_to?(:approved_process_id=)
      new_process.rejected_process_id = nil if new_process.respond_to?(:rejected_process_id=)
    end

    def copy_polymorphic_relation(new_job, relation_name)
      return unless job.respond_to?(relation_name)

      relations = job.send(relation_name)
      return if relations.blank?

      relations.each do |relation|
        copy_single_polymorphic_relation(new_job, relation)
      end
    end

    def copy_single_polymorphic_relation(new_job, relation)
      new_relation = relation.dup
      new_relation.reference_id = new_job.id
      new_relation.reference_type = "Job"
      new_relation.account_id = account.id if new_relation.respond_to?(:account_id=)
      new_relation.save
    rescue StandardError => e
      Rails.logger.warn "[#{self.class.name}] Error copying polymorphic relation: #{e.message}"
    end

    def reindex_job(new_job)
      new_job.reindex if new_job.respond_to?(:reindex)
    end

    def broadcast_progress(current:, total:, copied_job_ids:, elapsed_time:)
      percent = (current * 100.0 / total).round(2)
      estimated_time = ((elapsed_time / current) * (total - current)).round(2)

      ActionCable.server.broadcast(
        "job_copy:#{user_id}_job_copy_collection",
        {
          status: "loading",
          percent: percent,
          current: current,
          total: total,
          copied_job_ids: copied_job_ids,
          elapsed_time: elapsed_time,
          estimated_time: estimated_time
        }
      )

      Rails.logger.info "[#{self.class.name}] 📨 Broadcasting progress: #{percent}% (#{current}/#{total})"
    end

    def broadcast_completion(total:, copied_job_ids:, total_time:)
      sleep(0.5) unless Rails.env.test?

      ActionCable.server.broadcast(
        "job_copy:#{user_id}_job_copy_collection",
        {
          status: "completed",
          percent: 100,
          total: total,
          copied_job_ids: copied_job_ids,
          total_time: total_time
        }
      )

      Rails.logger.info "[#{self.class.name}] ✅ Broadcasting completion: #{total} jobs created"
    end

    def broadcast_error(message)
      ActionCable.server.broadcast(
        "job_copy:#{user_id}_job_copy_collection",
        {
          status: "error",
          percent: 0,
          error_message: message
        }
      )

      Rails.logger.error "[#{self.class.name}] ❌ Broadcasting error: #{message}"
    end

    def success_result(job, count)
      {
        success: true,
        job: job,
        count: count
      }
    end

    def error_result(message)
      {
        success: false,
        job: nil,
        count: 0,
        error: message
      }
    end

    # Relationships that have a direct foreign key to Job
    DIRECT_RELATIONSHIPS = %i[
      selective_processes
    ].freeze

    # Polymorphic relationships (reference_type + reference_id)
    POLYMORPHIC_RELATIONSHIPS = %i[
      skill_relationships
      benefit_relationships
      remuneration_relationships
      language_relationships
      list_relationships
    ].freeze
  end
end
