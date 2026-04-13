class Job < ApplicationRecord
  include Searchable

  has_many :selective_processes, dependent: :destroy
  has_many :applies, dependent: :destroy
  belongs_to :user
  belongs_to :account, optional: true

  validates :title, presence: true
  validates :description, presence: true

  after_create :create_default_selective_processes

  private

  def create_default_selective_processes
    @account_id = account_id || Current&.user&.account_id
    SelectiveProcess.default_process.each do |attrs|
      selective_processes.create!(
        name: attrs[:name],
        position: attrs[:position],
        status: attrs[:status],
        account_id: @account_id,
      )
    end
  end
end
