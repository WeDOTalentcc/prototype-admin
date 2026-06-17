require "nokogiri"

module Emails
  class UrlTrackingService
    def self.wrap_links(html_content, base_tracking_url)
      return html_content if base_tracking_url.blank? || html_content.blank?

      doc = Nokogiri::HTML::DocumentFragment.parse(html_content)
      doc.css("a[href]").each do |link|
        original_url = link["href"]
        next if skip_tracking?(original_url)

        tracked_url = "#{base_tracking_url}?url=#{CGI.escape(original_url)}"
        link["href"] = tracked_url
      end

      doc.to_html
    end

    def self.skip_tracking?(url)
      url.blank? || url.start_with?("mailto:", "tel:", "sms:", "#") || url.include?("unsubscribe")
    end
  end
end
