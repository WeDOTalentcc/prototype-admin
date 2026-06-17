class MessageSampleService
  def self.call(message, user)
    if message[:entity] == Message::ROLE_USER && message[:status] == Message::STATUS_NOT_ANSWERED
      if message[:reference_type] == "User" && message[:reference_id] == user.id
        if message[:content] == "Show all jobs"
          content = "<p class='f20'>Here are all the jobs available for you to apply:</p>"
          jobs = Job.where(account_id: user.account_id, user_id: user.id)
          jobs_list = jobs.map do |job|
            content += "<p>- #{job.title} (#{job.description})</p>"
            content += "<p>-----------------------------------------------------------</p>"
          end
          message.update(
            status: Message::STATUS_ANSWERED,
          )
          message.save
          new_message = Message.create(
            content: content,
            reference_type: "User",
            reference_id: user.id,
            entity: Message::ROLE_SYSTEM,
            status: Message::STATUS_NOT_ANSWERED,
            account_id: user.account_id
          )
          ActionCable.server.broadcast("messages_user_#{user.id}", {
            id: new_message.id,
            content: new_message.content,
            entity: new_message.entity,
            status: new_message.status,
            metadata: new_message.metadata,
            created_at: new_message.created_at
          })
        end
        if message[:content] == "Show all users"
          content = "<p class='f20'>Here are all the users available:</p>"
          users = User.where(account_id: user.account_id)
          users_list = users.map do |user|
            content += "<p>- #{user.email}</p>"
            content += "<p>-----------------------------------------------------------</p>"
          end
          message.update(
            status: Message::STATUS_ANSWERED,
          )
          message.save
          new_message = Message.create(
            content: content,
            reference_type: "User",
            reference_id: user.id,
            entity: Message::ROLE_SYSTEM,
            status: Message::STATUS_NOT_ANSWERED,
            account_id: user.account_id
          )
          ActionCable.server.broadcast("messages_user_#{user.id}", {
            id: new_message.id,
            content: new_message.content,
            entity: new_message.entity,
            status: new_message.status,
            metadata: new_message.metadata,
            created_at: new_message.created_at
          })
        end
      end
    end
  end
end
