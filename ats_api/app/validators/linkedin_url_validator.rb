# frozen_string_literal: true

class LinkedinUrlValidator
  LINKEDIN_PATTERNS = [
    %r{\Ahttps?://(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]{3,100}/?\z},
    %r{\Alinkedin\.com/in/[a-zA-Z0-9_-]{3,100}/?\z},
    %r{\A(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]{3,100}/?\z},
    %r{\A[a-zA-Z0-9_-]{3,100}\z}
  ].freeze

  attr_reader :url

  def initialize(url)
    @url = url&.to_s&.strip
  end

  def valid?
    return false if url.blank?
    LINKEDIN_PATTERNS.any? { |pattern| url.match?(pattern) }
  end

  def self.valid?(url)
    new(url).valid?
  end
end
