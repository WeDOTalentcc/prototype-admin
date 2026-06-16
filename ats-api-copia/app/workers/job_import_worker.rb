class JobImportWorker
  include Sneakers::Worker

  from_queue 'jobs_import',
    durable: true,
    ack: true,
    retry_max_times: 5,
    arguments: {
      'x-dead-letter-exchange' => 'dead_jobs_import'
    }

  def work(raw_message)
    begin
      payload = JSON.parse(raw_message)
      job_data = payload["payload"]

      account_id = job_data["account_id"]
      user_id = job_data["user_id"]

      unless account_id.present?
        Sneakers.logger.error "Rejecting job import: missing account_id in payload"
        return reject!
      end

      unless user_id.present?
        Sneakers.logger.error "Rejecting job import: missing user_id in payload (account_id=#{account_id})"
        return reject!
      end

      job_attrs = {
        provider: job_data["provider"],
        provider_job_id: job_data["provider_job_id"],
        title: job_data["name"],
        description: job_data["description"],
        company_id: job_data["company_id"],
        published_date: job_data["published_date"],
        application_deadline: job_data["application_deadline"],
        is_remote: job_data["is_remote"],
        city: job_data["city"],
        state: job_data["state"],
        country: job_data["country"],
        job_url: job_data["job_url"],
        career_page_id: job_data["career_page_id"],
        career_page_name: job_data["career_page_name"],
        career_page_url: job_data["career_page_url"],
        career_page_logo: job_data["career_page_logo"],
        friendly_badge: job_data["friendly_badge"],
        disabilities: job_data["disabilities"],
        workplace_type: job_data["workplace_type"],
        user_id: user_id,
        account_id: account_id
      }

      job = Job.find_or_initialize_by(
        provider: job_attrs[:provider],
        provider_job_id: job_attrs[:provider_job_id]
      )

      job.assign_attributes(job_attrs)

      if job.save
        Sneakers.logger.info "Job saved: id=#{job.id} account_id=#{account_id}"
        ack!
      else
        Sneakers.logger.error "Job save failed: #{job.errors.full_messages}"
        reject!
      end
    rescue => e
      Sneakers.logger.error "Job import error: #{e.message}"
      reject!
    end
  end
end
