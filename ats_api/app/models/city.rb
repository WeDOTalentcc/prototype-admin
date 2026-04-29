class City < ApplicationRecord
  include Searchable

  enable_autocomplete :city_state, :name

  belongs_to :state
  belongs_to :country

  def search_data
    {
      id: id,
      name: name,
      state_id: state_id,
      country_id: country_id,
      city_state: "#{name}, #{state&.name}"
    }
  end
end
