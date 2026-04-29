class ContractTypeSerializer
  include JSONAPI::Serializer

  set_type :contract_type
  attributes :name
end
