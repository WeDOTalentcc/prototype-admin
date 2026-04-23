class AddCandidateIdToExperiences < ActiveRecord::Migration[7.1]
  def up
    add_reference :experiences, :candidate, null: true, index: true, foreign_key: true unless column_exists?(:experiences, :candidate_id)

    execute <<~SQL
      UPDATE experiences
      SET candidate_id = reference_id
      WHERE candidate_id IS NULL AND reference_type = 'Candidate'
    SQL

    change_column_null :experiences, :candidate_id, false

    remove_column :experiences, :reference_type if column_exists?(:experiences, :reference_type)
    remove_column :experiences, :reference_id if column_exists?(:experiences, :reference_id)
  end

  def down
    add_column :experiences, :reference_type, :string unless column_exists?(:experiences, :reference_type)
    add_column :experiences, :reference_id, :bigint unless column_exists?(:experiences, :reference_id)

    execute <<~SQL
      UPDATE experiences
      SET reference_type = 'Candidate', reference_id = candidate_id
      WHERE reference_type IS NULL OR reference_id IS NULL
    SQL

    change_column_null :experiences, :reference_type, false
    change_column_null :experiences, :reference_id, false

    remove_reference :experiences, :candidate, foreign_key: true if column_exists?(:experiences, :candidate_id)
  end
end
