class Feedback < ApplicationRecord
  include Searchable

  belongs_to :account
  belongs_to :job, optional: true
  belongs_to :apply, optional: true
  belongs_to :selective_process

  validates :title, presence: true
  validates :description, presence: true
  validates :name, presence: true

  def search_data
    {
      title: title,
      description: description,
      name: name,
      additional_text: additional_text,
      is_deleted: is_deleted,
      job_id: job_id,
      apply_id: apply_id,
      selective_process_id: selective_process_id,
      account_id: account_id,
      created_at: created_at,
      updated_at: updated_at
    }
  end

  def self.copy_feedback_by_job(previous_job_id, current_job)
    feedbacks = Feedback.where(job_id: previous_job_id)

    return if feedbacks.empty?

    feedbacks.each do |feedback|
      old_selective_process = feedback.selective_process
      new_selective_process = SelectiveProcess.where(
        job_id: current_job.id,
        status: old_selective_process.status
      ).first if old_selective_process

      Feedback.create(
        title: feedback.title,
        description: feedback.description,
        name: feedback.name,
        additional_text: feedback.additional_text,
        is_deleted: feedback.is_deleted,
        job_id: current_job.id,
        selective_process_id: new_selective_process.id,
        account_id: feedback.account_id
      ) if new_selective_process
    end
  end
end
