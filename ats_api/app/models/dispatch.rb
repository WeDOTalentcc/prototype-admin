class Dispatch < ApplicationRecord
  include TracksJobAnalytics

  belongs_to :account
  belongs_to :user
  belongs_to :reference, polymorphic: true, optional: true

  has_many :dispatch_messages, dependent: :destroy
  has_one :email_followup_status, dependent: :destroy

  enum status: { pending: 0, processing: 1, completed: 2, failed: 3 }

  alias_method :target, :reference

  def self.replace_tags(content, entities)
    ActiveSupport::Deprecation.warn(
      "Dispatch.replace_tags is deprecated. Use TagReplacer::Service.call instead."
    )
    TagReplacer::Service.call(content, record: entities)
  end

  def self.tag_array
    {
      candidate: [
        { text: "Candidate - email", tag: "{{candidate_email}}", field: "email" },
        { text: "Candidate - name", tag: "{{candidate_name}}", field: "name" }
      ],
      user: [
        { text: "User - email", tag: "{{user_email}}", field: "email" },
        { text: "User - name", tag: "{{user_name}}", field: "name" }
      ],
      job: [
        { text: "Job - title", tag: "{{job_title}}", field: "title" },
        { text: "Job - description", tag: "{{job_description}}", field: "description" },
        { text: "Job - salary from", tag: "{{job_salary_from}}", field: "salary_from" },
        { text: "Job - salary to", tag: "{{job_salary_to}}", field: "salary_to" }
      ],
      account: [
        { text: "Account - name", tag: "{{account_name}}", field: "name" }
      ]
    }
  end

  def self.custom_replace_tags
    [
      { text: "Evaluation Candidate - URL", tag: "{{evaluation_candidate_url}}", method: "get_evaluation_candidate_url", entity: "EvaluationCandidate" }
    ]
  end
end
