class AddressSerializer
  include JSONAPI::Serializer

  attributes :id, :city, :state, :country, :user_id, :account_id, :street, :number, :complement, :neighborhood, :zip_code,
             :title, :address_type, :description, :worksite, :bill_to, :sold_to, :created_at, :updated_at
end
