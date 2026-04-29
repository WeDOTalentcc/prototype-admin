module Emails
  class TrackingPixelService
    GIF_1x1 = %(<img src="%{url}" width="1" height="1" border="0" alt="" style="display:none; width: 1px; height: 1px;">).freeze

    def self.inject_pixel(html_content, tracking_url)
      return html_content if tracking_url.blank? || html_content.blank?

      pixel = format(GIF_1x1, url: tracking_url)

      html_content.sub(%r{</body>}i, "#{pixel}</body>") || html_content + pixel
    end
  end
end
