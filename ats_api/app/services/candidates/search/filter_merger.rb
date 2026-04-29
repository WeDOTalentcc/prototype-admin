module Candidates
  module Search
    class FilterMerger
      LockedFilterOverrideAttempt = Class.new(SecurityError)

      class << self
        def merge(base_filters, user_filters, warn_on_override: true)
          locked = Configuration.locked_filters

          attempted_overrides = user_filters.keys.map(&:to_sym) & locked

          if attempted_overrides.any? && warn_on_override
            Rails.logger.warn({
              event: "locked_filter_override_attempt",
              attempted: attempted_overrides,
              ignored: true
            }.to_json)
          end

          safe_user_filters = user_filters.reject { |k, _| locked.include?(k.to_sym) }

          safe_user_filters.merge(base_filters)
        end

        def whitelist_for_pgvector(user_filters)
          allowed = Configuration.pgvector_allowed_filters
          filtered = user_filters.select { |k, _| allowed.include?(k.to_sym) }

          filtered
        end
      end
    end
  end
end
