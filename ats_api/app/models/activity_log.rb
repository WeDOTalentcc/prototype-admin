class ActivityLog < ApplicationRecord
  include Searchable

  belongs_to :user, optional: true
  belongs_to :account, optional: true

  def search_data
    attributes.except("changeset").merge(
      user_name: user&.name,
      account_name: account&.name
    )
  end

  def self.log_change(record, user:, action:, changeset:, account:, ip: nil, category: "others")
    create!(
      reference_type: record.class.name,
      reference_id: record.id,
      action: action,
      changeset: changeset,
      category: category,
      user: user,
      account: account || user&.account,
      ip_address: ip,
    )
  end

  def rollback!(current_user:)
    raise "Rollback only allowed for update actions" unless action == "update"

    record = reference_type.constantize.find_by(id: reference_id)
    raise ActiveRecord::RecordNotFound, "Record not found" unless record

    prev_values = changeset.transform_values do |v|
      if v.is_a?(Array)
        v[0]
      elsif v.is_a?(Hash) && v.key?("from")
        v["from"]
      else
        v
      end
    end

    record.update_columns(prev_values.merge(updated_at: Time.current))

    inverted_changeset = changeset.transform_values do |v|
      if v.is_a?(Array)
        { "from" => v[1], "to" => v[0] }
      elsif v.is_a?(Hash) && v.key?("from") && v.key?("to")
        { "from" => v["to"], "to" => v["from"] }
      else
        v
      end
    end

    self.class.create!(
      reference_type: reference_type,
      reference_id: reference_id,
      action: "rollback",
      changeset: inverted_changeset,
      user: current_user,
      account: current_user&.account,
      rolled_back_from_id: id
    )
  end
end
