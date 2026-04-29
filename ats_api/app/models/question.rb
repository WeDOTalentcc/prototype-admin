class Question < ApplicationRecord
  include Searchable
  belongs_to :evaluation
  belongs_to :selective_process, -> { unscope(where: :is_deleted) }, optional: true
  belongs_to :parent_question, class_name: "Question", optional: true
  has_many :sub_questions, class_name: "Question", foreign_key: "parent_question_id", dependent: :nullify

  after_commit :refresh_parent_evaluation_questions_hash

  validates :title, presence: true
  validates :response_type, presence: true
  validates :validation_type_weight, numericality: { greater_than_or_equal_to: 0, less_than_or_equal_to: 1 }, allow_nil: true
  validate :framework_weights_must_be_hash

  private

  def refresh_parent_evaluation_questions_hash
    eids = [ evaluation_id ]
    eids.concat(previous_changes["evaluation_id"]) if previous_changes.key?("evaluation_id")
    eids.compact.uniq.each do |eid|
      Evaluation.find_by(id: eid)&.refresh_questions_hash!
    end
  end

  def framework_weights_must_be_hash
    return if framework_weights.is_a?(Hash)

    errors.add(:framework_weights, "must be a JSON object")
  end
end
