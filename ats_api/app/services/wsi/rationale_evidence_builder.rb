# frozen_string_literal: true

module Wsi
  class RationaleEvidenceBuilder
    MIN_EVIDENCES = 2
    MIN_EXCERPT_LENGTH = 3

    EXCERPT_PATTERNS = [
      /excerpt:\s*"([^"]*)"/i,
      /excerpt:\s*'([^']*)'/i,
      /trecho:\s*"([^"]*)"/i,
      /trecho:\s*'([^']*)'/i
    ].freeze

    def self.call(extraction:, source_text:)
      new(extraction: extraction, source_text: source_text).call
    end

    def initialize(extraction:, source_text:)
      @extraction = extraction.deep_symbolize_keys
      @source = source_text.to_s
    end

    def call
      ordered = verified_ordered_strings
      return [] if ordered.size < MIN_EVIDENCES

      ordered
    end

    private

    def verified_ordered_strings
      candidates = collect_candidates.uniq
      verified = candidates.select do |s|
        s.length >= MIN_EXCERPT_LENGTH && substring_of_source?(s)
      end
      drop_substrings_contained_in_longer(verified).sort_by { |s| @source.index(s) || 0 }
    end

    def collect_candidates
      out = []
      Array(@extraction[:rationale]).each { |s| out << s.to_s.strip }
      Array(@extraction[:trait_signals_detected]).each { |line| out.concat(excerpts_from_trait_line(line)) }
      kq = normalize_key_quote(@extraction[:key_quote])
      out << kq if kq.present?
      out.compact.map(&:strip).reject(&:blank?)
    end

    def excerpts_from_trait_line(line)
      text = line.to_s
      found = []
      EXCERPT_PATTERNS.each do |re|
        text.scan(re) { |m| found << Regexp.last_match(1) }
      end
      found
    end

    def normalize_key_quote(raw)
      s = raw.to_s.strip
      s = s.delete_prefix('"').delete_prefix("'").delete_suffix('"').delete_suffix("'").strip
      s
    end

    def substring_of_source?(fragment)
      return false if fragment.blank?

      @source.include?(fragment)
    end

    def drop_substrings_contained_in_longer(strings)
      uniq = strings.uniq
      uniq.reject do |s|
        uniq.any? { |other| other != s && other.include?(s) }
      end
    end
  end
end
