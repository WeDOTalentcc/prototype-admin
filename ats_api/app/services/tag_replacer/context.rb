# frozen_string_literal: true

module TagReplacer
  class Context
    attr_reader :record, :recruiter_id

    def initialize(record, recruiter_id = nil)
      @record = record
      @recruiter_id = recruiter_id
      @cache = {}
    end

    def fetch(entity_key)
      return nil if entity_key.nil?
      @cache[entity_key] ||= resolve_entity(entity_key)
    end

    def preload(entity_keys)
      entity_keys.each { |key| fetch(key) }
    end

    def recruiter
      @cache[:recruiter] ||= User.find_by(id: recruiter_id) if recruiter_id
    end

    private

    def resolve_entity(key)
      return record[key] if record.is_a?(Hash) && record.key?(key)

      case key
      when :candidate then record[:candidate]
      when :job then record[:job]
      when :recruiter then recruiter
      when :user then record[:user] || recruiter
      when :client_contact then record[:client_contact]
      when :client_company then record[:client_company] || record[:job]&.client_company
      when :interview then record[:interview]
      when :business then record[:business] || current_business
      when :proposal then record[:proposal]
      when :experience then record[:experience]
      when :education then record[:education]
      when :evaluation_candidate then record[:evaluation_candidate]
      when :account then record[:account]
      else
        Rails.logger.debug("[TagReplacer::Context] Unknown entity key: #{key}")
        nil
      end
    end

    def current_business
      Business.current if defined?(Business) && Business.respond_to?(:current)
    end
  end
end
