class WorkflowTemplate < ApplicationRecord
  include Searchable

  enable_autocomplete :name

  belongs_to :user, optional: true
  belongs_to :account
  has_many :selective_processes
  validates :name, presence: true
end
