# frozen_string_literal: true

require "open-uri"

module Candidates
  class AvatarDownloaderService
    attr_reader :candidate, :image_url

    def initialize(candidate, image_url)
      @candidate = candidate
      @image_url = image_url
    end

    def call
      return { success: false, error: "URL da imagem não informada" } if image_url.blank?
      return { success: false, error: "URL inválida" } unless valid_url?
      return { success: false, error: "Avatar já existe" } if candidate.avatar.attached?

      download_and_attach_avatar
    rescue OpenURI::HTTPError => e
      Rails.logger.error "[AvatarDownloaderService] HTTP Error: #{e.message}"
      { success: false, error: "Erro ao baixar imagem: #{e.message}" }
    rescue => e
      Rails.logger.error "[AvatarDownloaderService] Error: #{e.message}"
      Rails.logger.error e.backtrace.first(5).join("\n")
      { success: false, error: "Erro inesperado: #{e.message}" }
    end

    private

    def valid_url?
      uri = URI.parse(image_url)
      uri.is_a?(URI::HTTP) || uri.is_a?(URI::HTTPS)
    rescue URI::InvalidURIError
      false
    end

    def download_and_attach_avatar
      downloaded_image = URI.open(image_url, read_timeout: 10)
      filename = generate_filename
      content_type = detect_content_type(downloaded_image)

      candidate.avatar.attach(
        io: downloaded_image,
        filename: filename,
        content_type: content_type
      )

      Rails.logger.info "[AvatarDownloaderService] Avatar attached successfully for candidate ##{candidate.id}"
      { success: true, filename: filename }
    end

    def generate_filename
      extension = File.extname(URI.parse(image_url).path)
      extension = ".jpg" if extension.blank?
      "avatar_#{candidate.id}_#{Time.current.to_i}#{extension}"
    end

    def detect_content_type(file)
      return file.content_type if file.respond_to?(:content_type) && file.content_type.present?

      extension = File.extname(URI.parse(image_url).path).downcase
      case extension
      when ".jpg", ".jpeg" then "image/jpeg"
      when ".png" then "image/png"
      when ".gif" then "image/gif"
      when ".webp" then "image/webp"
      else "image/jpeg"
      end
    end
  end
end
