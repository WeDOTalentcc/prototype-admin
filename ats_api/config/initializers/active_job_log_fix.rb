module ActiveJob
  class LogSubscriber < ActiveSupport::LogSubscriber
    def perform_start(event)
      info do
        job = event.payload[:job]

        # Handle nil scheduled_at
        scheduled_at = job.scheduled_at ? job.scheduled_at.utc.iso8601(9) : "immediately"

        "Performing #{job.class.name} (Job ID: #{job.job_id}) from #{queue_name(event)} enqueued at #{job.enqueued_at} with arguments: #{args_info(job)}" +
          (job.scheduled_at ? " (scheduled at #{scheduled_at})" : "")
      end
    end
  end
end
