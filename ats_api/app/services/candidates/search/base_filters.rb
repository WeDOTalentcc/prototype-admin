module Candidates
  module Search
    class BaseFilters
      def initialize(account_id:)
        @account_id = account_id
      end

      def to_hash
        base = {
          account_id: @account_id,
          is_deleted: false
        }

        # Require curriculum for quality search
        if Configuration.require_curriculum_text?
          base[:has_curriculum] = true
        end

        base.freeze
      end

      def base_scope(relation = Candidate)
        relation
          .where(account_id: @account_id)
          .where(is_deleted: false)
      end
    end
  end
end
