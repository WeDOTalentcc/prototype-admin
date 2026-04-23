# app/models/concerns/has_activity_log.rb
module HasActivityLog
  extend ActiveSupport::Concern

  included do
    attr_accessor :activity_log_category_override

    has_many :activity_logs, as: :reference, dependent: :destroy

    after_create  { log_activity("create", "log") }
    after_update  { log_activity("update", resolve_category) if saved_changes? }
    after_destroy { log_activity("destroy", "log") }
  end

  def log_activity_with_category(category)
    self.activity_log_category_override = category
    yield
  ensure
    self.activity_log_category_override = nil
  end

  def log_activity(action, category = "others")
    relevant_changes = previous_changes.except(:updated_at, :created_at).select do |_key, change_array|
      change_array[0] != change_array[1]
    end

    formatted_changeset = relevant_changes.transform_values do |change_array|
      { "from" => change_array[0], "to" => change_array[1] }
    end

    formatted_changeset = enrich_activity_log_changeset(formatted_changeset) if respond_to?(:enrich_activity_log_changeset, true)

    return if formatted_changeset.empty?

    ActivityLog.log_change(
      self,
      user: Current.user,
      action: action,
      category: category,
      changeset: formatted_changeset,
      account: Current.user&.account,
      ip: Current.ip,
    )
  end

  private

  def resolve_category
    activity_log_category_override || "log"
  end
end
