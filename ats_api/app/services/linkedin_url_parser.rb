# frozen_string_literal: true

class LinkedinUrlParser
  attr_reader :url

  def initialize(url)
    @url = url&.to_s&.strip
  end

  def username
    return nil if url.blank?

    return url unless url.include?("linkedin.com")

    match = url.match(%r{linkedin\.com/in/([a-zA-Z0-9_-]+)/?})
    match ? match[1] : nil
  end

  def self.extract_username(url)
    new(url).username
  end
end
