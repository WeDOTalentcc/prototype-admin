# frozen_string_literal: true

module TagReplacer
  module Resolvers
    class UrlResolver < BaseResolver
      URL_BUILDERS = {
        candidate_access: ->(ctx, _) { build_candidate_access_url(ctx) }
      }.freeze

      def resolve(context, tag_definition)
        url_type = tag_definition.extra[:url_type]
        builder = URL_BUILDERS[url_type]

        raise ResolutionError, "Unknown url_type: #{url_type}" unless builder

        builder.call(context, tag_definition) || "-"
      end

      private

      def self.build_candidate_access_url(ctx)
        candidate = ctx.fetch(:candidate)
        return nil unless candidate

        "#{ENV.fetch('CANDIDATE_PORTAL_URL', 'http://localhost:3001')}/access/#{candidate.access_token}" if candidate.respond_to?(:access_token)
      end
    end
  end
end
