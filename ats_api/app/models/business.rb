class Business < ApplicationRecord
  include Searchable

  has_one_attached :logo
  has_one_attached :cover_image

  belongs_to :account
  validates :name, presence: true
  validates :email, format: { with: URI::MailTo::EMAIL_REGEXP }, allow_blank: true
  validates :cnpj, uniqueness: true, allow_blank: true
end
