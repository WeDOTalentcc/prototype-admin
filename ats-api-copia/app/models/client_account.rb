# frozen_string_literal: true

class ClientAccount < ApplicationRecord
  has_many :client_users, foreign_key: :company_id, dependent: :destroy
  has_one :company_profile, dependent: :destroy
  has_many :subscriptions, dependent: :destroy
  has_many :invoices, dependent: :destroy
  has_many :payment_methods, dependent: :destroy

  validates :name, presence: true
end
