# frozen_string_literal: true

module TagReplacer
  module Resolvers
    class BaseResolver
      def resolve(context, tag_definition)
        raise NotImplementedError, "#{self.class}#resolve must be implemented"
      end

      private

      def format_value(value)
        case value
        when nil, "" then "-"
        when ActiveSupport::TimeWithZone, Time, DateTime
          value.strftime("%d/%m/%Y")
        else
          value.to_s
        end
      end
    end
  end
end
