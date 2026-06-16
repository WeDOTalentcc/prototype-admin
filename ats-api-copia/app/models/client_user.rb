# frozen_string_literal: true

class ClientUser < ApplicationRecord
  belongs_to :client_account, foreign_key: :company_id

  validates :company_id, presence: true
  validates :email, presence: true, uniqueness: { scope: :company_id }
end
