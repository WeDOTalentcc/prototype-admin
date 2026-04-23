# frozen_string_literal: true

module Sourcings
  class FirstBatchPageSize
    BASE = 10

    def self.for_sourcing(sourcing)
      return BASE unless hybrid_local_and_global?(sourcing)

      BASE / 2
    end

    def self.hybrid_local_and_global?(sourcing)
      return false unless sourcing&.parameters.is_a?(Hash)

      sources = Array(sourcing.parameters["sources"]).map(&:to_s)
      sources.include?("local") && sources.include?("global")
    end
  end
end
