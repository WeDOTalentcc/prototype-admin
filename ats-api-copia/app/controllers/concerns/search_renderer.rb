module SearchRenderer
  extend ActiveSupport::Concern

  def perform_search(
    model:,
    serializer:,
    term: params[:term],
    search_params: nil,
    page: params[:page],
    pinned_first: term.blank?,
    current_user_id: @current_user.id,
    search_with_pin: nil
  )
    results = model.search_default(
      term || search_params,
      search_with_pin,
      page,
      pinned_first,
      false
    )

    render json: serializer.new(results[:records], {
      meta: {
        total: results[:total_count],
        aggregators: results[:aggs]
      }
    }).serializable_hash
  end
end
