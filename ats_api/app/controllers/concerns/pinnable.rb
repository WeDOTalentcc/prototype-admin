module Pinnable
  extend ActiveSupport::Concern

  def inject_pin_and_confidential(params_entity, object_current)
    params_entity = inject_array_ids(params_entity, object_current, :pin_user_ids) if params_entity[:pin]
    if params_entity[:pin] == false
      params_entity = remove_array_ids(params_entity, object_current, :pin_user_ids)
    end

    if params_entity[:confidential]
      params_entity = inject_array_ids(params_entity, object_current, :confidential_user_ids)
    end

    if params_entity[:confidential] == false
      params_entity = remove_array_ids(params_entity, object_current, :confidential_user_ids)
    end

    params_entity.except(:pin, :confidential)
  end

  def inject_pin_status_for_response(items, current_user)
    items.map do |item|
      item_json = item.as_json

      # Add pin status
      if item.respond_to?(:pin_user_ids) && item.pin_user_ids
        item_json["is_pinned"] = item.pin_user_ids.include?(current_user.id)
      else
        item_json["is_pinned"] = false
      end

      if item.respond_to?(:confidential_user_ids) && item.confidential_user_ids
        item_json["is_confidential"] = item.confidential_user_ids.include?(current_user.id)
      end

      item_json
    end
  end

  private

  def inject_array_ids(params_entity, object_current, field)
    params_entity[field] = object_current[field] || []
    params_entity[field] << @current_user.id
    params_entity[field].uniq!
    params_entity
  end

  def remove_array_ids(params_entity, object_current, field)
    params_entity[field] = object_current[field] || []
    params_entity[field].delete @current_user.id if params_entity[field].present?
    params_entity[field].uniq! if params_entity[field].present?
    params_entity
  end
end
