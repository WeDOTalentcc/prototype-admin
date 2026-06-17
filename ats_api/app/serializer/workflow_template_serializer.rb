class WorkflowTemplateSerializer
  include JSONAPI::Serializer

  attributes(
    :id,
    :name,
    :is_main,
    :is_deleted,
    :user_id,
    :account_id,
    :created_at,
    :updated_at
  )

  belongs_to :user

  attribute :selective_processes, if: proc { |_record, params|
    params[:includes]&.include?("selective_processes")
  } do |object, _params|
    job_id = _params[:extra_params]&.dig(:job_id) || nil
    object.selective_processes.where(job_id: job_id).order(position: :asc).map do |process|
      {
        id: process.id,
        name: process.name,
        status: process.status,
        position: process.position,
        sub_status: process.sub_status,
        job_id: process.job_id,
        position_x: process.position_x,
        position_y: process.position_y,
        childrens: process.childrens
      }
    end
  end
end
