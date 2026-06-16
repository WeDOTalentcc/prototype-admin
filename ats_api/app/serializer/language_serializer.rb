class LanguageSerializer
  include JSONAPI::Serializer

  attributes :id, :name, :acronym, :name_ptbr, :created_at, :updated_at
end
