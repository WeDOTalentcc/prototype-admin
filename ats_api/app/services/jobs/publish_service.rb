# frozen_string_literal: true

module Jobs
  class PublishService
    def initialize(job:)
      @job = job
    end

    def publish
      checker = FieldRequirementChecker.new(job)

      unless checker.is_ready_for_publication?
        return error(
          "Vaga não está pronta para publicação",
          missing_fields: checker.make_missing_fields
        )
      end

      active_status = JobStatus.find_by(name: "Ativa")

      attrs = {
        published_date: Time.current,
        is_active: true
      }
      attrs[:job_status_id] = active_status.id if active_status

      if job.update(attrs)
        success
      else
        error(job.errors.full_messages.join(", "))
      end
    end

    def unpublish
      draft_status = JobStatus.find_by(name: "Rascunho")

      attrs = {
        published_date: nil,
        is_active: false
      }
      attrs[:job_status_id] = draft_status.id if draft_status

      if job.update(attrs)
        success
      else
        error(job.errors.full_messages.join(", "))
      end
    end

    private

    attr_reader :job

    def success
      { success: true, job: job }
    end

    def error(message, missing_fields: nil)
      result = { success: false, error: message }
      result[:missing_fields] = missing_fields if missing_fields
      result
    end
  end
end
