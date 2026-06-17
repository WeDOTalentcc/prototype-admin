module JobService
  class CopyJobCollection
    def self.make_copy_collection_by_amount(amount, job_id, user_id, entities)
      tenant = User.find(user_id).account.tenant
      Apartment::Tenant.switch!(tenant)
      return if amount.nil? || amount.zero?
      return if amount >= 100

      current_amount = 0
      amount.times do
        JobService::CopyJobCollection.save_job_copy(job_id, user_id, entities)
        sleep(0.2)
        current_amount += 1
        CollectionChannel.broadcast_to("#{user_id}_collection", {
                                         status: "loading",
                                         percent: current_amount * 10 / amount * 10
                                       })
      end
      sleep(0.3)
      CollectionChannel.broadcast_to("#{user_id}_collection", {
                                       status: "completed ", percent: 100
                                     })
    end

    def self.save_job_copy(job_id, user_id, entities)
      job = Job.where(id: job_id).first.dup

      raise "Job not found" if job.nil?

      job.title = job.title.to_s + " ##{Job.where(source_job_id: job_id).count + 1}"
      job.source_job_id = job_id
      job.save
      @job = job

      SelectiveProcess.make_a_copy_from_job(job_id, @job.id)

      RemunerationRelationship.create_remuneration_by(job_id, @job.id, "Job")

      Evaluation.create_evaluation_by_job(job_id, @job)

      Feedback.copy_feedback_by_job(job_id, @job)

      old_job = Job.find_by(id: job_id)

      if old_job
        JobService::CopyJobCollection.make_relationships(old_job, @job)
      end

      @job.tap { |copied_job| copied_job.reindex }
    end

    def self.make_polymorphic_relationships(old_job, job, entities = nil)
      ActiveRecord::Base.connection.tables.each do |table|
        model_name = table.singularize.camelize
        next if !entities.nil? && !entities.include?(model_name)

        next unless table.ends_with?("_relationships")
        next unless Object.const_defined?(model_name) && model_name.constantize < ApplicationRecord
        next if excluded_classes.include?(table)

        model_name.constantize.where(reference_type: "Job", reference_id: old_job.id).each do |object|
          next if object.respond_to?(:is_deleted) && object.is_deleted == true

          object_attr = object.attributes.except("id", "uid", "created_at", "updated_at")
          object_attr["reference_id"] = job.id
          object_created = model_name.constantize.create(object_attr)
          object_created.reindex if object_created.respond_to?(:reindex)
        end
      end
    end

    def self.make_relationships(old_job, job, entities = nil)
      ActiveRecord::Base.connection.tables.each do |table|
        model_name = table.singularize.camelize
        next if !entities.nil? && !entities.include?(model_name)

        next unless Object.const_defined?(model_name) && model_name.constantize < ApplicationRecord
        next unless ActiveRecord::Base.connection.column_exists?(table, "job_id")
        next if JobService::CopyJobCollection.excluded_classes.include?(table)
        next if table.ends_with?("_relationships")

        model_name.constantize.where(job_id: old_job.id).each do |object|
          next if object.respond_to?(:is_deleted) && object.is_deleted == true

          object_attr = object.attributes.except(
            "id", "uid", "created_at", "updated_at", "job_id", "sended_nps",
            "forecast_date", "billing", "billing_date", "dh_approved", "dh_approved_date", "po_number",
            "billed", "invoice", "issue", "maturity", "payment"
          )
          object_attr["job_id"] = job.id
          object_created = model_name.constantize.create(object_attr)
          object_created.reindex if object_created.respond_to?(:reindex)
        end
      end
    end

    def self.excluded_classes
      %w[
        experiences
        shortlist_candidates
        template_notes
        jobs
        placements
        selective_processes
        applies
        note_relationships
      ]
    end
  end
end
