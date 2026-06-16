# frozen_string_literal: true

class ReindexAppliesForCandidateJob < ApplicationJob
  queue_as :default

  def perform(candidate_id, account_id)
    account = Account.find_by(id: account_id)
    return unless account&.tenant.present?

    Apartment::Tenant.switch(account.tenant) do
      Apply.where(candidate_id: candidate_id).reindex
    end
  end
end
