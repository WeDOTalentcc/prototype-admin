class Apply < ApplicationRecord
  include Searchable

  belongs_to :candidate
  belongs_to :job
  belongs_to :selective_process

  before_update :log_selective_process_change

  private

  def log_selective_process_change
    if will_save_change_to_selective_process_id?
      @apply_id = id
      ApplyStatus.create!(
        apply_id: @apply_id,
        selective_process_id: selective_process_id,
        status_id: nil,
        status_name: "Mudança de processo",
        comment: "",
        user_id: Current.user&.id,
        account_id: account_id
      )
    end
  end
end
