# frozen_string_literal: true

module TagReplacer
  module Resolvers
    class MethodResolver < BaseResolver
      def resolve(context, tag_definition)
        entity = context.fetch(tag_definition.entity)
        return "-" unless entity

        method_name = tag_definition.extra[:method_name]

        unless Sanitizer.allowed_method?(method_name)
          raise InvalidMethodError, "Method #{method_name} is not allowed"
        end

        unless entity.respond_to?(method_name)
          raise ResolutionError, "#{tag_definition.entity} does not respond to #{method_name}"
        end

        format_value(entity.public_send(method_name))
      end
    end
  end
end
