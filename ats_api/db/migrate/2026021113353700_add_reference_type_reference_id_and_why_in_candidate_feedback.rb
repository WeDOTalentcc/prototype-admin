class AddReferenceTypeReferenceIdAndWhyInCandidateFeedback < ActiveRecord::Migration[7.1]
  def change
    add_column :candidate_feedbacks, :reference_type, :string if not column_exists?(:candidate_feedbacks, :reference_type)
    add_column :candidate_feedbacks, :reference_id, :bigint if not column_exists?(:candidate_feedbacks, :reference_id)
    add_column :candidate_feedbacks, :reason, :text if not column_exists?(:candidate_feedbacks, :reason)
  end
end
