# app/models/data_file.rb
class DataFile < ApplicationRecord
  include UidGeneratable
  include Searchable

  has_one_attached :file
  belongs_to :user, optional: true
  belongs_to :account, optional: true
  validates :name, presence: true
  validates :file, attached: true, content_type: [
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg",
    "image/png",
    "text/plain",
    "text/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    /^audio\/.*/
  ]

  def search_data
    {
      **attributes.deep_symbolize_keys,
      user_name: user&.name,
      account_name: account&.name,
      created_at: created_at.strftime("%d/%m/%Y %H:%M:%S")
    }
  end
end
