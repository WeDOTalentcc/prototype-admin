# frozen_string_literal: true

module Taxonomy
  # Loads config/taxonomy/candidates.yml for curated search hints (no PII).
  class CandidateCatalog
    # Mirrors full taxonomy export from lia-agent-system/app/core/taxonomy.py
    PER_CATEGORY_LIMIT = 10_000
    DEFAULT_CATEGORIES = %w[job_titles skills certifications industries].freeze

    def self.version
      path = Rails.root.join("config/taxonomy/candidates.yml")
      return "unknown" unless path.file?

      YAML.load_file(path).fetch("version", "unknown")
    end

    def self.hints_for(q:, categories:)
      new.hints_for(q: q, categories: categories)
    end

    def hints_for(q:, categories:)
      categories = DEFAULT_CATEGORIES if categories.blank?
      qnorm = q.to_s.downcase.strip
      out = {}

      categories.each do |cat|
        case cat.to_s.downcase
        when "job_titles"
          out[:job_titles] = filter_grouped(data[:job_titles] || {}, qnorm, limit: PER_CATEGORY_LIMIT)
        when "skills"
          out[:skills] = filter_grouped(data[:skills] || {}, qnorm, limit: PER_CATEGORY_LIMIT)
        when "certifications"
          out[:certifications] = filter_grouped(data[:certifications] || {}, qnorm, limit: PER_CATEGORY_LIMIT)
        when "industries"
          out[:industries] = filter_grouped(data[:industries] || {}, qnorm, limit: PER_CATEGORY_LIMIT)
        end
      end

      out
    end

    private

    def data
      @data ||= load_yaml.deep_symbolize_keys
    end

    def load_yaml
      path = Rails.root.join("config/taxonomy/candidates.yml")
      raise "Missing #{path}" unless path.file?

      YAML.load_file(path)
    end

    # grouped_hash: { "group_key" => ["term", ...] }
    def filter_grouped(grouped_hash, qnorm, limit:)
      return [] unless grouped_hash.is_a?(Hash)

      items = []
      grouped_hash.each do |group, titles|
        Array(titles).each do |text|
          next if text.blank?
          next if qnorm.present? && !text.to_s.downcase.include?(qnorm)

          items << { "text" => text.to_s, "group" => group.to_s }
          return items if items.size >= limit
        end
      end

      items
    end
  end
end
