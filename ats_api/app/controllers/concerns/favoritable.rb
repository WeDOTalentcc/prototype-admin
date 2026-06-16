module Favoritable
  extend ActiveSupport::Concern

  def inject_favorite(params_entity, object_current)
    return params_entity.except(:favorite) unless params_entity.key?(:favorite)

    params_entity[:favorite_user_ids] = update_user_ids(
      object_current.favorite_user_ids || [],
      params_entity[:favorite]
    )

    params_entity.except(:favorite)
  end

  def inject_favorite_status_for_response(items, current_user)
    items.map do |item|
      item.as_json.merge("is_favorited" => favorited?(item, current_user))
    end
  end

  private

  def update_user_ids(current_ids, should_favorite)
    return (current_ids + [ @current_user.id ]).uniq if should_favorite

    current_ids - [ @current_user.id ]
  end

  def favorited?(item, current_user)
    return false unless item.respond_to?(:favorite_user_ids)

    item.favorite_user_ids&.include?(current_user.id) || false
  end
end
