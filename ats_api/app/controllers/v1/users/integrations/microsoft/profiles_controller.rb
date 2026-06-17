# frozen_string_literal: true

require "base64"

module V1
  module Users
    module Integrations
      module Microsoft
        class ProfilesController < V1::Users::ApplicationController
          include MicrosoftLinked
          # GET /v1/users/integrations/microsoft/me
          def show
            profile = MicrosoftService::Api.get("/me", @current_user)
            photo = fetch_photo_data_url(@current_user)

            render json: {
              id: profile["id"],
              display_name: profile["displayName"],
              given_name: profile["givenName"],
              surname: profile["surname"],
              user_principal_name: profile["userPrincipalName"],
              mail: profile["mail"] || profile["userPrincipalName"],
              photo: photo
            }
          rescue => error
            Rails.logger.error("MS /me endpoint error: #{error.class} #{error.message}")
            Rails.logger.error(error.backtrace&.first(5)&.join("\n"))
            render json: { error: "Falha ao obter dados da Microsoft" }, status: :unprocessable_entity
          end

          private

          def fetch_photo_data_url(user)
            url = "https://graph.microsoft.com/v1.0/me/photo/$value"
            headers = { "Authorization" => "Bearer #{user.ms_access_token}", "Accept" => "image/*" }
            resp = HTTParty.get(url, headers: headers)

            if resp.code == 401 && user.ms_refresh_token.present?
              MicrosoftService::Api.refresh_expires_at(user)
              headers = { "Authorization" => "Bearer #{user.ms_access_token}", "Accept" => "image/*" }
              resp = HTTParty.get(url, headers: headers)
            end

            return nil unless resp.code.between?(200, 299)

            content_type = resp.headers["content-type"] || "image/jpeg"
            {
              content_type: content_type,
              data_url: "data:#{content_type};base64,#{Base64.strict_encode64(resp.body)}"
            }
          rescue => error
            Rails.logger.warn("MS photo fetch failed: #{error.class} #{error.message}")
            nil
          end
        end
      end
    end
  end
end
