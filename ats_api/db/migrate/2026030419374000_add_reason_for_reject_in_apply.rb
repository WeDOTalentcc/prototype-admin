class AddReasonForRejectInApply < ActiveRecord::Migration[7.1]
  def change
    add_column :applies, :reason_for_reject, :text if not column_exists?(:applies, :reason_for_reject)
  end
end
