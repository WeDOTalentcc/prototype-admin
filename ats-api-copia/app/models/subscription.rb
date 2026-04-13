# frozen_string_literal: true

class Subscription < ApplicationRecord
  belongs_to :client_account

  has_many :invoices, dependent: :destroy

  validates :client_account_id, presence: true
end
