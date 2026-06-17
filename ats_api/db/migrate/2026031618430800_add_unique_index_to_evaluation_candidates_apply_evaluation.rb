class AddUniqueIndexToEvaluationCandidatesApplyEvaluation < ActiveRecord::Migration[7.1]
  def up
    execute <<~SQL
      DELETE FROM evaluation_candidates
      WHERE id NOT IN (
        SELECT MIN(id)
        FROM evaluation_candidates
        WHERE apply_id IS NOT NULL AND is_deleted = false
        GROUP BY apply_id, evaluation_id
      )
      AND apply_id IS NOT NULL
      AND is_deleted = false
    SQL

    add_index :evaluation_candidates, [ :apply_id, :evaluation_id ],
              unique: true,
              where: "apply_id IS NOT NULL AND is_deleted = false",
              name: "idx_evaluation_candidates_apply_evaluation_uniq",
              if_not_exists: true
  end

  def down
    remove_index :evaluation_candidates,
                 name: "idx_evaluation_candidates_apply_evaluation_uniq",
                 if_exists: true
  end
end
