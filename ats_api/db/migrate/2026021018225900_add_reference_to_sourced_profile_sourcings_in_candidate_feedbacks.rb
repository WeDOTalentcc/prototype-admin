class AddReferenceToSourcedProfileSourcingsInCandidateFeedbacks < ActiveRecord::Migration[7.1]
  def change
    add_reference :candidate_feedbacks, :sourced_profile_sourcing, foreign_key: true if not column_exists?(:candidate_feedbacks, :sourced_profile_sourcing_id)
    add_index :candidate_feedbacks, :sourced_profile_sourcing_id if not index_exists?(:candidate_feedbacks, :sourced_profile_sourcing_id)
  end
end
