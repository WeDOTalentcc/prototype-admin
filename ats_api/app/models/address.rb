class Address < ApplicationRecord
  include Searchable

  belongs_to :city, optional: true
  belongs_to :state, optional: true
  belongs_to :country, optional: true
  belongs_to :user, optional: true
  belongs_to :account
end
