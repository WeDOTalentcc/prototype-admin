module Hideable
  extend ActiveSupport::Concern

  def inject_hide(params_entity, object_current)
    return params_entity.except(:hide) unless params_entity.key?(:hide)

    params_entity[:hide_user_ids] = update_hide_user_ids(
      object_current.hide_user_ids || [],
      params_entity[:hide]
    )

    params_entity.except(:hide)
  end

  def inject_hide_status_for_response(items, current_user)
    items.map do |item|
      item.as_json.merge("is_hidden" => hidden?(item, current_user))
    end
  end

  private

  def update_hide_user_ids(current_ids, should_hide)
    return (current_ids + [ @current_user.id ]).uniq if should_hide

    current_ids - [ @current_user.id ]
  end

  def hidden?(item, current_user)
    return false unless item.respond_to?(:hide_user_ids)

    item.hide_user_ids&.include?(current_user.id) || false
  end
end
