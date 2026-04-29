# frozen_string_literal: true

class SectorRelationshipSerializer
  include JSONAPI::Serializer

  set_type :sector_relationship
  set_id :id

  attributes :sector_id,
             :sector_name,
             :reference_type,
             :reference_id,
             :account_id,
             :is_deleted,
             :created_at,
             :updated_at

  attribute :sector do |object|
    if object.sector
      {
        id: object.sector.id,
        name: object.sector.name,
        level: object.sector.level,
        icon: object.sector.icon
      }
    end
  end
end
