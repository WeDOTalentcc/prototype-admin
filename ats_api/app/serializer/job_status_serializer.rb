class JobStatusSerializer
  include JSONAPI::Serializer

  attributes :id, :name, :color, :created_at, :updated_at, :jobs_count, :is_main

  attribute :jobs_count do |job_status|
    job_status.jobs.count
  end
end
