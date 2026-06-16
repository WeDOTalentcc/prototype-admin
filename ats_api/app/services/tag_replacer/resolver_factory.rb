# frozen_string_literal: true

module TagReplacer
  class ResolverFactory
    RESOLVERS = {
      attribute: Resolvers::AttributeResolver,
      method: Resolvers::MethodResolver,
      date: Resolvers::DateResolver,
      url: Resolvers::UrlResolver
    }.freeze

    def self.for(tag_definition)
      resolver_class = RESOLVERS[tag_definition.resolver_type]

      raise ResolutionError, "No resolver for type: #{tag_definition.resolver_type}" unless resolver_class

      resolver_class.new
    end
  end
end
