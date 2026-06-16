class AddressRelationship < ApplicationRecord
  include Searchable

  belongs_to :address
  belongs_to :account
  belongs_to :user, optional: true

  validates :reference_type, presence: true
  validates :reference_id, presence: true, uniqueness: {
    scope: [ :reference_type, :address_id ],
    conditions: -> { where(is_deleted: false) },
    message: "Reference must be unique for the address"
  }
  validates :address, presence: true
end
