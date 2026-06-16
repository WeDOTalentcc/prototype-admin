class ApplyStatus < ApplicationRecord
  belongs_to :apply
  belongs_to :selective_process
  belongs_to :user
end
