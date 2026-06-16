class JobUserSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :user_id,
    :job_id,
    :account_id,
    :person_function,
    :split,
    :created_at,
    :updated_at
  )

  attribute :user_name do |object|
    if object.respond_to?(:user_name)
      object[:user_name]
    else
      object.user&.name
    end
  end

  attribute :user_email do |object|
    if object.respond_to?(:user_email)
      object[:user_email]
    else
      object.user&.email
    end
  end

  attribute :job_title do |object|
    if object.respond_to?(:job_title)
      object[:job_title]
    else
      object.job&.title
    end
  end

  attribute :user do |job_user|
    next unless job_user.user

    {
      id: job_user.user_id,
      name: job_user.user.name,
      email: job_user.user.email
    }
  end

  attribute :job do |job_user|
    next unless job_user.job

    {
      id: job_user.job_id,
      title: job_user.job.title
    }
  end
end
