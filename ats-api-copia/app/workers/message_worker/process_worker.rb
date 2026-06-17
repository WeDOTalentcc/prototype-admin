module MessageWorker
  class ProcessWorker
    include Sneakers::Worker

    from_queue "messages_processed",
              ack: true,
              durable: true,
              exchange: "",
              routing_key: "messages_processed",
              arguments: {}

    def work(raw_payload)
      data = JSON.parse(raw_payload)
      puts "Recebido resultado: #{data.inspect}"

      message = Message.find(data["original_message_id"])
      return if message.entity != Message::ROLE_USER || message.status != Message::STATUS_NOT_ANSWERED
      message.update!(
        status: Message::STATUS_ANSWERED,
        metadata: data["response"]
      )

      content = "<p class='f20'>#{data['response']['message']}</p>"

      new_message = Message.create!(
        content: content,
        reference_type: "User",
        reference_id: message.reference_id,
        entity: Message::ROLE_SYSTEM,
        status: Message::STATUS_NOT_ANSWERED,
        account_id: message.account_id,
        metadata: data["response"]
      )

      ActionCable.server.broadcast("messages_user_#{message.reference_id}", {
        content: new_message.content,
        entity: new_message.entity,
        status: new_message.status,
        metadata: new_message.metadata
      })

      ack!
    end
  end
end
