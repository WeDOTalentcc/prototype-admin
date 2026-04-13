module AccountScopable
  extend ActiveSupport::Concern

  included do
    before_validation :assign_account
  end

  private

  def assign_account
    if new_record? && respond_to?(:account_id) && account_id.blank?
      self.account_id = Current.user.account_id if Current.user.present?
    end
  end
end
