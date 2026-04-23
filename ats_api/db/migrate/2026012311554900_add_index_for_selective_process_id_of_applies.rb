class AddIndexForSelectiveProcessIdOfApplies < ActiveRecord::Migration[7.1]
  def change
    unless index_exists?(:applies, [ :selective_process_id, :is_deleted ])
      add_index :applies, [ :selective_process_id, :is_deleted ],
                name: 'index_applies_on_selective_process_id_and_is_deleted'
    end

    unless index_exists?(:applies, [ :job_id, :is_deleted ])
      add_index :applies, [ :job_id, :is_deleted ],
                name: 'index_applies_on_job_id_and_is_deleted'
    end
  end
end
