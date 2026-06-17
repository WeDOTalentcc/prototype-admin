class FixEvaluationTypeDefault < ActiveRecord::Migration[7.1]
  def up
    execute "UPDATE evaluation_candidates SET evaluation_type = 0 WHERE evaluation_type IS NULL"

    change_column_default :evaluation_candidates, :evaluation_type, 0
    change_column_null :evaluation_candidates, :evaluation_type, false

    add_index :evaluation_candidates, :scheduling_link_id, if_not_exists: true
    add_index :evaluation_candidates, :interview_session_id, if_not_exists: true
    add_index :evaluation_candidates, :evaluation_type, if_not_exists: true
  end

  def down
    change_column_null :evaluation_candidates, :evaluation_type, true
    change_column_default :evaluation_candidates, :evaluation_type, nil

    remove_index :evaluation_candidates, :scheduling_link_id, if_exists: true
    remove_index :evaluation_candidates, :interview_session_id, if_exists: true
    remove_index :evaluation_candidates, :evaluation_type, if_exists: true
  end
end
