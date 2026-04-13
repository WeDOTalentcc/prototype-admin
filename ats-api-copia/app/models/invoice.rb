# frozen_string_literal: true

class Invoice < ApplicationRecord
  belongs_to :subscription, optional: true
  belongs_to :client_account

  validates :client_account_id, presence: true
end
