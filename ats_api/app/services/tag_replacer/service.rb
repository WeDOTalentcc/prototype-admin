# frozen_string_literal: true

module TagReplacer
  class Service
    def self.call(message, record:, recruiter_id: nil, options: {})
      return "" if message.blank?

      new(message, record: record, recruiter_id: recruiter_id, options: options).execute
    end

    def execute
      resolved_cache = {}

      Registry.tags_in(message).each do |tag_definition|
        tag_string = tag_definition.tag
        next unless message.include?(tag_string)

        resolved_cache[tag_string] ||= resolve(tag_definition)
        message.gsub!(tag_string, resolved_cache[tag_string].to_s)
      end

      message
    end

    private

    attr_reader :message, :context, :options

    def initialize(message, record:, recruiter_id:, options: {})
      @message = message.dup
      @context = Context.new(record, recruiter_id)
      @options = options
    end

    def resolve(tag_definition)
      resolver = ResolverFactory.for(tag_definition)
      resolver.resolve(context, tag_definition)
    rescue TagReplacer::ResolutionError => e
      Rails.logger.warn("[TagReplacer] Failed to resolve #{tag_definition.tag}: #{e.message}")
      options[:fallback] || tag_definition.tag
    end
  end
end
