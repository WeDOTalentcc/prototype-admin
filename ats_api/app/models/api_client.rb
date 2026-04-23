# frozen_string_literal: true

class ApiClient < ApplicationRecord
  belongs_to :account

  validates :name, presence: true, uniqueness: { scope: :account_id }
  validates :client_id, presence: true, uniqueness: true
  validates :client_secret_hash, presence: true
  validates :account_id, presence: true

  # Authenticate using a plain client_id and client_secret.
  # Returns the ApiClient when valid, otherwise nil.
  def self.authenticate(client_id, client_secret)
    return nil if client_id.blank? || client_secret.blank?

    client = find_by(client_id: client_id)
    return nil unless client

    begin
      bcrypt_secret = BCrypt::Password.new(client.client_secret_hash)
      return client if bcrypt_secret == client_secret
    rescue BCrypt::Errors::InvalidHash
      Rails.logger.warn("ApiClient.authenticate invalid hash for client_id=#{client_id}")
      return nil
    end

    nil
  end
end
