# frozen_string_literal: true

class SectorSerializer
  include JSONAPI::Serializer

  set_type :sector
  set_id :id

  attributes :name, :description, :icon, :tags, :level, :is_public, :is_deleted, :created_at, :updated_at

  attribute :parent_sector_id
  attribute :account_id

  attribute :parent_sector do |object|
    if object.parent_sector
      {
        id: object.parent_sector.id,
        name: object.parent_sector.name,
        icon: object.parent_sector.icon
      }
    end
  end

  attribute :children_count do |object|
    object.child_sectors.size
  end

  attribute :has_children do |object|
    object.child_sectors.any?
  end

  attribute :full_path do |object|
    object.full_path
  end

  attribute :ancestors do |object, params|
    next [] unless params && params[:extra_params]&.dig(:include_ancestors)

    object.ancestors.map do |ancestor|
      {
        id: ancestor.id,
        name: ancestor.name,
        icon: ancestor.icon,
        level: ancestor.level
      }
    end
  end

  attribute :children do |object, params|
    next [] unless params && params[:extra_params]&.dig(:include_children)

    object.child_sectors.map do |child|
      {
        id: child.id,
        name: child.name,
        icon: child.icon,
        level: child.level,
        tags: child.tags,
        children_count: child.child_sectors.size
      }
    end
  end

  attribute :siblings do |object, params|
    next [] unless params && params[:extra_params]&.dig(:include_siblings)

    object.siblings.map do |sibling|
      {
        id: sibling.id,
        name: sibling.name,
        icon: sibling.icon,
        level: sibling.level
      }
    end
  end
end
