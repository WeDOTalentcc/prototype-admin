class AddCountryIdOnCities < ActiveRecord::Migration[7.1]
  def change
    if ActiveRecord::Base.connection.table_exists? 'accounts'
      add_reference :cities, :country
    end
  end
end
