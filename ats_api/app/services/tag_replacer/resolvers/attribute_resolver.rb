# frozen_string_literal: true

module TagReplacer
  module Resolvers
    class AttributeResolver < BaseResolver
      def resolve(context, tag_definition)
        entity = context.fetch(tag_definition.entity)
        return "-" unless entity

        attribute = tag_definition.attribute
        unless entity.respond_to?(attribute)
          raise ResolutionError, "#{tag_definition.entity} does not respond to #{attribute}"
        end

        format_value(entity.public_send(attribute))
      end
    end
  end
end
