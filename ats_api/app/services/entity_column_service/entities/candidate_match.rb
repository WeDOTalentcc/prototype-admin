# frozen_string_literal: true

module EntityColumnService
  module Entities
    class CandidateMatch < Candidate
      def self.structure
        base = super.deep_dup

        score_col = {
          value:    "score",
          text:     "Match",
          sortable: true,
          type:     "Score",
          width:    "auto",
          filter:   "score"
        }

        idx = base.index { |c| c[:value] == "name" } || 0
        base.insert(idx + 1, score_col)

        base
      end

      def self.shortlists
        base = super.deep_dup

        score_col = {
          value:    "score",
          text:     "Match",
          sortable: true,
          type:     "DynamicTextSimple",
          width:    "auto"
        }

        idx = base.index { |c| c[:value] == "name" } || 0
        base.insert(idx + 1, score_col)

        base
      end
    end
  end
end
