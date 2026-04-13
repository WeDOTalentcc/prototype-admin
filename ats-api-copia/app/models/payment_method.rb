# frozen_string_literal: true

class PaymentMethod < ApplicationRecord
  belongs_to :client_account

  validates :client_account_id, presence: true
end
