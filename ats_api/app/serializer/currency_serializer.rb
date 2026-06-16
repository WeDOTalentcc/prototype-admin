class CurrencySerializer
  include JSONAPI::Serializer

  set_type :currency
  attributes :name
end
