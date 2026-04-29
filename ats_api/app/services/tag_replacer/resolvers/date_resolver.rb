# frozen_string_literal: true

module TagReplacer
  module Resolvers
    class DateResolver < BaseResolver
      def resolve(context, tag_definition)
        format = tag_definition.extra[:format]

        case format
        when :en then I18n.l(Date.current, format: :long, locale: :en)
        when :br then I18n.l(Date.current, format: :long, locale: :"pt-BR")
        else Date.current.to_s
        end
      end
    end
  end
end
