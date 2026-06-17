# frozen_string_literal: true

module CollectionJob
  module AppliesJob
    class DeleteCollectionJob < ApplicationJob
      include AtsSyncable

      queue_as :default
      sidekiq_options retry: false

      def perform(select_all_params, user_id, apply_collection_params = {})
        user = User.find(user_id)
        account = user.account
        Current.user = user
        Apartment::Tenant.switch!(account.tenant)
        page = 1
        first_record = CollectionService.call(select_all_params, page)
        total_page = (first_record[:total_count] / 30) + 1
        while page <= total_page
          CollectionService.call(select_all_params, page)[:records].each do |record|
            next if record.is_deleted
            candidate_id = select_all_params[:reference_type] == "applies" ? record.candidate_id : record.id

            apply = Apply.find_by(
              candidate_id: candidate_id,
              job_id: apply_collection_params[:job_id],
              is_deleted: false
            )

            if apply
              status_to_use = apply.selective_process_status.present? ? apply.selective_process_status : "Deletado"
              apply.update!(
                is_deleted: true,
                selective_process_status: status_to_use
              )

              sync_apply_to_ats(apply)
            end
          end

          CollectionChannel.broadcast_to("#{user_id}_collection", {
                                           status: "loading ",
                                           percent: page * 100 / total_page
                                         })

          page += 1
        end


        sleep(2)
        CollectionChannel.broadcast_to("#{user_id}_collection", {
                                          status: "completed ",
                                          percent: 100
                                        })
      end
    end
  end
end
