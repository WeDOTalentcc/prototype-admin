module Chatbot
  class EvaluationStarterJob < ApplicationJob
    queue_as :default

    def perform(apply_id, evaluation_id, account_id = nil)
      Apartment::Tenant.switch!(Account.find(account_id).tenant) if account_id
      Chatbot::Evaluation::Starter.new(apply_id: apply_id, evaluation_id: evaluation_id).call
    end
  end
end
