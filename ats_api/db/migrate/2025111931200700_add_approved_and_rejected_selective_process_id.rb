class AddApprovedAndRejectedSelectiveProcessId < ActiveRecord::Migration[7.1]
  def change
    unless column_exists?(:evaluations, :approved_selective_process_id)
      add_reference :evaluations,
                    :approved_selective_process,
                    foreign_key: { to_table: :selective_processes },
                    null: true
    end

    unless column_exists?(:evaluations, :rejected_selective_process_id)
      add_reference :evaluations,
                    :rejected_selective_process,
                    foreign_key: { to_table: :selective_processes },
                    null: true
    end
  end
end
