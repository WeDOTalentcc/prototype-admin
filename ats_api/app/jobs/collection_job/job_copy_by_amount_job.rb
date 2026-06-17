module CollectionJob
  class JobCopyByAmountJob < ApplicationJob
    queue_as :default
    sidekiq_options retry: false

    def perform(amount, job_id, user_id, entities)
      JobService::CopyJobCollection.make_copy_collection_by_amount(amount, job_id, user_id, entities)
    end
  end
end
