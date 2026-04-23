# frozen_string_literal: true

module EntityColumnService
  module Entities
    class Base
      def self.structure
        raise NotImplementedError, "Subclasses must implement structure method"
      end

      def self.default
        structure
      end
    end
  end
end
